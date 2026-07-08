"""
知识库 Agent 工具 —— 供数据分析 Agent 召回知识(含数据源专属库)。

search_knowledge_base(query, source_id|dataset_ids) → 给 Agent 的格式化文本。
make_kb_tool(source_id, tenant_id) → 闭包工具,Agent 只需传 query。
同步实现,复用 retrieval.retrieve;按 source_id 解析该数据源的专属知识库。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from common.context import RequestContext
from module_rag.entity.do.rag_do import RagDataset
from module_rag.retrieval import retrieve
from module_task_schedule.sync_db import get_sync_session_local


def _datasets_for_source(source_id: str) -> list[str]:
    db = get_sync_session_local()()
    try:
        rows = db.execute(select(RagDataset.id).where(RagDataset.source_id == source_id)).scalars().all()
        return list(rows)
    finally:
        db.close()


def search_knowledge_base(
    query: str,
    *,
    source_id: str | None = None,
    dataset_ids: list[str] | None = None,
    tenant_id: Any = None,
    top_k: int = 5,
    retrieval_type: str = 'hybrid',
    rerank: bool = False,
) -> str:
    """检索知识库,返回适合喂给 LLM 的格式化文本(带来源标注)。"""
    if tenant_id is None:
        tenant_id = RequestContext.get_effective_tenant_id()
    ids = list(dataset_ids or [])
    if source_id:
        ids.extend(_datasets_for_source(source_id))
    ids = list(dict.fromkeys(ids))
    if not ids:
        return '未找到可用知识库。'
    res = retrieve(tenant_id, query, ids, k=top_k, retrieval_type=retrieval_type, rerank=rerank)
    records = res.get('records') or []
    if not records:
        return '知识库中未检索到相关内容。'
    lines = []
    for i, r in enumerate(records, 1):
        content = (r.get('content') or '').strip()
        tag = 'QA' if r.get('chunk_type') == 'qa' else '片段'
        lines.append(f'[{i}] ({tag}) {content}')
    return '\n\n'.join(lines)


def make_kb_tool(
    source_id: str | None = None, dataset_ids: list[str] | None = None, tenant_id: Any = None, top_k: int = 5
):
    """构造 Agent 工具闭包:固定知识库范围,Agent 调用时只传 query。"""

    def search_knowledge_base(query: str) -> str:
        """从知识库检索与问题相关的资料,返回带编号的片段文本。"""
        from module_rag.agent_tools import search_knowledge_base as _s

        return _s(query, source_id=source_id, dataset_ids=dataset_ids, tenant_id=tenant_id, top_k=top_k)

    return search_knowledge_base
