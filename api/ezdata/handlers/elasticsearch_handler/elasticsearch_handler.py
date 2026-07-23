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
    # top_hits 聚合(argmax/取样代表行):形如 {"hits":{"hits":[{"_source":..},..]}}
    top_hits = {
        n: a for n, a in aggs.items()
        if isinstance(a, dict) and isinstance(a.get('hits'), dict) and isinstance(a['hits'].get('hits'), list)
    }
    # 同层的指标聚合 → 直接作为列
    for n, a in aggs.items():
        if isinstance(a, dict) and 'buckets' not in a and n not in top_hits:
            if 'value' in a:
                base[n] = a['value']
            elif 'values' in a:  # percentiles 等多值
                base[n] = a['values']
    if not bucket_aggs:
        if top_hits:  # 无桶但有 top_hits:把命中文档展开成行(_source + _id 拼到 base)
            rows = []
            for n, a in top_hits.items():
                for h in a['hits']['hits']:
                    rows.append({**base, **(h.get('_source') or {}), '_id': h.get('_id')})
            return rows or ([base] if base else [])
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
    capabilities = (
        Capability.READ | Capability.WRITE | Capability.EXTRACT | Capability.SCHEMA | Capability.GEN_API | Capability.AGGREGATE
    )
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

    @staticmethod
    def _normalize_stmt(statement: Any, params: dict | None) -> tuple[str, dict]:
        """把 statement 规整成 (index, body)。容错弱模型/agent 常见的误调用形态:
        - handler.query("索引", {DSL})           —— statement 为字符串,DSL 落到 params
        - handler.query({"index":..}, {DSL})     —— body 漏放到 params
        - handler.query({"index":.., "body":..}) —— 正确形态
        - handler.query({"index":.., "query":..,"aggs":..}) —— 忘了包 body,顶层就是 DSL
        """
        if isinstance(statement, str):
            return statement, dict(params or {})
        if isinstance(statement, dict):
            index = statement.get('index')
            body = statement.get('body')
            if body is None:
                if isinstance(params, dict) and index:
                    body = params  # index 在 statement,DSL 误放到 params
                else:  # 忘了 body 包装:除 index 外的键当作 DSL 本身
                    body = {k: v for k, v in statement.items() if k != 'index'}
            if not index:
                raise ValueError("ES 查询缺少 index:请传 {'index':'索引名','body':{DSL}}")
            return index, dict(body or {})
        raise ValueError("ES 查询 statement 须为 {'index':'索引名','body':{DSL}}(或 ('索引名', {DSL}))")

    def query(self, statement: Any, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """statement = {'index': ..., 'body': <ES DSL>}(程序化构造 DSL,不做模板注入)。

        含聚合(aggs)时返回拍平后的聚合行;否则返回命中文档(hits)。
        容错:弱模型常写成 handler.query("索引", {DSL}) 或漏掉 body 包装,统一由 _normalize_stmt 规整。
        """
        index, body = self._normalize_stmt(statement, params)
        if limit is not None:  # size 已显式给定则取较小值(聚合常用 size:0,保持为 0)
            body['size'] = min(int(limit), body.get('size', limit))
        resp = self.client.search(index=index, body=body)
        if resp.get('aggregations'):
            return _flatten_aggs(resp['aggregations'])
        return [h['_source'] | {'_id': h['_id']} for h in resp['hits']['hits']]

    _AGG_METRIC_CAP = 10000  # 分组下推:未限 top_n 时 terms 桶上限(避免超大基数)

    @staticmethod
    def _metric_agg(agg: str, field: str | None) -> dict | None:
        """度量 → ES metric agg 片段;count 返回 None(用桶 doc_count / count API)。"""
        if agg == 'count':
            return None
        if agg == 'count_distinct':
            return {'cardinality': {'field': field}}  # 近似基数(高基数有误差,低基数与精确一致)
        return {agg: {'field': field}}  # sum/avg/max/min 与 ES 同名

    @classmethod
    def _build_agg_request(cls, spec: Any, cols: dict[str, str]) -> tuple[dict, str | None]:
        """把 AggSpec 编译成 ES search body(纯函数,便于测试)。

        返回 (body, dim):dim 为分组维度名(无分组为 None)。文本字段聚合/过滤自动补 `.keyword`。
        """
        from ezdata.handlers.agg_spec import AggNotSupported

        spec.validate()
        if spec.grain:
            # grain 分桶为下推增量能力,当前兜底路径(pandas)不做分桶,为口径一致暂不下推 grain
            raise AggNotSupported('ES 下推暂不支持 grain')
        if len(spec.group_by) > 1:
            raise AggNotSupported('ES 下推暂只支持单维度分组;多维回退兜底')

        def kw(fname: str) -> str:  # 文本字段的 terms 聚合/精确过滤须走 .keyword 子字段
            return f'{fname}.keyword' if cols.get(fname) == 'text' and f'{fname}.keyword' in cols else fname

        filters: list[dict] = []
        for f, v in (spec.filters or {}).items():
            vals = list(v) if isinstance(v, (list, tuple, set)) else [v]
            filters.append({'terms': {kw(f): vals}})
        if spec.time_range and spec.time_field:
            rng = {}
            if spec.time_range.get('start'):
                rng['gte'] = spec.time_range['start']
            if spec.time_range.get('end'):
                rng['lte'] = spec.time_range['end']
            if rng:
                filters.append({'range': {spec.time_field: rng}})
        query = {'bool': {'filter': filters}} if filters else {'match_all': {}}

        metric = cls._metric_agg(spec.agg, spec.field)
        if spec.group_by:
            dim = spec.group_by[0]
            terms: dict = {
                'field': kw(dim),
                'size': int(spec.top_n) if spec.top_n else cls._AGG_METRIC_CAP,
                'order': {'value': 'desc'} if metric else {'_count': 'desc'},
            }
            agg_body: dict = {'terms': terms}
            if metric:
                agg_body['aggs'] = {'value': metric}
            return {'size': 0, 'query': query, 'aggs': {dim: agg_body}}, dim
        # 无分组
        body = {'size': 0, 'query': query}
        if metric:
            body['aggs'] = {'value': metric}
        return body, None

    def aggregate(self, spec: Any) -> list[dict]:
        """把 AggSpec 下推为 ES 聚合,返回 [{维度..., 'value': 聚合值}]。"""
        cols = {c.name: c.type for c in self.get_columns(spec.table)}
        body, dim = self._build_agg_request(spec, cols)
        if dim is None and self._metric_agg(spec.agg, spec.field) is None:
            # count 无分组:直接 count API(比空聚合更省)
            total = self.client.count(index=spec.table, body={'query': body['query']})['count']
            return [{'value': total}]
        rows = self.query({'index': spec.table, 'body': body})
        if dim is None:  # 无分组单值(_flatten_aggs → [{'value': x}])
            return [{'value': rows[0]['value']}] if rows and 'value' in rows[0] else [{'value': None}]
        out: list[dict] = []
        for r in rows:  # 每桶 → {dim: key, 'value': 度量 or doc_count}
            out.append({dim: r.get(dim), 'value': r['value'] if 'value' in r else r.get('doc_count')})
        return out

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
