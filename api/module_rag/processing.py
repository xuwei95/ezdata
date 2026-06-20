"""
切分处理层 —— 走 Agno ChunkingStrategy(现代化),依赖感知 + 回退到内置递归切分。

可用策略(免重依赖):
  recursive(默认)/ fixed / document —— 开箱即用
  semantic —— 需 chonkie(已装),用 DashScope embedder 按语义切
  markdown / agentic / code —— 需 unstructured / LLM,未启用时回退 recursive

入口 chunk_text(text, strategy, chunk_size, overlap, dataset) -> list[str]
"""

from __future__ import annotations

from typing import Any

from config.env import RagConfig
from module_rag.embedding import _DEFAULT_BASE
from module_rag.text_split import split_text

# 我方策略名 → Agno ChunkingStrategyType 名
_AGNO_MAP = {
    'recursive': 'RECURSIVE_CHUNKER',
    'fixed': 'FIXED_SIZE_CHUNKER',
    'document': 'DOCUMENT_CHUNKER',
    'semantic': 'SEMANTIC_CHUNKER',
}
SUPPORTED = ['recursive', 'fixed', 'document', 'semantic']


def _dashscope_compatible(dataset: Any) -> tuple[str, str, str]:
    """返回 (model, base_url, api_key) 给 Agno OpenAIEmbedder 用(DashScope openai 兼容端点)。"""
    provider = (getattr(dataset, 'embedding_provider', None) or RagConfig.embedding_type or 'dashscope').lower()
    model = getattr(dataset, 'embedding_model', None) or RagConfig.embedding_model
    base = (RagConfig.embedding_url or '').strip() or _DEFAULT_BASE.get(provider, _DEFAULT_BASE['openai'])
    return model, base, RagConfig.api_key


def _semantic_strategy(chunk_size: int, dataset: Any):
    from agno.knowledge.chunking.semantic import SemanticChunking  # noqa: PLC0415
    from agno.knowledge.embedder.openai import OpenAIEmbedder  # noqa: PLC0415

    model, base, key = _dashscope_compatible(dataset)
    emb = OpenAIEmbedder(id=model, base_url=base, api_key=key)
    return SemanticChunking(embedder=emb, chunk_size=chunk_size)


def chunk_text(text: str, *, strategy: str = 'recursive', chunk_size: int = 512,
               overlap: int = 100, dataset: Any = None) -> list[str]:
    """按策略切分文本,返回非空分段列表。任何异常回退到内置递归切分。"""
    text = (text or '').strip()
    if not text:
        return []
    strategy = (strategy or 'recursive').lower()
    try:
        from agno.knowledge.chunking.strategy import ChunkingStrategyFactory, ChunkingStrategyType  # noqa: PLC0415
        from agno.knowledge.document import Document  # noqa: PLC0415

        if strategy == 'semantic':
            strat = _semantic_strategy(chunk_size, dataset)
        elif strategy in _AGNO_MAP:
            strat = ChunkingStrategyFactory.create_strategy(
                getattr(ChunkingStrategyType, _AGNO_MAP[strategy]), chunk_size=chunk_size, overlap=overlap)
        else:
            raise ValueError(f'未启用的切分策略: {strategy}')

        chunks = [c.content.strip() for c in strat.chunk(Document(content=text)) if c.content and c.content.strip()]
        if chunks:
            return chunks
        raise ValueError('切分结果为空')
    except Exception:  # noqa: BLE001 依赖缺失/异常 → 回退内置递归切分
        return split_text(text, chunk_size, overlap)
