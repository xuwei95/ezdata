"""Milvus handler:向量库,委托 Agno(agno.vectordb.milvus.Milvus)。依赖走 agno[milvusdb] extra。"""

from typing import Any

from ezdata.handlers.milvus_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.vector_base import VectorConnector


class MilvusHandler(VectorConnector):
    name = 'milvus'
    title = 'Milvus'
    agno_path = 'agno.vectordb.milvus.Milvus'
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _vectordb(self, collection: str) -> Any:
        vcls = self._agno_cls()
        return vcls(**self._kw(collection=collection, embedder=self._embedder(),
                 uri=self.arg('uri'), token=self.arg('token')))
