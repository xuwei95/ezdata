"""Qdrant handler:向量库,委托 Agno(agno.vectordb.qdrant.Qdrant)。依赖走 agno[qdrant] extra。"""

from typing import Any

from ezdata.handlers.qdrant_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.vector_base import VectorConnector


class QdrantHandler(VectorConnector):
    name = 'qdrant'
    title = 'Qdrant'
    agno_path = 'agno.vectordb.qdrant.Qdrant'
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _vectordb(self, collection: str) -> Any:
        vcls = self._agno_cls()
        return vcls(**self._kw(collection=collection, embedder=self._embedder(),
                 location=self.arg('location'), url=self.arg('url'), host=self.arg('host'),
                 port=self.arg('port'), api_key=self.arg('api_key'), https=self.arg('https')))
