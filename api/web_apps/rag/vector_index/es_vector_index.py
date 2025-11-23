from web_apps.rag.vector_index import BaseVectorIndex
from langchain_community.vectorstores import VectorStore
from langchain_community.vectorstores import ElasticVectorSearch
from config import SYS_CONF

VECTOR_STORE_URL = SYS_CONF.get('ES_HOSTS', '')
VECTOR_STORE_INDEX = SYS_CONF.get('VECTOR_STORE_INDEX', 'rag_store_index')


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

