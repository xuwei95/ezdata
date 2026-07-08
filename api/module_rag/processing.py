"""
切分处理层 —— 走 Agno ChunkingStrategy(现代化),依赖感知 + 回退到内置递归切分。

可用策略(免重依赖):
  recursive(默认)/ fixed / document —— 开箱即用
  semantic —— 需 chonkie(已装),用 DashScope embedder 按语义切
  markdown / agentic / code —— 需 unstructured / LLM,未启用时回退 recursive

入口 chunk_text(text, strategy, chunk_size, overlap, dataset) -> list[str]
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

from config.env import RagConfig
from module_rag.embedding import _DEFAULT_BASE
from module_rag.text_split import split_text

# 扩展名 → Agno reader key(免重依赖的几类)
_EXT_READER = {
    '.pdf': 'pdf',
    '.docx': 'docx',
    '.doc': 'docx',
    '.csv': 'csv',
    '.tsv': 'csv',
    '.xlsx': 'excel',
    '.xls': 'excel',
    '.json': 'json',
    '.jsonl': 'json',
    '.md': 'markdown',
    '.markdown': 'markdown',
    '.txt': 'text',
    '.text': 'text',
    '.log': 'text',
    '.pptx': 'pptx',
    '.ppt': 'pptx',  # 需 python-pptx
}


def read_file(file_key: str, *, filename: str | None = None) -> str:
    """用 Agno Reader 读文件成文本;不支持/失败时回退我们的 extractor。"""
    from module_rag.extractor import _normalize_key, _read_storage_bytes, extract_bytes

    name = filename or os.path.basename(_normalize_key(file_key))
    ext = os.path.splitext(name)[1].lower()
    raw = _read_storage_bytes(file_key)
    key = _EXT_READER.get(ext)
    if key:
        try:
            from pathlib import Path

            from agno.knowledge.reader.reader_factory import ReaderFactory

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
                tf.write(raw)
                tmp = tf.name
            try:
                reader = ReaderFactory.create_reader(key)
                docs = reader.read(Path(tmp), name=name)
                text = '\n\n'.join((d.content or '') for d in docs).strip()
                if text:
                    return text
            finally:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
        except Exception:
            pass
    return extract_bytes(raw, ext)


# 我方策略名 → Agno ChunkingStrategyType 名
_AGNO_MAP = {
    'recursive': 'RECURSIVE_CHUNKER',
    'fixed': 'FIXED_SIZE_CHUNKER',
    'document': 'DOCUMENT_CHUNKER',
    'semantic': 'SEMANTIC_CHUNKER',
    'markdown': 'MARKDOWN_CHUNKER',  # 需 unstructured
}
SUPPORTED = ['recursive', 'fixed', 'document', 'semantic', 'markdown']


def _dashscope_compatible(dataset: Any) -> tuple[str, str, str]:
    """返回 (model, base_url, api_key) 给 Agno OpenAIEmbedder 用(DashScope openai 兼容端点)。"""
    provider = (getattr(dataset, 'embedding_provider', None) or RagConfig.embedding_type or 'dashscope').lower()
    model = getattr(dataset, 'embedding_model', None) or RagConfig.embedding_model
    base = (RagConfig.embedding_url or '').strip() or _DEFAULT_BASE.get(provider, _DEFAULT_BASE['openai'])
    return model, base, RagConfig.api_key


def _semantic_strategy(chunk_size: int, dataset: Any):
    from agno.knowledge.chunking.semantic import SemanticChunking
    from agno.knowledge.embedder.openai import OpenAIEmbedder

    model, base, key = _dashscope_compatible(dataset)
    emb = OpenAIEmbedder(id=model, base_url=base, api_key=key)
    return SemanticChunking(embedder=emb, chunk_size=chunk_size)


def chunk_text(
    text: str, *, strategy: str = 'recursive', chunk_size: int = 512, overlap: int = 100, dataset: Any = None
) -> list[str]:
    """按策略切分文本,返回非空分段列表。任何异常回退到内置递归切分。"""
    text = (text or '').strip()
    if not text:
        return []
    strategy = (strategy or 'recursive').lower()
    try:
        from agno.knowledge.chunking.strategy import ChunkingStrategyFactory, ChunkingStrategyType
        from agno.knowledge.document import Document

        if strategy == 'semantic':
            strat = _semantic_strategy(chunk_size, dataset)
        elif strategy in _AGNO_MAP:
            strat = ChunkingStrategyFactory.create_strategy(
                getattr(ChunkingStrategyType, _AGNO_MAP[strategy]), chunk_size=chunk_size, overlap=overlap
            )
        else:
            raise ValueError(f'未启用的切分策略: {strategy}')

        chunks = [c.content.strip() for c in strat.chunk(Document(content=text)) if c.content and c.content.strip()]
        if chunks:
            return chunks
        raise ValueError('切分结果为空')
    except Exception:
        return split_text(text, chunk_size, overlap)
