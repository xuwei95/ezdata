"""
RAG 运行时工具(同步上下文)——构建向量库 / embedding 客户端 / embedding 缓存。

训练在后台线程(同步会话)里跑;检索在 async 控制器里经 run_in_threadpool 调同步逻辑。
向量库后端、embedding provider 都由「知识库绑定 > RagConfig 兜底」决定,后端可替换。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from config.env import RagConfig, TaskLogConfig
from module_rag.embedding import EmbeddingClient
from module_rag.entity.do.rag_do import RagDataset, RagEmbedding
from module_rag.vector_store.base import VectorStore
from module_rag.vector_store.factory import get_vector_store


def md5(text: str) -> str:
    return hashlib.md5((text or '').encode('utf-8')).hexdigest()


# ---------------- 向量库 ----------------
def _vector_connection(dataset: RagDataset) -> dict[str, Any]:
    """解析向量库连接:优先库绑定的 data_source(预留),否则 RagConfig 兜底。"""
    # TODO(P2): dataset.vector_source_id -> 读 data_source 行并解密,接非 ES 后端
    hosts = RagConfig.rag_vector_hosts or TaskLogConfig.task_es_hosts or 'http://127.0.0.1:9200'
    conn: dict[str, Any] = {'hosts': hosts}
    if RagConfig.rag_vector_api_key:
        conn['api_key'] = RagConfig.rag_vector_api_key
    elif RagConfig.rag_vector_user:
        conn['user'] = RagConfig.rag_vector_user
        conn['password'] = RagConfig.rag_vector_password
    return conn


def index_name(dataset: RagDataset) -> str:
    return dataset.index_name or f'rag_ds_{dataset.id}'


def build_store(dataset: RagDataset) -> VectorStore:
    backend = dataset.vector_backend or RagConfig.rag_vector_backend
    return get_vector_store(backend, _vector_connection(dataset), index_name(dataset))


# ---------------- embedding ----------------
def build_embedding_client(dataset: RagDataset) -> EmbeddingClient:
    provider = dataset.embedding_provider or RagConfig.embedding_type
    model = dataset.embedding_model or RagConfig.embedding_model
    dims = dataset.embedding_dims or (RagConfig.embedding_dims or None)
    return EmbeddingClient(provider, model, RagConfig.api_key, RagConfig.embedding_url or None, dims=dims)


def model_key(dataset: RagDataset) -> str:
    provider = dataset.embedding_provider or RagConfig.embedding_type
    model = dataset.embedding_model or RagConfig.embedding_model
    return f'{provider}:{model}'


def embed_with_cache(db, texts: list[str], dataset: RagDataset, client: EmbeddingClient) -> list[list[float]]:
    """带缓存的批量向量化(同步会话)。命中 rag_embedding 跳过模型调用;未命中算完入库。"""
    if not texts:
        return []
    use_cache = bool(RagConfig.embedding_cache)
    mk = model_key(dataset)
    hashes = [md5(t) for t in texts]
    cached: dict[str, list[float]] = {}
    if use_cache:
        from sqlalchemy import select  # noqa: PLC0415
        uniq = list(dict.fromkeys(hashes))
        rows = db.execute(select(RagEmbedding).where(
            RagEmbedding.model_id == mk, RagEmbedding.hash.in_(uniq))).scalars().all()
        for r in rows:
            try:
                cached[r.hash] = json.loads(r.vector)
            except Exception:
                pass

    miss_idx = [i for i, h in enumerate(hashes) if h not in cached]
    if miss_idx:
        miss_vecs = client.embed([texts[i] for i in miss_idx])
        for i, vec in zip(miss_idx, miss_vecs):
            cached[hashes[i]] = vec
            if use_cache:
                db.add(RagEmbedding(hash=hashes[i], model_id=mk, dim=len(vec),
                                    vector=json.dumps(vec, ensure_ascii=False)))
        if use_cache:
            db.commit()
    return [cached[h] for h in hashes]
