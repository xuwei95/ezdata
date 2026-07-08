"""
向量库工厂 —— 按后端名取 VectorStore 实现。

切换向量库:在 _BACKENDS 注册新子类即可,业务层通过 get_vector_store() 拿到统一接口。
后端名沿用 module_data 的 data_source 类型名(elasticsearch/milvus/qdrant/pgvector/chroma),
便于知识库直接挂到一个 data_source 上(dataset.vector_source_id)。
"""

from __future__ import annotations

from typing import Any

from module_rag.vector_store.base import VectorStore
from module_rag.vector_store.es_store import EsVectorStore


def _es(conn: dict, index: str) -> VectorStore:
    return EsVectorStore(conn, index)


# 已实现的后端;预留位抛清晰错误,提示按同一接口补实现
_BACKENDS: dict[str, Any] = {
    'elasticsearch': _es,
    'es': _es,
}

_PLANNED = {'milvus', 'qdrant', 'pgvector', 'chroma', 'weaviate', 'lancedb', 'pinecone'}


def get_vector_store(backend: str, connection_data: dict[str, Any], index: str) -> VectorStore:
    key = (backend or 'elasticsearch').strip().lower()
    builder = _BACKENDS.get(key)
    if builder is not None:
        return builder(connection_data, index)
    if key in _PLANNED:
        raise NotImplementedError(
            f'向量后端 {key} 尚未实现:新增 VectorStore 子类并在 vector_store/factory._BACKENDS 注册即可接入'
        )
    raise ValueError(f'未知向量后端: {backend}')


def supported_backends() -> list[str]:
    return sorted(set(_BACKENDS) | _PLANNED)
