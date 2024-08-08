from config import SYS_CONF
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple
)
import uuid
from langchain_core.documents import Document

elasticsearch_url = SYS_CONF.get('ES_HOSTS', '')
index_name = SYS_CONF.get('RAG_STORE_INDEX', 'rag_store_index')


def _default_text_mapping() -> Dict:
    return {
        "properties": {
            "text": {"type": "text"},
        }
    }


def _default_query(question, filter: Optional[dict]) -> Dict:
    query = {
        "bool": {
            "must": [
                {"match": {"content": question}}
            ]
        }
    }

    if filter:
        for key, value in filter.items():
            query["bool"]["must"].append(
                {"match": {f"metadata.{key}.keyword": value}}
            )
    return query


class EsTextIndex:

    def __init__(
            self,
            *,
            ssl_verify: Optional[Dict[str, Any]] = None,
    ):
        """Initialize with necessary components."""

        try:
            import elasticsearch
        except ImportError:
            raise ImportError(
                "Could not import elasticsearch python package. "
                "Please install it with `pip install elasticsearch`."
            )
        self.index_name = index_name
        _ssl_verify = ssl_verify or {}
        try:
            self.client = elasticsearch.Elasticsearch(
                elasticsearch_url,
                **_ssl_verify,
            )
        except ValueError as e:
            raise ValueError(
                f"Your elasticsearch client string is mis-formatted. Got error: {e} "
            )

    def add_texts(
            self,
            texts: Iterable[str],
            metadatas: Optional[List[dict]] = None,
            ids: Optional[List[str]] = None,
            refresh_indices: bool = True,
            **kwargs: Any,
    ) -> List[str]:
        """Run more texts through the embeddings and add to the vectorstore.

        Args:
            texts: Iterable of strings to add to the vectorstore.
            metadatas: Optional list of metadatas associated with the texts.
            ids: Optional list of unique IDs.
            refresh_indices: bool to refresh ElasticSearch indices

        Returns:
            List of ids from adding the texts into the vectorstore.
        """
        try:
            from elasticsearch.exceptions import NotFoundError
            from elasticsearch.helpers import bulk
        except ImportError:
            raise ImportError(
                "Could not import elasticsearch python package. "
                "Please install it with `pip install elasticsearch`."
            )
        requests = []
        ids = ids or [str(uuid.uuid4()) for _ in texts]
        mapping = _default_text_mapping()

        # check to see if the index already exists
        try:
            self.client.indices.get(index=self.index_name)
        except NotFoundError:
            # TODO would be nice to create index before embedding,
            # just to save expensive steps for last
            self.create_index(self.client, self.index_name, mapping)

        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas else {}
            request = {
                "_op_type": "index",
                "_index": self.index_name,
                "text": text,
                "metadata": metadata,
                "_id": ids[i],
            }
            requests.append(request)
        bulk(self.client, requests)

        if refresh_indices:
            self.client.indices.refresh(index=self.index_name)
        return ids

    def search(
            self, query: str,
            **kwargs
    ):
        search_kwargs = kwargs.get('search_kwargs') if kwargs.get('search_kwargs') else {}
        score_threshold = search_kwargs.get("score_threshold")
        if (score_threshold is None) or (not isinstance(score_threshold, float)):
            search_kwargs['score_threshold'] = .0
        docs_with_similarity = self.search_with_score(
            query, **search_kwargs
        )
        docs = []
        for doc, similarity in docs_with_similarity:
            doc.metadata['score'] = similarity
            docs.append(doc)
        return docs

    def similarity_search(
            self, query: str, k: int = 4, filter: Optional[dict] = None, **kwargs: Any
    ) -> List[Document]:
        """Return docs most similar to query.

        Args:
            query: Text to look up documents similar to.
            k: Number of Documents to return. Defaults to 4.

        Returns:
            List of Documents most similar to the query.
        """
        docs_and_scores = self.search_with_score(query, k, filter=filter)
        documents = [d[0] for d in docs_and_scores]
        return documents

    def search_with_score(
            self, query: str, k: int = 4, filter: Optional[dict] = None, **kwargs: Any
    ) -> List[Tuple[Document, float]]:
        """Return docs most similar to query.
        Args:
            query: Text to look up documents similar to.
            k: Number of Documents to return. Defaults to 4.
        Returns:
            List of Documents most similar to the query.
        """
        _query = _default_query(query, filter)
        response = self.client_search(
            self.client, self.index_name, _query, size=k
        )
        hits = [hit for hit in response["hits"]["hits"]]
        docs_and_scores = [
            (
                Document(
                    page_content=hit["_source"]["text"],
                    metadata=hit["_source"]["metadata"],
                ),
                hit["_score"],
            )
            for hit in hits
        ]
        return docs_and_scores

    def create_index(self, client: Any, index_name: str, mapping: Dict) -> None:
        version_num = client.info()["version"]["number"][0]
        version_num = int(version_num)
        if version_num >= 8:
            client.indices.create(index=index_name, mappings=mapping)
        else:
            client.indices.create(index=index_name, body={"mappings": mapping})

    def client_search(
            self, client: Any, index_name: str, query: Dict, size: int
    ) -> Any:
        version_num = client.info()["version"]["number"][0]
        version_num = int(version_num)
        if version_num >= 8:
            response = client.search(index=index_name, query=query, size=size)
        else:
            response = client.search(
                index=index_name, body={"query": query, "size": size}
            )
        return response

    def delete_by_ids(self, ids: list[str]) -> None:
        """Delete by vector IDs.

       Args:
           ids: List of ids to delete.
       """

        if ids is None:
            raise ValueError("No ids provided to delete.")

        # TODO: Check if this can be done in bulk
        for id in ids:
            self.client.delete(index=self.index_name, id=id)

    def delete(self) -> None:
        """Delete by vector IDs.

        Args:
            ids: List of ids to delete.
        """
        if self.client.indices.exists(index=self.index_name):
            self.client.indices.delete(
                index=self.index_name, ignore=[400, 404])