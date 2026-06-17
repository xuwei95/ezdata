"""LanceDB handler:向量库,委托 Agno(agno.vectordb.lancedb.LanceDb)。依赖走 agno[lancedb] extra。"""

from typing import Any

from module_data.handlers.lancedb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.vector_base import VectorConnector


class LanceDBHandler(VectorConnector):
    name = 'lancedb'
    title = 'LanceDB'
    agno_path = 'agno.vectordb.lancedb.LanceDb'
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _vectordb(self, collection: str) -> Any:
        vcls = self._agno_cls()
        return vcls(**self._kw(table_name=collection, embedder=self._embedder(),
                 uri=self.arg('persist_directory'), api_key=self.arg('api_key')))
