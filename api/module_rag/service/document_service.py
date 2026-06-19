import json
import uuid
from datetime import datetime
from typing import Any

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.context import RequestContext
from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_rag.entity.do.rag_do import RagChunk, RagDataset, RagDocument
from module_rag.entity.vo.rag_vo import DocumentCreateReq
from utils.page_util import PageUtil

_STATUS_TEXT = {1: '待训练', 2: '训练中', 3: '成功', 4: '失败'}


class DocumentService:
    """文档管理 + 触发训练。"""

    @classmethod
    async def get_list(cls, db: AsyncSession, dataset_id: str, name: str | None,
                       page_num: int, page_size: int, is_page: bool = True) -> Any:
        query = select(RagDocument).where(
            RagDocument.dataset_id == dataset_id,
            RagDocument.name.like(f'%{name}%') if name else True,
        ).order_by(RagDocument.create_time.desc())
        return await PageUtil.paginate(db, query, page_num, page_size, is_page)

    @classmethod
    async def create(cls, db: AsyncSession, req: DocumentCreateReq, operator: str) -> dict:
        ds = (await db.execute(select(RagDataset).where(RagDataset.id == req.dataset_id))).scalars().first()
        if not ds:
            raise ServiceException(message='知识库不存在')
        try:
            doc_id = uuid.uuid4().hex
            meta = {}
            if req.document_type == 'text' and req.text:
                meta['text'] = req.text
            db.add(RagDocument(
                id=doc_id, dataset_id=req.dataset_id, name=req.name, document_type=req.document_type,
                file_key=req.file_key, source=req.source,
                meta_data=json.dumps(meta, ensure_ascii=False) if meta else None,
                chunk_strategy=json.dumps(req.chunk_strategy, ensure_ascii=False) if req.chunk_strategy else None,
                status=1, chunk_count=0, create_by=operator, create_time=datetime.now(),
            ))
            await db.commit()
            if req.auto_train:
                await cls._launch_train(doc_id)
            return {'id': doc_id}
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def train(cls, db: AsyncSession, doc_id: str) -> CrudResponseModel:
        doc = (await db.execute(select(RagDocument).where(RagDocument.id == doc_id))).scalars().first()
        if not doc:
            raise ServiceException(message='文档不存在')
        await cls._launch_train(doc_id)
        return CrudResponseModel(is_success=True, message='已开始训练')

    @classmethod
    async def _launch_train(cls, doc_id: str) -> None:
        """捕获当前租户,起后台线程训练(不阻塞请求)。"""
        tenant_id = RequestContext.get_effective_tenant_id()
        from module_rag.pipeline import train_document_async  # noqa: PLC0415
        await run_in_threadpool(train_document_async, doc_id, tenant_id)

    @classmethod
    async def status(cls, db: AsyncSession, doc_id: str) -> dict:
        d = (await db.execute(select(RagDocument).where(RagDocument.id == doc_id))).scalars().first()
        if not d:
            raise ServiceException(message='文档不存在')
        return {'id': d.id, 'status': d.status, 'statusText': _STATUS_TEXT.get(d.status, ''),
                'chunkCount': d.chunk_count, 'error': d.error}

    @classmethod
    async def delete(cls, db: AsyncSession, ids: str) -> CrudResponseModel:
        id_list = [i for i in ids.split(',') if i]
        docs = (await db.execute(select(RagDocument).where(RagDocument.id.in_(id_list)))).scalars().all()
        # 先从向量库删该文档分段
        for doc in docs:
            ds = (await db.execute(select(RagDataset).where(RagDataset.id == doc.dataset_id))).scalars().first()
            if ds:
                await run_in_threadpool(cls._drop_doc_vectors, ds, doc.id, doc.tenant_id)
        try:
            for doc_id in id_list:
                await db.execute(delete(RagChunk).where(RagChunk.document_id == doc_id))
                await db.execute(delete(RagDocument).where(RagDocument.id == doc_id))
            await db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    def _drop_doc_vectors(dataset: RagDataset, document_id: str, tenant_id: Any) -> None:
        from module_rag.runtime_util import build_store  # noqa: PLC0415
        try:
            store = build_store(dataset)
            if store.index_exists():
                store.delete_by_document(document_id, tenant_id=str(tenant_id) if tenant_id is not None else None)
        except Exception:
            pass
