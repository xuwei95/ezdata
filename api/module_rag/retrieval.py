"""
召回(同步,经 run_in_threadpool 调用)。

支持多知识库、三种模式(vector / keyword / hybrid)、score 阈值、可选 rerank。
QA 捷径:命中 question_hash 直接给标星答案。各库可能用不同 embedding,故按库分别向量化 query。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from common.context import RequestContext
from config.env import RagConfig
from module_rag.entity.do.rag_do import RagChunk, RagDataset
from module_rag.rerank import rerank as do_rerank
from module_rag.runtime_util import build_embedding_client, build_store, md5
from module_task_schedule.sync_db import get_sync_session_local


def retrieve(tenant_id: Any, query: str, dataset_ids: list[str], *, k: int = 5,
             retrieval_type: str = 'hybrid', score_threshold: float = 0.0,
             rerank: bool = False, rerank_score_threshold: float = 0.0) -> dict:
    db = get_sync_session_local()()
    token = RequestContext.set_current_tenant_id(tenant_id)
    try:
        if not query or not dataset_ids:
            return {'total': 0, 'records': []}
        tenant_str = str(tenant_id) if tenant_id is not None else ''
        tenant_filter = [{'term': {'tenant_id': tenant_str}}] if tenant_str else None

        # QA 捷径
        qa = db.execute(select(RagChunk).where(
            RagChunk.chunk_type == 'qa', RagChunk.question_hash == md5(query),
            RagChunk.dataset_id.in_(dataset_ids))).scalars().first()

        # 批量取数据集(避免逐个 select),按传入顺序处理
        ds_map = {d.id: d for d in
                  db.execute(select(RagDataset).where(RagDataset.id.in_(dataset_ids))).scalars().all()}

        # query 向量按 embedding 配置(provider/model/dims)缓存:多库共用同一 embedding 时只向量化一次
        vec_cache: dict[tuple, Any] = {}

        def _qvec(ds: RagDataset) -> Any:
            key = (ds.embedding_provider or RagConfig.embedding_type,
                   ds.embedding_model or RagConfig.embedding_model,
                   ds.embedding_dims or (RagConfig.embedding_dims or None))
            if key not in vec_cache:
                vec_cache[key] = build_embedding_client(ds).embed_query(query)
            return vec_cache[key]

        all_hits: list[list[dict]] = []
        for ds_id in dataset_ids:
            dataset = ds_map.get(ds_id)
            if dataset is None:
                continue
            store = build_store(dataset)
            if not store.index_exists():
                continue
            if retrieval_type == 'keyword':
                hits = store.keyword_search(query, k * 2, filters=tenant_filter)
            else:
                qvec = _qvec(dataset)
                if retrieval_type == 'vector':
                    hits = store.vector_search(qvec, k * 2, filters=tenant_filter)
                    if score_threshold:  # 余弦相似度阈值
                        hits = [h for h in hits if (h.get('score') or 0) >= score_threshold]
                else:  # hybrid:阈值作用于向量腿
                    hits = store.hybrid_search(qvec, query, k * 2, filters=tenant_filter,
                                               score_threshold=score_threshold)
            all_hits.append(hits)

        # 跨库融合
        from module_rag.vector_store.base import VectorStore  # noqa: PLC0415
        fused = VectorStore.rrf_fuse(all_hits) if len(all_hits) > 1 else (all_hits[0] if all_hits else [])

        # rerank
        if rerank and fused:
            order = do_rerank(query, [h.get('content', '') for h in fused], top_n=k)
            if order:
                reranked = []
                for idx, score in order:
                    if idx < len(fused) and (not rerank_score_threshold or score >= rerank_score_threshold):
                        reranked.append({**fused[idx], 'rerank_score': round(score, 6)})
                fused = reranked

        records = []
        if qa:
            records.append({'chunk_id': qa.id, 'content': qa.answer, 'question': qa.question,
                            'answer': qa.answer, 'dataset_id': qa.dataset_id, 'document_id': qa.document_id,
                            'chunk_type': 'qa', 'score': 1.0})

        top = fused[:k]
        # QA 分段的 question/answer 不一定在向量库 metadata 里(老索引只存了 question,answer 仅在 DB)
        # → 按 chunk_id 回查 DB 补全,保证向量/混合命中的 QA 也能带出答案(否则只回问题没答案)
        qa_ids = [h.get('chunk_id') for h in top if h.get('chunk_type') == 'qa' and h.get('chunk_id')]
        qa_map: dict[str, Any] = {}
        if qa_ids:
            qa_map = {c.id: c for c in db.execute(
                select(RagChunk).where(RagChunk.id.in_(qa_ids))).scalars().all()}
        for h in top:
            rec = {
                'chunk_id': h.get('chunk_id'), 'content': h.get('content'),
                'dataset_id': h.get('dataset_id'), 'document_id': h.get('document_id'),
                'chunk_type': h.get('chunk_type', 'chunk'),
                'question': h.get('question'),
                'score': h.get('rerank_score') or h.get('rrf_score') or h.get('score'),
            }
            if rec['chunk_type'] == 'qa':
                c = qa_map.get(rec['chunk_id'])
                if c is not None:
                    rec['question'] = c.question
                    rec['answer'] = c.answer
                if not rec.get('content'):        # QA 入库 content 为空 → 用 answer 兜底展示
                    rec['content'] = rec.get('answer')
            records.append(rec)
        return {'total': len(records), 'records': records}
    finally:
        RequestContext.reset_current_tenant_id(token)
        db.close()
