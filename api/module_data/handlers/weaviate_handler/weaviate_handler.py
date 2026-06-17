"""Weaviate handler:向量库,委托 Agno(agno.vectordb.weaviate.Weaviate)。依赖走 agno[weaviate] extra。"""

from typing import Any

from module_data.handlers.vector_base import VectorConnector
from module_data.handlers.weaviate_handler.connection_args import connection_args, connection_args_example


class WeaviateHandler(VectorConnector):
    name = 'weaviate'
    title = 'Weaviate'
    agno_path = 'agno.vectordb.weaviate.Weaviate'
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _vectordb(self, collection: str) -> Any:
        vcls = self._agno_cls()
        return vcls(**self._kw(collection=collection, embedder=self._embedder(),
                 wcd_url=self.arg('weaviate_url'), wcd_api_key=self.arg('weaviate_api_key')))
