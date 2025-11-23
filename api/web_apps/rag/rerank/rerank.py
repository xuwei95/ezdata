from typing import Optional
from langchain_core.documents import Document
from utils.common_utils import md5


class RerankRunner:
    def __init__(self, rerank_model) -> None:
        self.rerank_model = rerank_model

    def run(self, query: str, documents: list[Document], score_threshold: Optional[float] = 0.1,
            top_n: Optional[int] = 5) -> list[Document]:
        """
        Run rerank model
        :param query: search query
        :param documents: documents for reranking
        :param score_threshold: score threshold
        :param top_n: top n
        :param user: unique user id if needed
        :return:
        """
        docs = []
        doc_id = []
        unique_documents = []
        for document in documents:
            _hash = md5(document.page_content)
            if _hash not in doc_id:
                doc_id.append(_hash)
                docs.append(document.page_content)
                unique_documents.append(document)

        documents = unique_documents

        rerank_result = self.rerank_model.invoke_rerank(
            query=query,
            docs=docs,
            top_n=top_n
        )

        rerank_documents = []

        for result in rerank_result:
            # format document
            if result['score'] >= score_threshold:
                rerank_document = Document(
                    page_content=result['text'],
                    metadata=documents[result['index']].metadata
                )
                rerank_document.metadata['score'] = result['score']
                rerank_documents.append(rerank_document)

        return rerank_documents