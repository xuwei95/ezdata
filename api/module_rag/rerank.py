"""Rerank 客户端(按 provider 列举适配,纯 HTTP,env 驱动 RERANK_*)。

- dashscope / tongyi / qwen:DashScope 原生 rerank 端点。
- siliconflow / openai(及其它 OpenAI 兼容):POST {base}/rerank,base 取 RERANK_URL 或内置默认。
未启用/失败返回空,调用方回退原序。
"""

from __future__ import annotations

import requests

from config.env import RagConfig

_DASHSCOPE_RERANK = 'https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank'
# OpenAI 兼容 rerank 的 provider → 默认 base_url(用户未配 RERANK_URL 时)
_OPENAI_COMPAT_BASE = {
    'siliconflow': 'https://api.siliconflow.cn/v1',
}


def rerank(query: str, docs: list[str], top_n: int | None = None) -> list[tuple[int, float]]:
    """返回 [(原始index, 相关性分)],按分降序。未启用/失败时返回空(调用方回退原序)。"""
    rtype = (RagConfig.rerank_type or '').lower()
    key = RagConfig.rerank_key
    if not rtype or not key or not docs:
        return []
    top_n = top_n or len(docs)
    model = RagConfig.rerank_model

    if rtype in ('dashscope', 'tongyi', 'qwen'):
        return _dashscope(query, docs, key, model or 'gte-rerank', top_n)
    # 其余按 OpenAI 兼容 rerank 处理(siliconflow / openai / 自建网关等)
    base = (RagConfig.rerank_url or '').strip() or _OPENAI_COMPAT_BASE.get(rtype, '')
    if not base or not model:
        return []
    return _openai_compat(query, docs, key, model, base.rstrip('/'), top_n)


def _dashscope(query: str, docs: list[str], key: str, model: str, top_n: int) -> list[tuple[int, float]]:
    body = {
        'model': model,
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


def _openai_compat(query: str, docs: list[str], key: str, model: str, base: str, top_n: int) -> list[tuple[int, float]]:
    """SiliconFlow / OpenAI 兼容 rerank:POST {base}/rerank,返回 results[].{index,relevance_score}。"""
    body = {'model': model, 'query': query, 'documents': docs, 'top_n': top_n, 'return_documents': False}
    try:
        resp = requests.post(f'{base}/rerank', json=body, timeout=30,
                             headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
        resp.raise_for_status()
        results = resp.json().get('results', [])
        return [(int(r['index']), float(r.get('relevance_score', 0.0))) for r in results]
    except Exception:
        return []
