"""
Elasticsearch handler:原生 elasticsearch-py + dlt 自定义 resource。

不走 SQLAlchemy 半 engine——实测半 engine 含数组字段时 dlt 抽取会"静默丢列",且 ES SQL 只读。
故查询用 DSL、抽取用 scan 包 @dlt.resource、写用 bulk,保留数组/嵌套原貌。
"""

from collections.abc import Iterable
from typing import Any

from ezdata.handlers.base import Capability, Column, Connector, ConnectResult
from ezdata.handlers.elasticsearch_handler.connection_args import connection_args, connection_args_example


def _flatten_aggs(aggs: dict, base: dict | None = None) -> list[dict]:
    """把 ES 聚合结果拍平成表格行:

    - 桶聚合(terms/histogram/range/filters):每个桶一行,key→以聚合名为列,带 doc_count;
    - 指标聚合(avg/sum/max/min/cardinality...):value 作为列拼到当前行;
    - 嵌套桶:逐层交叉展开(父桶 key + 子桶 key 同行)。
    """
    base = dict(base or {})
    bucket_aggs = {n: a for n, a in aggs.items() if isinstance(a, dict) and 'buckets' in a}
    # 同层的指标聚合 → 直接作为列
    for n, a in aggs.items():
        if isinstance(a, dict) and 'buckets' not in a:
            if 'value' in a:
                base[n] = a['value']
            elif 'values' in a:  # percentiles 等多值
                base[n] = a['values']
    if not bucket_aggs:
        return [base] if base else []
    rows: list[dict] = []
    for n, a in bucket_aggs.items():
        buckets = a['buckets']
        if isinstance(buckets, dict):  # filters/keyed range:dict 形态
            buckets = [{'key': k, **v} for k, v in buckets.items()]
        for b in buckets:
            row = dict(base)
            row[n] = b.get('key_as_string', b.get('key'))
            row['doc_count'] = b.get('doc_count')
            sub = {k: v for k, v in b.items() if k not in ('key', 'key_as_string', 'doc_count') and isinstance(v, dict)}
            rows.extend(_flatten_aggs(sub, row) if sub else [row])
    return rows


