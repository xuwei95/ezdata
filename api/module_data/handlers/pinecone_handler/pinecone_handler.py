"""Pinecone handler:向量库,委托 Agno(agno.vectordb.pineconedb.PineconeDb)。依赖走 agno[pinecone] extra。"""

from typing import Any

from module_data.handlers.pinecone_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.vector_base import VectorConnector


class PineconeHandler(VectorConnector):
    name = 'pinecone'
    title = 'Pinecone'
    agno_path = 'agno.vectordb.pineconedb.PineconeDb'
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _vectordb(self, collection: str) -> Any:
        vcls = self._agno_cls()
        return vcls(**self._kw(name=collection, dimension=self.arg('dimension'),
                 embedder=self._embedder(), api_key=self.arg('api_key'),
                 environment=self.arg('environment'), metric=self.arg('metric')))
