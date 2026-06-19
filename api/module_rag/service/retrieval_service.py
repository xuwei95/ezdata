from fastapi.concurrency import run_in_threadpool

from common.context import RequestContext
from module_rag.entity.vo.rag_vo import RetrievalReq


class RetrievalService:
    """召回入口(供召回测试页 + Agent 工具复用)。同步检索经线程池执行。"""

    @classmethod
    async def search(cls, req: RetrievalReq) -> dict:
        tenant_id = RequestContext.get_effective_tenant_id()
        from module_rag.retrieval import retrieve  # noqa: PLC0415
        return await run_in_threadpool(
            retrieve, tenant_id, req.query, req.dataset_ids,
            k=req.top_k, retrieval_type=req.retrieval_type, score_threshold=req.score_threshold,
            rerank=req.rerank, rerank_score_threshold=req.rerank_score_threshold,
        )
