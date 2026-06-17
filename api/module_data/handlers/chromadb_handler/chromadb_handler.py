"""ChromaDB handler:向量库,委托 Agno(agno.vectordb.chroma.ChromaDb)。依赖走 agno[chromadb] extra。"""

from typing import Any

from module_data.handlers.chromadb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.vector_base import VectorConnector


class ChromaDBHandler(VectorConnector):
    name = 'chromadb'
    title = 'ChromaDB'
    agno_path = 'agno.vectordb.chroma.ChromaDb'
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _vectordb(self, collection: str) -> Any:
        vcls = self._agno_cls()
        return vcls(**self._kw(collection=collection, embedder=self._embedder(),
                 path=self.arg('persist_directory'), host=self.arg('host'), port=self.arg('port')))
