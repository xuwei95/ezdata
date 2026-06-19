"""向后兼容 shim —— 实现已移至 vector_store/es_store.py。"""

from module_rag.vector_store.es_store import EsVectorStore

__all__ = ['EsVectorStore']
