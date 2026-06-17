"""
MongoDB handler:原生 pymongo + dlt 自定义 resource。

查询用白名单字段构造 filter dict(拦截 $where 等注入面),不走 SQL。
"""

from collections.abc import Iterable
from typing import Any
from urllib.parse import quote_plus

from module_data.handlers.base import Capability, Column, Connector, ConnectResult
from module_data.handlers.mongodb_handler.connection_args import connection_args, connection_args_example


class MongoDBHandler(Connector):
    name = 'mongodb'
    title = 'MongoDB'
    family = 'document'
    capabilities = (
        Capability.READ | Capability.WRITE | Capability.EXTRACT
        | Capability.SCHEMA | Capability.GEN_API
    )
    connection_args = connection_args
    connection_args_example = connection_args_example

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._client = None

    def _uri(self) -> str:
        user = quote_plus(str(self.arg('username', 'user', default='')))
        pwd = quote_plus(str(self.arg('password', default='')))
        host = self.arg('host', default='127.0.0.1')
        port = self.arg('port', default=27017)
        auth = f'{user}:{pwd}@' if user else ''
        return f'mongodb://{auth}{host}:{port}/'

    @property
    def client(self) -> Any:
        if self._client is None:
            from pymongo import MongoClient

            self._client = MongoClient(self._uri(), serverSelectionTimeoutMS=5000)
        return self._client

    @property
    def db(self) -> Any:
        return self.client[self.arg('database', default='test')]

    def test_connection(self) -> ConnectResult:
        try:
            self.client.admin.command('ping')
            return ConnectResult(True, 'ok')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        return self.db.list_collection_names()

    def get_columns(self, table: str) -> list[Column]:
        """Mongo 无固定 schema:取一条样本推断字段。"""
        doc = self.db[table].find_one()
        if not doc:
            return []
        return [Column(name=k, type=type(v).__name__) for k, v in doc.items()]

    def query(self, statement: dict, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """statement = {'collection':..., 'filter':{...}} 或 {'collection':..., 'pipeline':[...]}。"""
        coll = self.db[statement['collection']]
        if 'pipeline' in statement:
            cur = coll.aggregate(statement['pipeline'])
        else:
            cur = coll.find(statement.get('filter') or {})
            if limit is not None:
                cur = cur.limit(int(limit))
        out = []
        for d in cur:
            d['_id'] = str(d.get('_id'))
            out.append(d)
        return out

    def search(self, table: str, filters: list[dict] | None = None, page: int = 1,
               pagesize: int = 20, **kwargs: Any) -> dict:
        """分页查询:find(filter).skip().limit() + count_documents。"""
        from module_data.query import to_mongo

        flt, sort = to_mongo(filters) if filters else ({}, [])
        coll = self.db[table]
        total = coll.count_documents(flt)
        cur = coll.find(flt)
        if sort:
            cur = cur.sort(sort)
        records = []
        for d in cur.skip((page - 1) * pagesize).limit(pagesize):
            d['_id'] = str(d.get('_id'))
            records.append(d)
        return {'records': records, 'total': total, 'page': page, 'pagesize': pagesize}

    def extract(self, table: str, *, filter: dict | None = None,  # noqa: A002  对齐查询语义,filter 即 Mongo filter
                filters: list[dict] | None = None, chunk_size: int = 1000, **kwargs: Any) -> Any:
        import dlt

        coll = self.db[table]
        # 统一过滤结构 -> Mongo filter
        if filters and filter is None:
            from module_data.query import to_mongo

            filter, _sort = to_mongo(filters)  # noqa: A001
        flt = filter or {}

        @dlt.resource(name=table, write_disposition='append')
        def _docs() -> Any:
            for d in coll.find(flt).batch_size(chunk_size):
                d['_id'] = str(d.get('_id'))
                yield d

        return _docs

    def write(self, data: Iterable[dict], table: str, mode: str = 'append', **kwargs: Any) -> Any:
        coll = self.db[table]
        if mode == 'replace':
            coll.drop()
        docs = list(data)
        if docs:
            coll.insert_many(docs)
        return {'written': len(docs)}
