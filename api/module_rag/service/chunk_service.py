import uuid
from datetime import datetime
from typing import Any

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.context import RequestContext
from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_rag.entity.do.rag_do import RagChunk, RagDataset
from module_rag.entity.vo.rag_vo import ChunkSaveReq
from utils.page_util import PageUtil


class ChunkService:
    """分段 / QA 管理。写操作同步到向量库。"""

    @classmethod
    async def get_list(cls, db: AsyncSession, dataset_id: str, document_id: str | None,
                       page_num: int, page_size: int, is_page: bool = True) -> Any:
        query = select(RagChunk).where(
            RagChunk.dataset_id == dataset_id,
            RagChunk.document_id == document_id if document_id else True,
        ).order_by(RagChunk.position)
        return await PageUtil.paginate(db, query, page_num, page_size, is_page)

    @classmethod
    async def save(cls, db: AsyncSession, req: ChunkSaveReq, operator: str) -> dict:
        ds = (await db.execute(select(RagDataset).where(RagDataset.id == req.dataset_id))).scalars().first()
        if not ds:
            raise ServiceException(message='知识库不存在')
        from module_rag.runtime_util import snapshot_dataset  # noqa: PLC0415
        ds_snap = snapshot_dataset(ds)  # commit 后 ds 会过期,提前快照供线程池用
        tenant_id = RequestContext.get_effective_tenant_id()
        is_qa = req.chunk_type == 'qa'
        if is_qa and not (req.question and req.answer):
            raise ServiceException(message='QA 需填写问题和答案')
        if not is_qa and not req.content:
            raise ServiceException(message='分段内容不能为空')

        from module_rag.runtime_util import md5  # noqa: PLC0415
        index_text = req.question if is_qa else req.content
        try:
            if req.id:  # 编辑
                c = (await db.execute(select(RagChunk).where(RagChunk.id == req.id))).scalars().first()
                if not c:
                    raise ServiceException(message='分段不存在')
                c.content = req.content
                c.question = req.question
                c.answer = req.answer
                c.question_hash = md5(req.question) if is_qa and req.question else None
                c.hash = md5(req.content or req.question or '')
                cid = c.id
                doc_id = c.document_id
            else:  # 新增
                cid = uuid.uuid4().hex
                doc_id = req.document_id or 'manual'
                db.add(RagChunk(
                    id=cid, dataset_id=req.dataset_id, document_id=doc_id, chunk_type=req.chunk_type,
                    content=req.content, question=req.question, answer=req.answer,
                    question_hash=md5(req.question) if is_qa and req.question else None,
                    hash=md5(req.content or req.question or ''), position=0, status=1,
                    create_by=operator, create_time=datetime.now(),
                ))
            await db.commit()
            # 同步向量库(用游离快照,避免线程内读已过期 ORM 触发懒加载)
            await run_in_threadpool(cls._index_single, ds_snap, cid, index_text, req.chunk_type, doc_id, tenant_id)
            return {'id': cid}
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def delete(cls, db: AsyncSession, ids: str) -> CrudResponseModel:
        id_list = [i for i in ids.split(',') if i]
        chunks = (await db.execute(select(RagChunk).where(RagChunk.id.in_(id_list)))).scalars().all()
        by_ds: dict[str, list[str]] = {}
        for c in chunks:
            by_ds.setdefault(c.dataset_id, []).append(c.id)
        for ds_id, cids in by_ds.items():
            ds = (await db.execute(select(RagDataset).where(RagDataset.id == ds_id))).scalars().first()
            if ds:
                await run_in_threadpool(cls._delete_vectors, ds, cids)
        try:
            await db.execute(delete(RagChunk).where(RagChunk.id.in_(id_list)))
            await db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def bulk_import(cls, db: AsyncSession, req) -> dict:  # noqa: ANN001
        """CSV/Excel 批量导入 QA对/分段。"""
        ds = (await db.execute(select(RagDataset).where(RagDataset.id == req.dataset_id))).scalars().first()
        if not ds:
            raise ServiceException(message='知识库不存在')
        tenant_id = RequestContext.get_effective_tenant_id()
        from module_rag.bulk_import import bulk_import_from_file  # noqa: PLC0415
        return await run_in_threadpool(bulk_import_from_file, req.dataset_id, req.chunk_type, req.file_key, tenant_id)

    @classmethod
    async def star(cls, db: AsyncSession, chunk_id: str, flag: int) -> CrudResponseModel:
        c = (await db.execute(select(RagChunk).where(RagChunk.id == chunk_id))).scalars().first()
        if not c:
            raise ServiceException(message='分段不存在')
        try:
            c.star_flag = flag
            await db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await db.rollback()
            raise e

    # ---------------- 同步向量库(线程内)----------------
    @staticmethod
    def _index_single(dataset: RagDataset, chunk_id: str, text: str, chunk_type: str,
                      document_id: str, tenant_id: Any) -> None:
        from module_rag.runtime_util import build_embedding_client, build_store  # noqa: PLC0415
        client = build_embedding_client(dataset)
        vec = client.embed_query(text)
        store = build_store(dataset)
        store.ensure_index(len(vec))
        store.add([{
            'chunk_id': chunk_id, 'content': text, 'content_vector': vec,
            'tenant_id': str(tenant_id) if tenant_id is not None else '',
            'dataset_id': dataset.id, 'document_id': document_id, 'chunk_type': chunk_type,
        }])

    @staticmethod
    def _delete_vectors(dataset: RagDataset, chunk_ids: list[str]) -> None:
        from module_rag.runtime_util import build_store  # noqa: PLC0415
        try:
            store = build_store(dataset)
            if store.index_exists():
                store.delete_by_ids(chunk_ids)
        except Exception:
            pass
