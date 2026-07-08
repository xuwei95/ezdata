"""
向量库抽象 —— 让 RAG 的向量后端可替换。

设计:
  - 后端只需实现 5 个原语:ping / ensure_index / index_exists / drop / count / add /
    delete_by_document / vector_search / keyword_search。
  - 混合检索(hybrid_search)与 RRF 融合由基类统一提供(应用层融合,零许可证依赖),
    所有后端开箱即用;ES 等若有更优的单请求混合,可覆写 hybrid_search。

切换向量库 = 新增一个 VectorStore 子类 + 在 factory 注册,业务层不感知。
分段文档 schema(各后端统一):
  {chunk_id, content, content_vector, tenant_id, dataset_id, document_id, chunk_type, question, meta}
"""

from __future__ import annotations

import abc
from typing import Any

DEFAULT_RRF_K = 60  # RRF 融合常数,越大越削弱头部名次权重


class VectorStore(abc.ABC):
    """一个实例对应一个知识库的索引/集合。"""

    def __init__(self, connection_data: dict[str, Any], index: str) -> None:
        self.connection_data = connection_data or {}
        self.index = index

    # ---- 连接 / 索引 ----
    @abc.abstractmethod
    def ping(self) -> bool: ...

    @abc.abstractmethod
    def index_exists(self) -> bool: ...

    @abc.abstractmethod
    def ensure_index(self, dims: int, *, similarity: str = 'cosine', analyzer: str | None = None) -> bool:
        """建索引(幂等)。dims 由 embedding 模型决定,建后不可改。返回 True 表示本次新建。"""

    @abc.abstractmethod
    def drop(self) -> None: ...

    @abc.abstractmethod
    def count(self, *, filters: list[dict] | None = None) -> int: ...

    # ---- 写 / 删 ----
    @abc.abstractmethod
    def add(self, chunks: list[dict], *, refresh: bool = True) -> dict: ...

    @abc.abstractmethod
    def delete_by_document(self, document_id: str, *, tenant_id: str | None = None) -> int: ...

    @abc.abstractmethod
    def delete_by_ids(self, ids: list[str]) -> int: ...

    # ---- 检索原语 ----
    @abc.abstractmethod
    def vector_search(
        self, query_vector: list[float], k: int = 5, *, num_candidates: int = 100, filters: list[dict] | None = None
    ) -> list[dict]: ...

    @abc.abstractmethod
    def keyword_search(self, query_text: str, k: int = 5, *, filters: list[dict] | None = None) -> list[dict]: ...

    # ---- 混合检索(基类统一实现:应用层 RRF 融合)----
    def hybrid_search(
        self,
        query_vector: list[float],
        query_text: str,
        k: int = 5,
        *,
        num_candidates: int = 100,
        filters: list[dict] | None = None,
        rrf_k: int = DEFAULT_RRF_K,
        score_threshold: float = 0.0,
    ) -> list[dict]:
        pool = max(k * 4, 20)  # 各路多取一些再融合,提升召回
        vec = self.vector_search(query_vector, pool, num_candidates=num_candidates, filters=filters)
        if score_threshold:  # 阈值作用于向量腿(余弦相似度 0~1),弱向量匹配不参与融合
            vec = [h for h in vec if (h.get('score') or 0) >= score_threshold]
        kw = self.keyword_search(query_text, pool, filters=filters)
        return self.rrf_fuse([vec, kw], rrf_k=rrf_k)[:k]

    @staticmethod
    def rrf_fuse(result_lists: list[list[dict]], *, rrf_k: int = DEFAULT_RRF_K) -> list[dict]:
        """Reciprocal Rank Fusion:按各路名次累加 1/(rrf_k+rank),按 chunk_id 去重。"""
        scores: dict[str, float] = {}
        keep: dict[str, dict] = {}
        for results in result_lists:
            for rank, hit in enumerate(results):
                cid = hit.get('chunk_id')
                if cid is None:
                    continue
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank + 1)
                keep.setdefault(cid, hit)
        fused = []
        for cid, score in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
            fused.append({**keep[cid], 'rrf_score': round(score, 6)})
        return fused
