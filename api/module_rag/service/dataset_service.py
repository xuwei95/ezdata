import uuid
from datetime import datetime
from typing import Any

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from config.env import RagConfig
from exceptions.exception import ServiceException
from module_rag.entity.do.rag_do import RagChunk, RagDataset, RagDocument
from module_rag.entity.vo.rag_vo import DatasetCreateReq, DatasetUpdateReq
from utils.page_util import PageUtil


class DatasetService:
    """知识库 CRUD。删除时连带清向量库索引 + 文档 + 分段。"""

    @classmethod
    async def get_list(
        cls,
        db: AsyncSession,
        name: str | None,
        page_num: int,
        page_size: int,
        is_page: bool = True,
        include_source: bool = False,
    ) -> Any:
        # 默认只展示通用知识库;数据源专属库(source_id 非空)在数据管理的「知识库」tab 里管理。
        # include_source=True(如召回测试)时一并列出数据源专属库,供选择检索。
        conds = [RagDataset.name.like(f'%{name}%') if name else True]
        if not include_source:
            conds.append(RagDataset.source_id.is_(None))
        query = select(RagDataset).where(*conds).order_by(RagDataset.create_time.desc())
        return await PageUtil.paginate(db, query, page_num, page_size, is_page)

    @classmethod
    async def create(cls, db: AsyncSession, req: DatasetCreateReq, operator: str) -> dict:
        try:
            ds_id = uuid.uuid4().hex
            db.add(
                RagDataset(
                    id=ds_id,
                    name=req.name,
                    description=req.description,
                    embedding_provider=req.embedding_provider or RagConfig.embedding_type,
                    embedding_model=req.embedding_model or RagConfig.embedding_model,
                    vector_backend=req.vector_backend or RagConfig.rag_vector_backend,
                    vector_source_id=req.vector_source_id,
                    index_name=f'rag_ds_{ds_id}',
                    status=1,
                    built_in=0,
                    create_by=operator,
                    create_time=datetime.now(),
                    remark=req.remark,
                )
            )
            await db.commit()
            return {'id': ds_id}
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def ensure_for_source(
        cls, db: AsyncSession, source_id: str | None, source_code: str | None, operator: str
    ) -> dict:
        """取数据源专属知识库,不存在则创建(每个数据源一个,供数据分析用)。"""
        from module_data.entity.do.data_do import DataSource

        cond = DataSource.id == source_id if source_id else DataSource.code == source_code
        src = (await db.execute(select(DataSource).where(cond))).scalars().first()
        if not src:
            raise ServiceException(message='数据源不存在')
        # commit 后 ORM 实例会过期,提前把需要的值捕获到本地,避免懒加载 MissingGreenlet
        src_id = src.id
        src_label = src.name or src.code
        existing = (await db.execute(select(RagDataset).where(RagDataset.source_id == src_id))).scalars().first()
        if existing:
            return {'id': existing.id, 'name': existing.name, 'sourceId': src_id}
        try:
            ds_id = uuid.uuid4().hex
            ds_name = f'{src_label} · 专属知识库'
            db.add(
                RagDataset(
                    id=ds_id,
                    name=ds_name,
                    source_id=src_id,
                    description=f'数据源「{src_label}」的专属知识库,供数据分析使用',
                    embedding_provider=RagConfig.embedding_type,
                    embedding_model=RagConfig.embedding_model,
                    vector_backend=RagConfig.rag_vector_backend,
                    index_name=f'rag_ds_{ds_id}',
                    status=1,
                    built_in=1,
                    create_by=operator,
                    create_time=datetime.now(),
                )
            )
            await db.commit()
            return {'id': ds_id, 'name': ds_name, 'sourceId': src_id}
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def get_detail(cls, db: AsyncSession, ds_id: str) -> dict:
        d = (await db.execute(select(RagDataset).where(RagDataset.id == ds_id))).scalars().first()
        if not d:
            raise ServiceException(message='知识库不存在')
        return {
            'id': d.id,
            'name': d.name,
            'description': d.description,
            'status': d.status,
            'embeddingProvider': d.embedding_provider,
            'embeddingModel': d.embedding_model,
            'embeddingDims': d.embedding_dims,
            'vectorBackend': d.vector_backend,
            'vectorSourceId': d.vector_source_id,
            'indexName': d.index_name,
            'createBy': d.create_by,
            'createTime': d.create_time,
            'remark': d.remark,
        }

    @classmethod
    async def update(cls, db: AsyncSession, ds_id: str, req: DatasetUpdateReq, operator: str) -> CrudResponseModel:
        d = (await db.execute(select(RagDataset).where(RagDataset.id == ds_id))).scalars().first()
        if not d:
            raise ServiceException(message='知识库不存在')
        try:
            d.name = req.name
            d.description = req.description
            d.status = req.status
            if req.vector_backend:
                d.vector_backend = req.vector_backend
            d.vector_source_id = req.vector_source_id
            d.remark = req.remark
            d.update_by = operator
            d.update_time = datetime.now()
            await db.commit()
            return CrudResponseModel(is_success=True, message='保存成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def delete(cls, db: AsyncSession, ids: str) -> CrudResponseModel:
        id_list = [i for i in ids.split(',') if i]
        # 先删向量库索引(同步)
        from module_rag.runtime_util import snapshot_dataset

        datasets = (await db.execute(select(RagDataset).where(RagDataset.id.in_(id_list)))).scalars().all()
        snaps = [snapshot_dataset(d) for d in datasets]
        for d in snaps:
            await run_in_threadpool(cls._drop_index, d)
        try:
            for ds_id in id_list:
                await db.execute(delete(RagChunk).where(RagChunk.dataset_id == ds_id))
                await db.execute(delete(RagDocument).where(RagDocument.dataset_id == ds_id))
                await db.execute(delete(RagDataset).where(RagDataset.id == ds_id))
            await db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    def _drop_index(dataset: RagDataset) -> None:
        from module_rag.runtime_util import build_store

        try:
            build_store(dataset).drop()
        except Exception:
            pass