class ElasticsearchHandler(Connector):
    name = 'elasticsearch'
    title = 'Elasticsearch'
    family = 'search'
    capabilities = Capability.READ | Capability.WRITE | Capability.EXTRACT | Capability.SCHEMA | Capability.GEN_API
    connection_args = connection_args
    connection_args_example = connection_args_example

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._client = None

    def _client_kwargs(self) -> dict:
        hosts = self.arg('hosts', default='http://127.0.0.1:9200')
        if isinstance(hosts, str):
            hosts = [h.strip() for h in hosts.split(',') if h.strip()]
        kw: dict = {'hosts': hosts}
        if self.arg('cloud_id'):
            kw = {'cloud_id': self.arg('cloud_id')}
        if self.arg('api_key'):
            kw['api_key'] = self.arg('api_key')
        elif self.arg('user'):
            kw['basic_auth'] = (self.arg('user'), self.arg('password', default=''))
        return kw

    @property
    def client(self) -> Any:
        def _make():
            from elasticsearch import Elasticsearch

            return Elasticsearch(**self._client_kwargs())

        return self._lazy('_client', _make)

    def test_connection(self) -> ConnectResult:
        try:
            return ConnectResult(True, 'ok') if self.client.ping() else ConnectResult(False, 'ping 失败')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        return [i for i in self.client.indices.get_alias(index='*') if not i.startswith('.')]

    def get_columns(self, table: str) -> list[Column]:
        mapping = self.client.indices.get_mapping(index=table)
        props = next(iter(mapping.values()))['mappings'].get('properties', {})
        cols: list[Column] = []
        for k, v in props.items():
            cols.append(Column(name=k, type=v.get('type', 'object')))
            # text 字段常带 keyword 子字段:terms 聚合/精确匹配/排序须用 `字段.keyword`,
            # 显式暴露出来,否则调用方(含 AI agent)对文本字段聚合会报错或聚到分词 token 上。
            sub = v.get('fields') or {}
            if isinstance(sub.get('keyword'), dict):
                cols.append(Column(name=f'{k}.keyword', type='keyword'))
        return cols

    def sample_query(self, table: str, limit: int = 100) -> dict:
        return {'index': table, 'body': {'query': {'match_all': {}}, 'size': limit}}

    def query(self, statement: dict, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """statement = {'index': ..., 'body': <ES DSL>}(程序化构造 DSL,不做模板注入)。

        含聚合(aggs)时返回拍平后的聚合行;否则返回命中文档(hits)。
        """
        index = statement['index']
        body = dict(statement.get('body') or {})
        if limit is not None:  # size 已显式给定则取较小值(聚合常用 size:0,保持为 0)
            body['size'] = min(int(limit), body.get('size', limit))
        resp = self.client.search(index=index, body=body)
        if resp.get('aggregations'):
            return _flatten_aggs(resp['aggregations'])
        return [h['_source'] | {'_id': h['_id']} for h in resp['hits']['hits']]

    def search(
        self, table: str, filters: list[dict] | None = None, page: int = 1, pagesize: int = 20, **kwargs: Any
    ) -> dict:
        """分页查询:ES from/size + hits.total。"""
        from ezdata.utils.query import to_es

        dsl, sort = to_es(filters) if filters else ({'match_all': {}}, [])
        body: dict = {'query': dsl, 'from': (page - 1) * pagesize, 'size': pagesize}
        if sort:
            body['sort'] = sort
        resp = self.client.search(index=table, body=body)
        hits = resp['hits']
        total = hits['total']['value'] if isinstance(hits['total'], dict) else hits['total']
        records = [h['_source'] | {'_id': h['_id']} for h in hits['hits']]
        return {'records': records, 'total': total, 'page': page, 'pagesize': pagesize}

    def extract(
        self,
        table: str,
        *,
        query: dict | None = None,
        filters: list[dict] | None = None,
        chunk_size: int = 1000,
        **kwargs: Any,
    ) -> Any:
        import dlt
        from elasticsearch.helpers import scan

        # 统一过滤结构 -> ES DSL
        if filters and query is None:
            from ezdata.utils.query import to_es

            dsl, sort = to_es(filters)
            query = {'query': dsl}
            if sort:
                query['sort'] = sort
        client, index = self.client, table

        @dlt.resource(name=table, write_disposition='append')
        def _es_docs() -> Any:
            for hit in scan(client, index=index, query=query or {'query': {'match_all': {}}}, size=chunk_size):
                yield hit['_source'] | {'_id': hit['_id']}

        return _es_docs

    def write(
        self, data: Iterable[dict], table: str, mode: str = 'append', *, id_field: str | None = None, **kwargs: Any
    ) -> Any:
        from elasticsearch.helpers import bulk

        if mode == 'replace' and self.client.indices.exists(index=table):
            self.client.indices.delete(index=table)
        actions = []
        for doc in data:
            doc = dict(doc)
            # 文档自带 _id(ETL transform 里算的 md5 等)→ 用作文档 _id 并从 _source 剔除
            # (ES 保留字段,留在 _source 会报错);追加模式下同 _id 即幂等 upsert,重跑不重复。
            conv_id = doc.pop('_id', None)
            action = {'_index': table, '_source': doc}
            if id_field and id_field in doc:
                action['_id'] = doc[id_field]
            elif conv_id not in (None, ''):
                action['_id'] = conv_id
            actions.append(action)
        if not actions:
            # 无数据(如盘前/非交易日的"当日快照"接口返回空):不 bulk;确保索引存在(空索引),
            # 否则 replace 已删旧索引、append 又从未建索引 → 后续 refresh/查询会 404。
            if not self.client.indices.exists(index=table):
                self.client.indices.create(index=table)
            self.client.indices.refresh(index=table)
            return {'written': 0, 'errors': []}
        # raise_on_error=False:自行收集 errors,部分失败时给出简洁可读的错误(成功/失败数+示例),
        # 而非 helpers.bulk 默认抛出的超长 BulkIndexError;且避免"只报成功数"静默丢数。
        ok, errors = bulk(self.client, actions, stats_only=False, raise_on_error=False)
        self.client.indices.refresh(index=table)
        if errors:
            raise RuntimeError(f'ES 写入部分失败:成功 {ok} / 失败 {len(errors)};示例错误:{str(errors[0])[:300]}')
        return {'written': ok, 'errors': []}
