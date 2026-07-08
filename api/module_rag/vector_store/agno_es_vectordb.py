"""
EsAgnoVectorDb —— 把 ES8 封装成 Agno 的 VectorDb,可直接喂给 Agno Knowledge/Agent。

- 复用我们原生的 EsVectorStore(REST)做实际 ES 读写,不引 es-py、不依赖 agno vectordb。
- embedder 用 Agno OpenAIEmbedder 指向 DashScope 兼容端点(Agno 无 dashscope embedder)。
- search_type 支持 vector/keyword/hybrid(映射到 kNN / BM25 / 应用层 RRF)。
- 多租户:tenant_id 作为 ES filter,贯穿 insert/search/delete。
- agno Document {content,id,name,meta_data,content_id,embedding} ↔ 我们的 ES doc 字段。
"""

from __future__ import annotations

import asyncio
from typing import Any

from agno.knowledge.document import Document
from agno.vectordb.base import VectorDb
from agno.vectordb.search import SearchType

from config.env import RagConfig
from module_rag.embedding import _DEFAULT_BASE, _KNOWN_DIMS
from module_rag.vector_store.es_store import EsVectorStore


def _build_embedder(model: str | None = None, base_url: str | None = None, api_key: str | None = None):
    """Agno OpenAIEmbedder 指向 DashScope(openai 兼容端点)。"""
    from agno.knowledge.embedder.openai import OpenAIEmbedder

    provider = (RagConfig.embedding_type or 'dashscope').lower()
    model = model or RagConfig.embedding_model
    base = base_url or (RagConfig.embedding_url or '').strip() or _DEFAULT_BASE.get(provider, _DEFAULT_BASE['openai'])
    emb = OpenAIEmbedder(id=model, base_url=base, api_key=api_key or RagConfig.api_key)
    if emb.dimensions is None:
        emb.dimensions = _KNOWN_DIMS.get(model, 1536)
    return emb


