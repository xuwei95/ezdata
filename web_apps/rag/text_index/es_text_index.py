from config import ES_CONF, SYS_CONF
from ezetl.libs.es import EsClient


class EsTextIndex:

    def __init__(self):
        self.es_client = EsClient(**ES_CONF)
        self.index_name = SYS_CONF.get('RAG_STORE_INDEX', '')

    def search(
            self, query: str,
            **kwargs
    ):
        search_kwargs = kwargs.get('search_kwargs') if kwargs.get('search_kwargs') else {}
        score_threshold = search_kwargs.get("score_threshold")
        if (score_threshold is None) or (not isinstance(score_threshold, float)):
            search_kwargs['score_threshold'] = .0
        # todo: 查询逻辑
        docs = []
        return docs

    def add_texts(self, texts, **kwargs):
        pass

    def delete_by_ids(self, ids: list[str]) -> None:
        pass

    def delete(self) -> None:
        pass
