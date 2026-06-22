"""一次性重建知识库 embedding —— 切换 embedding 模型后把存量库重训到当前 env 配置。

切了 embedding 模型(EMBEDDING_TYPE/EMBEDDING_MODEL)后,旧库会失效:
向量维度变了(索引维度固定)、库里存的 embedding_provider/model 还是旧的。
本脚本把库切到「当前 env embedding」并重建:
  删旧向量索引 → 库 embedding 字段切到 env → 文档 force 重训(从存储重抽)→ 手动分段/QA 重嵌。

用法(在 worker 容器内跑,容器有 ES / 存储 / embedding 依赖):
  # 重建所有「与当前 env 不一致」的库(默认,已一致的跳过)
  docker exec -i ezdata-worker-dev python -m module_rag._rebuild_embeddings

  # 强制重建所有库(含已一致的,会重新消耗 embedding 调用)
  docker exec -i ezdata-worker-dev python -m module_rag._rebuild_embeddings --all

  # 只重建指定库(传 dataset id,可多个;支持 id 前缀)
  docker exec -i ezdata-worker-dev python -m module_rag._rebuild_embeddings 9e314b89 5a923ea1

注意:删索引 + 重嵌不可逆,且消耗 embedding/总调用;文档从 file_key(对象存储)重抽,需源文件仍在。
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import func, select

from config.env import RagConfig
from module_rag.embedding import EmbeddingClient, _KNOWN_DIMS
from module_rag.entity.do.rag_do import RagChunk, RagDataset, RagDocument
from module_rag.pipeline import train_document
from module_rag.runtime_util import build_store
from module_rag.service.chunk_service import ChunkService
from module_task_schedule.sync_db import get_sync_session_local


def _target_dims(provider: str, model: str) -> int:
    """目标向量维度:优先已知模型表,否则探测一条。"""
    return _KNOWN_DIMS.get(model) or len(
        EmbeddingClient(provider, model, RagConfig.api_key, RagConfig.embedding_url or None).embed_query('probe'))


def _match(ds_id: str, selectors: list[str]) -> bool:
    """库是否被 id 选择器命中(支持前缀)。selectors 为空=全部。"""
    return not selectors or any(ds_id == s or ds_id.startswith(s) for s in selectors)


def rebuild_dataset(db, ds: RagDataset, provider: str, model: str, dims: int) -> dict:
    """重建单个库:删索引 → 切 embedding 字段 → 文档 force 重训 → 手动分段/QA 重嵌。"""
    tid = ds.tenant_id
    # 1 删旧向量索引(维度变了,必须重建)
    try:
        build_store(ds).drop()
    except Exception as e:  # noqa: BLE001 索引不存在等忽略
        print(f'    (drop index warn: {e})')
    # 2 embedding 字段切到目标(后续文档训练 / 分段重嵌都按此 + env)
    ds.embedding_provider, ds.embedding_model, ds.embedding_dims = provider, model, dims
    db.commit()
    # 3 文档 force 重训(重抽 → 重切 → 重嵌 → 重建索引)
    doc_ids = db.execute(select(RagDocument.id).where(RagDocument.dataset_id == ds.id)).scalars().all()
    doc_ok = doc_fail = 0
    for did in doc_ids:
        r = train_document(did, tid, force=True)
        if r.get('ok'):
            doc_ok += 1
        else:
            doc_fail += 1
            print(f'    doc {did[:8]} FAIL: {r.get("error")}')
    # 4 手动分段/QA 重嵌(document_id 不属于真实文档的,不走文档训练)
    real = set(doc_ids)
    db.expire_all()
    ds2 = db.execute(select(RagDataset).where(RagDataset.id == ds.id)).scalars().first()
    chunks = db.execute(select(RagChunk).where(RagChunk.dataset_id == ds.id)).scalars().all()
    man_ok = 0
    for ch in chunks:
        if ch.document_id in real:  # 文档分段已在步骤 3 重建
            continue
        text = ch.question if ch.chunk_type == 'qa' else ch.content
        if not text:
            continue
        ChunkService._index_single(ds2, ch.id, text, ch.chunk_type, ch.document_id, tid)
        man_ok += 1
    return {'doc_ok': doc_ok, 'doc_fail': doc_fail, 'manual': man_ok}


def main(selectors: list[str], rebuild_all: bool) -> int:
    provider, model = RagConfig.embedding_type, RagConfig.embedding_model
    dims = _target_dims(provider, model)
    print(f'目标 embedding: {provider}/{model} dims={dims}')
    print('=' * 64)

    db = get_sync_session_local()()
    fails = 0
    try:
        datasets = db.execute(select(RagDataset)).scalars().all()
        for ds in datasets:
            tag = f'[{ds.id[:8]}] {ds.name}'
            if not _match(ds.id, selectors):
                continue
            already = ds.embedding_provider == provider and ds.embedding_model == model and ds.embedding_dims == dims
            if already and not rebuild_all:
                print(f'SKIP  {tag} (已是 {provider}/{model})')
                continue
            try:
                r = rebuild_dataset(db, ds, provider, model, dims)
                fails += r['doc_fail']
                print(f'OK    {tag}: 文档 {r["doc_ok"]} 成功/{r["doc_fail"]} 失败,手动分段重嵌 {r["manual"]}')
            except Exception as e:  # noqa: BLE001
                db.rollback()
                fails += 1
                print(f'ERR   {tag}: {e}')
    finally:
        db.close()
    print('=' * 64)
    print('完成' + (f'(有 {fails} 个文档/库失败)' if fails else ''))
    return 1 if fails else 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='切换 embedding 模型后重建知识库到当前 env 配置')
    ap.add_argument('datasets', nargs='*', help='只重建指定 dataset id(可前缀,可多个);省略=全部')
    ap.add_argument('--all', action='store_true', dest='rebuild_all',
                    help='强制重建(含已与 env 一致的库)')
    args = ap.parse_args()
    sys.exit(main(args.datasets, args.rebuild_all))
