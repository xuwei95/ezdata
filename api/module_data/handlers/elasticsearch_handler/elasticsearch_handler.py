"""
Elasticsearch handler:原生 elasticsearch-py + dlt 自定义 resource。

不走 SQLAlchemy 半 engine——实测半 engine 含数组字段时 dlt 抽取会"静默丢列",且 ES SQL 只读。
故查询用 DSL、抽取用 scan 包 @dlt.resource、写用 bulk,保留数组/嵌套原貌。
"""

from collections.abc import Iterable
from typing import Any

from module_data.handlers.base import Capability, Column, Connector, ConnectResult
from module_data.handlers.elasticsearch_handler.connection_args import connection_args, connection_args_example


class ElasticsearchHandler(Connector):
    name = 'elasticsearch'
    title = 'Elasticsearch'
    family = 'search'
    capabilities = (
        Capability.READ | Capability.WRITE | Capability.EXTRACT
        | Capability.SCHEMA | Capability.GEN_API
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
        if self._client is None:
            from elasticsearch import Elasticsearch

            self._client = Elasticsearch(**self._client_kwargs())
        return self._client

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
        return [Column(name=k, type=v.get('type', 'object')) for k, v in props.items()]

    def sample_query(self, table: str, limit: int = 100) -> dict:
        return {'index': table, 'body': {'query': {'match_all': {}}, 'size': limit}}

    def query(self, statement: dict, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """statement = {'index': ..., 'body': <ES DSL>}(程序化构造 DSL,不做模板注入)。"""
        index = statement['index']
        body = dict(statement.get('body') or {})
        if limit is not None:
            body['size'] = min(int(limit), body.get('size', limit))
        resp = self.client.search(index=index, body=body)
        return [h['_source'] | {'_id': h['_id']} for h in resp['hits']['hits']]

    def search(self, table: str, filters: list[dict] | None = None, page: int = 1,
               pagesize: int = 20, **kwargs: Any) -> dict:
        """分页查询:ES from/size + hits.total。"""
        from module_data.query import to_es

        dsl, sort = to_es(filters) if filters else ({'match_all': {}}, [])
        body: dict = {'query': dsl, 'from': (page - 1) * pagesize, 'size': pagesize}
        if sort:
            body['sort'] = sort
        resp = self.client.search(index=table, body=body)
        hits = resp['hits']
        total = hits['total']['value'] if isinstance(hits['total'], dict) else hits['total']
        records = [h['_source'] | {'_id': h['_id']} for h in hits['hits']]
        return {'records': records, 'total': total, 'page': page, 'pagesize': pagesize}

    def extract(self, table: str, *, query: dict | None = None, filters: list[dict] | None = None,
                chunk_size: int = 1000, **kwargs: Any) -> Any:
        import dlt
        from elasticsearch.helpers import scan

        # 统一过滤结构 -> ES DSL
        if filters and query is None:
            from module_data.query import to_es

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

    def write(self, data: Iterable[dict], table: str, mode: str = 'append', *, id_field: str | None = None,
              **kwargs: Any) -> Any:
        from elasticsearch.helpers import bulk

        if mode == 'replace' and self.client.indices.exists(index=table):
            self.client.indices.delete(index=table)
        actions = []
        for doc in data:
            action = {'_index': table, '_source': doc}
            if id_field and id_field in doc:
                action['_id'] = doc[id_field]
            actions.append(action)
        ok, errors = bulk(self.client, actions, stats_only=False)
        self.client.indices.refresh(index=table)
        return {'written': ok, 'errors': errors}
