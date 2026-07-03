"""
pgvector handler:本质是 PostgreSQL,继承 PostgresHandler 复用全部 SQL 能力(连接/查询/抽取/写入),
并额外提供 VECTOR 能力——相似度检索委托 Agno 的 PgVector(依赖走 agno[pgvector],与其它向量库同一套)。
"""

from typing import Any

from ezdata.handlers.base import Capability
from ezdata.handlers.pgvector_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.postgres_handler.postgres_handler import PostgresHandler


class PgVectorHandler(PostgresHandler):
    name = 'pgvector'
    title = 'pgvector (PostgreSQL)'
    family = 'vector'
    capabilities = (
        Capability.READ | Capability.WRITE | Capability.EXTRACT
        | Capability.SCHEMA | Capability.GEN_API | Capability.VECTOR
    )
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _agno_pgvector(self, collection: str) -> Any:
        from agno.vectordb.pgvector import PgVector

        return PgVector(table_name=collection, db_url=self._build_url(),
                        schema=self.arg('schema', default='public'))

    def similarity_search(self, query: str, collection: str, limit: int = 10,
                          filters: dict | None = None, **kwargs: Any) -> list[dict]:
        vdb = self._agno_pgvector(collection)
        return [{'name': getattr(d, 'name', None), 'content': getattr(d, 'content', None),
                 'meta_data': getattr(d, 'meta_data', None)}
                for d in vdb.search(query=query, limit=limit, filters=filters)]
