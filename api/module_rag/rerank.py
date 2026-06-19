"""Rerank 客户端(DashScope gte-rerank,纯 HTTP)。provider 可扩展。"""

from __future__ import annotations

import requests

from config.env import RagConfig

_DASHSCOPE_RERANK = 'https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank'


def rerank(query: str, docs: list[str], top_n: int | None = None) -> list[tuple[int, float]]:
    """返回 [(原始index, 相关性分)],按分降序。未启用/失败时返回空(调用方回退原序)。"""
    rtype = (RagConfig.rerank_type or '').lower()
    key = RagConfig.rerank_key
    if not rtype or not key or not docs:
        return []
    if rtype in ('dashscope', 'tongyi', 'qwen'):
        return _dashscope(query, docs, key, top_n or len(docs))
    return []


def _dashscope(query: str, docs: list[str], key: str, top_n: int) -> list[tuple[int, float]]:
    body = {
        'model': RagConfig.rerank_model or 'gte-rerank',
        'input': {'query': query, 'documents': docs},
        'parameters': {'top_n': top_n, 'return_documents': False},
    }
    try:
        resp = requests.post(_DASHSCOPE_RERANK, json=body, timeout=30,
                             headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
        resp.raise_for_status()
        results = resp.json().get('output', {}).get('results', [])
        return [(int(r['index']), float(r.get('relevance_score', 0.0))) for r in results]
    except Exception:
        return []
