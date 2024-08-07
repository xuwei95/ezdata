from web_apps.rag.vector_index import BaseVectorIndex
from langchain.vectorstores import VectorStore
from langchain.vectorstores.elastic_vector_search import ElasticVectorSearch
from config import SYS_CONF

VECTOR_STORE_URL = SYS_CONF.get('VECTOR_STORE_URL', '')
VECTOR_STORE_INDEX = SYS_CONF.get('VECTOR_STORE_INDEX', '')


class EsVectorIndex(BaseVectorIndex):
    def __init__(self, embeddings):
        super().__init__(embeddings)

    def _get_vector_store(self) -> VectorStore:
        """Only for created index."""
        if self._vector_store:
            return self._vector_store
        self._vector_store = ElasticVectorSearch(
            elasticsearch_url=VECTOR_STORE_URL,
            index_name=VECTOR_STORE_INDEX,
            embedding=self._embeddings
        )
        return self._vector_store