class EsAgnoVectorDb(VectorDb):
    """ES 的 Agno VectorDb 实现(一个实例 = 一个 ES 索引)。"""

    def __init__(
        self,
        connection_data: dict[str, Any],
        index: str,
        *,
        embedder: Any = None,
        search_type: SearchType = SearchType.hybrid,
        tenant_id: Any = None,
        reranker: Any = None,
        name: str | None = None,
    ) -> None:
        super().__init__(id=None, name=name or index, description=None)
        self._es = EsVectorStore(connection_data, index)
        self.embedder = embedder or _build_embedder()
        self.search_type = search_type
        self.reranker = reranker
        self.tenant_id = None if tenant_id is None else str(tenant_id)

    # ---------- filters ----------
    def _filters(self, extra: dict | None = None) -> list[dict] | None:
        fs: list[dict] = []
        if self.tenant_id is not None:
            fs.append({'term': {'tenant_id': self.tenant_id}})
        for k, v in (extra or {}).items():
            if v is not None:
                fs.append({'term': {k: v}})
        return fs or None

    # ---------- 索引生命周期 ----------
    def create(self) -> None:
        self._es.ensure_index(int(self.embedder.dimensions or 1536))

    def exists(self) -> bool:
        return self._es.index_exists()

    def drop(self) -> None:
        self._es.drop()

    def delete(self) -> bool:
        self._es.drop()
        return True

    def optimize(self) -> None:  # ES 无需
        return None

    def get_supported_search_types(self) -> list[str]:
        return [SearchType.vector.value, SearchType.keyword.value, SearchType.hybrid.value]

    # ---------- 去重/存在性 ----------
    def name_exists(self, name: str) -> bool:
        return self._es.index_exists() and self._es.count(filters=[{'term': {'name': name}}]) > 0

    def id_exists(self, id: str) -> bool:
        return self._es.index_exists() and self._es.count(filters=[{'term': {'chunk_id': id}}]) > 0

    def content_hash_exists(self, content_hash: str) -> bool:
        return self._es.index_exists() and self._es.count(filters=[{'term': {'content_hash': content_hash}}]) > 0

    # ---------- 写 ----------
    def _doc_to_es(self, d: Document, content_hash: str, filters: dict | None) -> dict:
        if not d.embedding:
            d.embed(embedder=self.embedder)
        cid = d.id or d.content_id or (d.meta_data or {}).get('chunk_id')
        return {
            'chunk_id': cid,
            'content': d.content,
            'content_vector': d.embedding,
            'name': d.name,
            'content_id': d.content_id,
            'content_hash': content_hash,
            'chunk_type': 'chunk',
            'meta': d.meta_data or {},
            'tenant_id': self.tenant_id if self.tenant_id is not None else '',
            **({'document_id': (filters or {}).get('document_id')} if (filters or {}).get('document_id') else {}),
        }

    def insert(self, content_hash: str, documents: list[Document], filters: dict | None = None) -> None:
        self.create()
        self._es.add([self._doc_to_es(d, content_hash, filters) for d in documents if d.content])

    def upsert_available(self) -> bool:
        return True

    def upsert(self, content_hash: str, documents: list[Document], filters: dict | None = None) -> None:
        self.insert(content_hash, documents, filters)  # ES bulk index 按 _id 即 upsert

    # ---------- 检索 ----------
    def search(self, query: str, limit: int = 5, filters: Any = None) -> list[Document]:
        if not self._es.index_exists():
            return []
        flt = self._filters(filters if isinstance(filters, dict) else None)
        st = self.search_type
        if st == SearchType.keyword:
            hits = self._es.keyword_search(query, limit, filters=flt)
        else:
            qv = self.embedder.get_embedding(query)
            if st == SearchType.vector:
                hits = self._es.vector_search(qv, limit, filters=flt)
            else:
                hits = self._es.hybrid_search(qv, query, limit, filters=flt)
        if self.reranker is not None:
            try:
                hits = self.reranker.rerank(query=query, documents=hits)  # best-effort
            except Exception:
                pass
        return [self._hit_to_doc(h) for h in hits[:limit]]

    @staticmethod
    def _hit_to_doc(h: dict) -> Document:
        meta = dict(h.get('meta') or {})
        meta['score'] = h.get('rrf_score') or h.get('score')
        return Document(
            id=h.get('chunk_id'),
            name=h.get('name'),
            content=h.get('content') or '',
            content_id=h.get('content_id'),
            meta_data=meta,
        )

    # ---------- 删除 ----------
    def delete_by_id(self, id: str) -> bool:
        return self._es.delete_by_ids([id]) > 0

    def delete_by_name(self, name: str) -> bool:
        return self._delete_by_term('name', name)

    def delete_by_content_id(self, content_id: str) -> bool:
        return self._delete_by_term('content_id', content_id)

    def delete_by_metadata(self, metadata: dict[str, Any]) -> bool:
        if not self._es.index_exists():
            return False
        fs = [{'term': {k: v}} for k, v in metadata.items()]
        body = {'query': {'bool': {'filter': fs}}}
        return int(self._es._req('POST', f'{self._es.index}/_delete_by_query?refresh=true', body).get('deleted', 0)) > 0

    def _delete_by_term(self, field: str, value: Any) -> bool:
        if not self._es.index_exists():
            return False
        body = {'query': {'bool': {'filter': [{'term': {field: value}}]}}}
        return int(self._es._req('POST', f'{self._es.index}/_delete_by_query?refresh=true', body).get('deleted', 0)) > 0

    # ---------- async 包装(线程池跑同步实现)----------
    async def async_create(self) -> None:
        await asyncio.to_thread(self.create)

    async def async_exists(self) -> bool:
        return await asyncio.to_thread(self.exists)

    async def async_drop(self) -> None:
        await asyncio.to_thread(self.drop)

    async def async_insert(self, content_hash: str, documents: list[Document], filters: dict | None = None) -> None:
        await asyncio.to_thread(self.insert, content_hash, documents, filters)

    async def async_upsert(self, content_hash: str, documents: list[Document], filters: dict | None = None) -> None:
        await asyncio.to_thread(self.upsert, content_hash, documents, filters)

    async def async_search(self, query: str, limit: int = 5, filters: Any = None) -> list[Document]:
        return await asyncio.to_thread(self.search, query, limit, filters)

    async def async_name_exists(self, name: str) -> bool:
        return await asyncio.to_thread(self.name_exists, name)
