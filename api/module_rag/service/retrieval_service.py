from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.context import RequestContext
from module_rag.entity.do.rag_do import RagDocument
from module_rag.entity.vo.rag_vo import RetrievalReq

_PSEUDO_DOC = {'bulk': '批量导入', 'manual': '手动添加'}


class RetrievalService:
    """召回入口(供召回测试页 + Agent 工具复用)。同步检索经线程池执行。"""

    @classmethod
    async def search(cls, db: AsyncSession, req: RetrievalReq) -> dict:
        tenant_id = RequestContext.get_effective_tenant_id()
        from module_rag.retrieval import retrieve

        res = await run_in_threadpool(
            retrieve,
            tenant_id,
            req.query,
            req.dataset_ids,
            k=req.top_k,
            retrieval_type=req.retrieval_type,
            score_threshold=req.score_threshold,
            rerank=req.rerank,
            rerank_score_threshold=req.rerank_score_threshold,
        )
        records = res.get('records', [])

        # 回填文档名(优先名称;批量/手动给友好标签;兜底 id)
        doc_ids = {
            r.get('document_id') for r in records if r.get('document_id') and r['document_id'] not in _PSEUDO_DOC
        }
        name_map: dict[str, str] = {}
        if doc_ids:
            rows = (await db.execute(select(RagDocument.id, RagDocument.name).where(RagDocument.id.in_(doc_ids)))).all()
            name_map = {rid: rname for rid, rname in rows}

        def doc_name(did: str | None) -> str | None:
            if not did:
                return None
            return name_map.get(did) or _PSEUDO_DOC.get(did) or did

        # 内部 snake → 前端 camel(retrieve 内部 + agent/测试仍用 snake)
        res['records'] = [
            {
                'chunkId': r.get('chunk_id'),
                'content': r.get('content'),
                'datasetId': r.get('dataset_id'),
                'documentId': r.get('document_id'),
                'documentName': doc_name(r.get('document_id')),
                'chunkType': r.get('chunk_type'),
                'question': r.get('question'),
                'answer': r.get('answer'),
                'score': r.get('score'),
            }
            for r in records
        ]
        return res
