from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_data.entity.do.data_do import DataAnalysisTemplate, DataModel, DataSource
from module_data.entity.vo.data_vo import DataModelQuery, DataSourceQuery
from utils.page_util import PageUtil


class DataSourceDao:
    """数据源 DAO。"""

    @classmethod
    async def get_by_id(cls, db: AsyncSession, ds_id: str) -> DataSource | None:
        return (await db.execute(select(DataSource).where(DataSource.id == ds_id))).scalars().first()

    @classmethod
    async def get_by_code(cls, db: AsyncSession, code: str) -> DataSource | None:
        return (await db.execute(select(DataSource).where(DataSource.code == code))).scalars().first()

    @classmethod
    async def get_list(cls, db: AsyncSession, q: DataSourceQuery, is_page: bool = False) -> PageModel | list:
        query = (
            select(DataSource)
            .where(
                DataSource.name.like(f'%{q.name}%') if q.name else True,
                DataSource.code == q.code if q.code else True,
                DataSource.source_type == q.source_type if q.source_type else True,
                DataSource.family == q.family if q.family else True,
                DataSource.status == q.status if q.status else True,
            )
            .order_by(DataSource.create_time.desc())
        )
        return await PageUtil.paginate(db, query, q.page_num, q.page_size, is_page)

    @classmethod
    async def add(cls, db: AsyncSession, obj: dict[str, Any]) -> DataSource:
        do = DataSource(**obj)
        db.add(do)
        await db.flush()
        return do

    @classmethod
    async def edit(cls, db: AsyncSession, ds_id: str, data: dict[str, Any]) -> None:
        do = await cls.get_by_id(db, ds_id)
        if do:
            for k, v in data.items():
                setattr(do, k, v)
            await db.flush()

    @classmethod
    async def remove(cls, db: AsyncSession, ids: list[str]) -> None:
        await db.execute(delete(DataSource).where(DataSource.id.in_(ids)))


class DataModelDao:
    """数据模型 DAO。"""

    @classmethod
    async def get_by_id(cls, db: AsyncSession, m_id: str) -> DataModel | None:
        return (await db.execute(select(DataModel).where(DataModel.id == m_id))).scalars().first()

    @classmethod
    async def get_list(cls, db: AsyncSession, q: DataModelQuery, is_page: bool = False) -> PageModel | list:
        query = (
            select(DataModel)
            .where(
                DataModel.name.like(f'%{q.name}%') if q.name else True,
                DataModel.code == q.code if q.code else True,
                DataModel.datasource_code == q.datasource_code if q.datasource_code else True,
            )
            .order_by(DataModel.create_time.desc())
        )
        return await PageUtil.paginate(db, query, q.page_num, q.page_size, is_page)

    @classmethod
    async def get_custom_query(cls, db: AsyncSession, datasource_code: str) -> DataModel | None:
        """取该数据源的 custom_query 模型(对话图表存看板复用,每源一个)。"""
        return (
            await db.execute(
                select(DataModel).where(
                    DataModel.datasource_code == datasource_code,
                    DataModel.kind == 'custom_query',
                )
            )
        ).scalars().first()

    @classmethod
    async def add(cls, db: AsyncSession, obj: dict[str, Any]) -> DataModel:
        do = DataModel(**obj)
        db.add(do)
        await db.flush()
        return do

    @classmethod
    async def edit(cls, db: AsyncSession, m_id: str, data: dict[str, Any]) -> None:
        do = await cls.get_by_id(db, m_id)
        if do:
            for k, v in data.items():
                setattr(do, k, v)
            await db.flush()

    @classmethod
    async def remove(cls, db: AsyncSession, ids: list[str]) -> None:
        await db.execute(delete(DataModel).where(DataModel.id.in_(ids)))


class AnalysisTemplateDao:
    """数据分析模板 CRUD(租户隔离由 TenantMixin/会话过滤自动处理)。"""

    @classmethod
    async def get_by_id(cls, db: AsyncSession, tid: str) -> DataAnalysisTemplate | None:
        return (await db.execute(select(DataAnalysisTemplate).where(DataAnalysisTemplate.id == tid))).scalars().first()

    @classmethod
    async def get_list(cls, db: AsyncSession, model_id: str | None = None) -> list[DataAnalysisTemplate]:
        stmt = select(DataAnalysisTemplate).order_by(DataAnalysisTemplate.update_time.desc())
        if model_id:
            stmt = stmt.where(DataAnalysisTemplate.model_id == model_id)
        return list((await db.execute(stmt)).scalars().all())

    @classmethod
    async def add(cls, db: AsyncSession, obj: dict[str, Any]) -> DataAnalysisTemplate:
        do = DataAnalysisTemplate(**obj)
        db.add(do)
        await db.flush()
        return do

    @classmethod
    async def edit(cls, db: AsyncSession, tid: str, data: dict[str, Any]) -> None:
        do = await cls.get_by_id(db, tid)
        if do:
            for k, v in data.items():
                setattr(do, k, v)

    @classmethod
    async def remove(cls, db: AsyncSession, ids: list[str]) -> None:
        await db.execute(delete(DataAnalysisTemplate).where(DataAnalysisTemplate.id.in_(ids)))
