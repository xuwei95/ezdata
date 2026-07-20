from typing import Any

from sqlalchemy import ColumnElement, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_data.entity.do.data_metric_do import DataMetric
from module_data.entity.vo.data_metric_vo import DataMetricQuery
from utils.page_util import PageUtil


class DataMetricDao:
    @classmethod
    async def get_by_id(cls, db: AsyncSession, metric_id: int) -> DataMetric | None:
        return (await db.execute(select(DataMetric).where(DataMetric.metric_id == metric_id))).scalars().first()

    @classmethod
    async def get_by_code(cls, db: AsyncSession, code: str) -> DataMetric | None:
        return (await db.execute(select(DataMetric).where(DataMetric.code == code))).scalars().first()

    @classmethod
    async def list_enabled(cls, db: AsyncSession) -> list[DataMetric]:
        return list(
            (await db.execute(select(DataMetric).where(DataMetric.status == '0').order_by(DataMetric.metric_id)))
            .scalars()
            .all()
        )

    @classmethod
    async def get_list(cls, db: AsyncSession, q: DataMetricQuery, scope_sql: ColumnElement | bool = True, is_page: bool = False):
        stmt = (
            select(DataMetric)
            .where(
                or_(DataMetric.name.like(f'%{q.keyword}%'), DataMetric.code.like(f'%{q.keyword}%')) if q.keyword else True,
                DataMetric.status == q.status if q.status else True,
                scope_sql,
            )
            .order_by(DataMetric.metric_id)
        )
        return await PageUtil.paginate(db, stmt, q.page_num, q.page_size, is_page)

    @classmethod
    async def add(cls, db: AsyncSession, data: dict[str, Any]) -> DataMetric:
        obj = DataMetric(**data)
        db.add(obj)
        await db.flush()
        return obj

    @classmethod
    async def edit(cls, db: AsyncSession, data: dict[str, Any]) -> None:
        await db.execute(update(DataMetric), [data])

    @classmethod
    async def remove(cls, db: AsyncSession, metric_id: int) -> None:
        await db.execute(delete(DataMetric).where(DataMetric.metric_id == metric_id))

    @classmethod
    async def mark_stale_by_models(cls, db: AsyncSession, model_ids: list[str]) -> int:
        """血缘影响:把绑定这些模型的指标标 stale(供 P2b 防过期)。"""
        if not model_ids:
            return 0
        r = await db.execute(
            update(DataMetric).where(DataMetric.model_id.in_(model_ids)).values(review_state='stale')
        )
        return r.rowcount or 0
