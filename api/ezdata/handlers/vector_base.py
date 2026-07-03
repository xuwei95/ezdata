"""
向量库连接器共享基类:委托给 Agno 的 vectordb 类(plan §2.2「向量复用 Agno」)。

依赖与 module_ai 的 Agno 同一套(各源装 `agno[qdrant]`/`agno[weaviate]`… extra),
不用 MindsDB 的旧 pin,避免 weaviate v3/v4、pinecone 改名等冲突。

子类只需:设 name/title/agno_path,实现 _vectordb(collection)(把 connection_data 映射成 Agno 实例)。
注:相似度检索需 embedder;默认用 Agno 默认 embedder(可由 connection_data['embedder_*'] 进阶配置)。
"""

import importlib
from typing import Any

from ezdata.handlers.base import Capability, Connector, ConnectResult


class VectorConnector(Connector):
    family = 'vector'
    capabilities = Capability.WRITE | Capability.VECTOR | Capability.SCHEMA
    agno_path: str = ''        # 'agno.vectordb.qdrant.Qdrant'

    @staticmethod
    def _kw(**pairs: Any) -> dict:
        """丢掉值为 None 的 kwargs(Agno 构造器对 None 不一定友好)。"""
        return {k: v for k, v in pairs.items() if v is not None}

    def _agno_cls(self) -> Any:
        module, cls = self.agno_path.rsplit('.', 1)
        return getattr(importlib.import_module(module), cls)

    def _embedder(self) -> Any:
        """默认 None → Agno 用其默认 embedder;进阶可在此按 connection_data 构造。"""
        return None

    def _vectordb(self, collection: str) -> Any:
        """子类覆写:用 connection_data + collection 构造 Agno vectordb 实例。"""
        raise NotImplementedError

    @staticmethod
    def _doc_to_dict(d: Any) -> dict:
        if isinstance(d, dict):
            return d
        return {
            'name': getattr(d, 'name', None),
            'content': getattr(d, 'content', None),
            'meta_data': getattr(d, 'meta_data', None),
            'score': getattr(d, 'score', None),
        }

    def _to_documents(self, documents: Any) -> list:
        from agno.document import Document

        out = []
        for d in documents:
            if isinstance(d, dict):
                out.append(Document(content=d.get('content', ''), name=d.get('name'),
                                    meta_data=d.get('meta_data') or {}))
            else:
                out.append(d)
        return out

    # ---------- 能力 ----------
    def test_connection(self) -> ConnectResult:
        try:
            self._agno_cls()   # 至少能加载 Agno 向量类(真正连通需指定 collection)
            return ConnectResult(True, 'ok(Agno 向量类已就绪)')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        c = self.arg('collection', 'table', 'index')
        return [c] if c else []

    def similarity_search(self, query: str, collection: str, limit: int = 10,
                          filters: dict | None = None, **kwargs: Any) -> list[dict]:
        vdb = self._vectordb(collection)
        results = vdb.search(query=query, limit=limit, filters=filters)
        return [self._doc_to_dict(d) for d in results]

    def query(self, statement: dict, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """statement = {'collection':..., 'query': '...', 'filters': {...}}。"""
        return self.similarity_search(
            statement['query'], statement['collection'],
            limit or statement.get('limit', 10), statement.get('filters'))

    def write(self, data: Any, table: str, mode: str = 'append', **kwargs: Any) -> Any:
        vdb = self._vectordb(table)
        docs = self._to_documents(data)
        if mode == 'replace' and vdb.exists():
            vdb.drop()
        vdb.insert(docs)
        return {'written': len(docs)}
