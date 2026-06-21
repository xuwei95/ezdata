from fastapi.concurrency import run_in_threadpool

from common.context import RequestContext
from module_rag.entity.vo.rag_vo import RetrievalReq


class RetrievalService:
    """召回入口(供召回测试页 + Agent 工具复用)。同步检索经线程池执行。"""

    @classmethod
    async def search(cls, req: RetrievalReq) -> dict:
        tenant_id = RequestContext.get_effective_tenant_id()
        from module_rag.retrieval import retrieve  # noqa: PLC0415
        res = await run_in_threadpool(
            retrieve, tenant_id, req.query, req.dataset_ids,
            k=req.top_k, retrieval_type=req.retrieval_type, score_threshold=req.score_threshold,
            rerank=req.rerank, rerank_score_threshold=req.rerank_score_threshold,
        )
        # 内部 snake → 前端 camel(retrieve 内部 + agent/测试仍用 snake)
        res['records'] = [{
            'chunkId': r.get('chunk_id'), 'content': r.get('content'),
            'datasetId': r.get('dataset_id'), 'documentId': r.get('document_id'),
            'chunkType': r.get('chunk_type'), 'question': r.get('question'),
            'score': r.get('score'),
        } for r in res.get('records', [])]
        return res
