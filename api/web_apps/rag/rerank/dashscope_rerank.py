import dashscope
from http import HTTPStatus


class DashScopeRerankModel:
    def __init__(self, api_key):
        self.api_key = api_key

    def invoke_rerank(self, query: str, docs: list[str], top_n=5) -> list[dict]:
        resp = dashscope.TextReRank.call(
            api_key=self.api_key,
            model=dashscope.TextReRank.Models.gte_rerank,
            query=query,
            documents=docs,
            top_n=top_n,
            return_documents=True
        )

        if resp.status_code == HTTPStatus.OK:
            documents = [{'index': doc.index, 'score': doc.relevance_score, 'text': doc['document']['text']} for doc in resp["output"]["results"]]
            return documents
        else:
            raise RuntimeError(f"Error in DashScope API call: {resp}")
