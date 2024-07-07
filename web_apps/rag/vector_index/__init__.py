from abc import abstractmethod, ABC
from langchain.embeddings.base import Embeddings
from langchain.vectorstores import VectorStore


class BaseVectorIndex(ABC):

    def __init__(self, embeddings: Embeddings):
        self._embeddings = embeddings
        self._vector_store = None

    @abstractmethod
    def _get_vector_store(self) -> VectorStore:
        raise NotImplementedError

    def search(
            self, query: str,
            **kwargs
    ):
        vector_store = self._get_vector_store()
        search_type = kwargs.get('search_type') if kwargs.get('search_type') else 'similarity'
        search_kwargs = kwargs.get('search_kwargs') if kwargs.get('search_kwargs') else {}
        if search_type == 'similarity_score_threshold':
            score_threshold = search_kwargs.get("score_threshold")
            if (score_threshold is None) or (not isinstance(score_threshold, float)):
                search_kwargs['score_threshold'] = .0
            docs_with_similarity = vector_store.similarity_search_with_relevance_scores(
                query, **search_kwargs
            )
            docs = []
            for doc, similarity in docs_with_similarity:
                doc.metadata['score'] = similarity
                docs.append(doc)
            return docs
        return vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        ).get_relevant_documents(query)

    def get_retriever(self, **kwargs):
        vector_store = self._get_vector_store()
        return vector_store.as_retriever(**kwargs)

    def add_texts(self, texts, **kwargs):
        vector_store = self._get_vector_store()
        vector_store.add_texts(texts, **kwargs)

    def delete_by_ids(self, ids: list[str]) -> None:
        vector_store = self._get_vector_store()
        vector_store.delete(ids)

    def delete(self) -> None:
        vector_store = self._get_vector_store()
        vector_store.delete()