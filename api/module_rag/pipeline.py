"""
文档训练流水线(同步,后台线程执行)。

  extract(抽取) → clean(清洗) → split(切分) → embed(向量化,带缓存) → index(写向量库 + rag_chunk)

状态机:rag_document.status 1待训练 → 2训练中 → 3成功 / 4失败(error 记原因)。
重训会先清掉该文档旧分段(向量库 + rag_chunk)。复用 module_task_schedule 的同步会话与租户上下文。
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import delete, select

from common.context import RequestContext
from module_rag.cleaner import clean_text
from module_rag.contextual import contextualize
from module_rag.entity.do.rag_do import RagChunk, RagDataset, RagDocument
from module_rag.extractor import extract_bytes
from module_rag.processing import chunk_text, read_file
from module_rag.runtime_util import build_embedding_client, build_store, embed_with_cache, md5
from module_task_schedule.sync_db import get_sync_session_local


def train_document_async(document_id: str, tenant_id: Any, force: bool = False) -> None:
    """起后台线程训练,立即返回。"""
    threading.Thread(target=train_document, args=(document_id, tenant_id, force), daemon=True).start()


def _raw_text(db, doc: RagDocument) -> str:
    dt = (doc.document_type or 'upload_file').lower()
    meta = json.loads(doc.meta_data) if doc.meta_data else {}
    if dt == 'upload_file':
        if not doc.file_key:
            raise ValueError('文档缺少文件')
        return read_file(doc.file_key, filename=doc.name)  # Agno reader,失败回退 extractor
    if dt == 'text':
        return meta.get('text') or doc.source or ''
    if dt == 'website':
        import requests  # noqa: PLC0415
        url = doc.source or meta.get('url')
        if not url:
            raise ValueError('网页文档缺少 URL')
        resp = requests.get(url, timeout=30, headers={'User-Agent': 'ezdata-rag/1.0'})
        resp.raise_for_status()
        return extract_bytes(resp.content, '.html')
    if dt == 'datamodel':
        # P2:把数据模型 schema/样例转文本,这里先用 meta 里预存的文本
        return meta.get('text') or ''
    raise ValueError(f'不支持的文档类型: {dt}')


def train_document(document_id: str, tenant_id: Any, force: bool = False) -> dict:
    db = get_sync_session_local()()
    token = RequestContext.set_current_tenant_id(tenant_id)
    try:
        doc = db.execute(select(RagDocument).where(RagDocument.id == document_id)).scalars().first()
        if doc is None:
            return {'ok': False, 'error': '文档不存在'}
        dataset = db.execute(select(RagDataset).where(RagDataset.id == doc.dataset_id)).scalars().first()
        if dataset is None:
            return {'ok': False, 'error': '知识库不存在'}

        # 切分策略
        strat = json.loads(doc.chunk_strategy) if doc.chunk_strategy else {}
        chunk_size = int(strat.get('chunk_size') or 512)
        overlap = int(strat.get('chunk_overlap') or 100)
        strategy = strat.get('strategy') or 'recursive'
        contextual = bool(strat.get('contextual'))

        # 1 抽取 / 清洗
        text = clean_text(_raw_text(db, doc),
                          remove_extra_spaces=strat.get('remove_extra_spaces', True),
                          remove_urls_emails=strat.get('remove_urls_emails', False))
        # 增量:原文+策略未变且上次成功 → 跳过(force 时强制重训)
        new_hash = md5(f'{text}|{strategy}|{chunk_size}|{overlap}|{int(contextual)}')
        if not force and doc.status == 3 and doc.content_hash == new_hash:
            return {'ok': True, 'skipped': True, 'chunks': doc.chunk_count}

        doc.status = 2
        doc.error = None
        doc.update_time = datetime.now()
        db.commit()

        # 2-3 切分(Agno 策略)+ 可选 Contextual Retrieval
        pieces = chunk_text(text, strategy=strategy, chunk_size=chunk_size, overlap=overlap, dataset=dataset)
        if contextual and pieces:
            pieces = contextualize(text, pieces)
        if not pieces:
            doc.status = 3
            doc.chunk_count = 0
            doc.update_time = datetime.now()
            db.commit()
            return {'ok': True, 'chunks': 0, 'note': '无可用文本'}

        # 4 向量化(带缓存)
        client = build_embedding_client(dataset)
        vectors = embed_with_cache(db, pieces, dataset, client)
        dims = len(vectors[0])
        if not dataset.embedding_dims:
            dataset.embedding_dims = dims
            if not dataset.embedding_provider:
                from config.env import RagConfig  # noqa: PLC0415
                dataset.embedding_provider = RagConfig.embedding_type
                dataset.embedding_model = RagConfig.embedding_model
            db.commit()

        # 5 写向量库 + rag_chunk(先清旧分段=重训幂等)
        store = build_store(dataset)
        store.ensure_index(dims)
        store.delete_by_document(doc.id, tenant_id=str(tenant_id) if tenant_id is not None else None)
        db.execute(delete(RagChunk).where(RagChunk.document_id == doc.id))

        es_docs, rows = [], []
        for pos, (content, vec) in enumerate(zip(pieces, vectors)):
            cid = uuid.uuid4().hex
            es_docs.append({
                'chunk_id': cid, 'content': content, 'content_vector': vec,
                'tenant_id': str(tenant_id) if tenant_id is not None else '',
                'dataset_id': dataset.id, 'document_id': doc.id, 'chunk_type': 'chunk',
            })
            rows.append(RagChunk(id=cid, dataset_id=dataset.id, document_id=doc.id, chunk_type='chunk',
                                 content=content, hash=md5(content), position=pos, status=1,
                                 create_time=datetime.now()))
        store.add(es_docs)
        for r in rows:
            db.add(r)

        doc.status = 3
        doc.chunk_count = len(rows)
        doc.content_hash = new_hash
        doc.update_time = datetime.now()
        db.commit()
        return {'ok': True, 'chunks': len(rows), 'strategy': strategy, 'contextual': contextual}
    except Exception as e:  # noqa: BLE001
        db.rollback()
        try:
            doc = db.execute(select(RagDocument).where(RagDocument.id == document_id)).scalars().first()
            if doc:
                doc.status = 4
                doc.error = ' '.join(str(e).split())[:1000]
                doc.update_time = datetime.now()
                db.commit()
        except Exception:
            db.rollback()
        return {'ok': False, 'error': str(e)}
    finally:
        RequestContext.reset_current_tenant_id(token)
        db.close()
