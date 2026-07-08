from datetime import datetime
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from common.vo import PageModel
from module_alert.entity.do.alert_do import AlertRecord, AlertStrategy
from module_alert.entity.vo.alert_vo import (
    AlertRecordPageQueryModel,
    AlertStrategyModel,
    AlertStrategyPageQueryModel,
)
from utils.page_util import PageUtil


class AlertStrategyDao:
    """告警策略数据库操作层"""

    @classmethod
    async def get_strategy_detail_by_id(cls, db: AsyncSession, strategy_id: int) -> AlertStrategy | None:
        return (
            (await db.execute(select(AlertStrategy).where(AlertStrategy.strategy_id == strategy_id))).scalars().first()
        )

    @classmethod
    async def get_strategy_list(
        cls, db: AsyncSession, query_object: AlertStrategyPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        query = (
            select(AlertStrategy)
            .where(
                AlertStrategy.strategy_name.like(f'%{query_object.strategy_name}%')
                if query_object.strategy_name
                else True,
                AlertStrategy.status == query_object.status if query_object.status is not None else True,
            )
            .order_by(AlertStrategy.strategy_id.desc())
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def add_strategy_dao(cls, db: AsyncSession, obj: AlertStrategyModel) -> AlertStrategy:
        db_obj = AlertStrategy(**obj.model_dump(exclude_unset=True, exclude={'strategy_id'}))
        db.add(db_obj)
        await db.flush()
        return db_obj

    @classmethod
    async def edit_strategy_dao(cls, db: AsyncSession, data: dict) -> None:
        await db.execute(update(AlertStrategy), [data])

    @classmethod
    async def delete_strategy_dao(cls, db: AsyncSession, strategy_ids: list[int]) -> None:
        await db.execute(delete(AlertStrategy).where(AlertStrategy.strategy_id.in_(strategy_ids)))

    @classmethod
    def sync_get_enabled_strategies(cls, db: Session, strategy_ids: list[int]) -> list[AlertStrategy]:
        """同步获取启用的策略(供 Celery worker 使用)"""
        if not strategy_ids:
            return []
        return list(
            db.execute(
                select(AlertStrategy).where(AlertStrategy.strategy_id.in_(strategy_ids), AlertStrategy.status == 1)
            )
            .scalars()
            .all()
        )


class AlertRecordDao:
    """告警记录数据库操作层"""

    @classmethod
    async def get_record_detail_by_id(cls, db: AsyncSession, alert_id: int) -> AlertRecord | None:
        return (await db.execute(select(AlertRecord).where(AlertRecord.alert_id == alert_id))).scalars().first()

    @classmethod
    async def get_record_list(
        cls, db: AsyncSession, query_object: AlertRecordPageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        query = (
            select(AlertRecord)
            .where(
                AlertRecord.strategy_id == query_object.strategy_id if query_object.strategy_id else True,
                AlertRecord.title.like(f'%{query_object.title}%') if query_object.title else True,
                AlertRecord.biz == query_object.biz if query_object.biz else True,
                AlertRecord.metric == query_object.metric if query_object.metric else True,
                AlertRecord.status == query_object.status if query_object.status is not None else True,
                AlertRecord.create_time >= datetime.strptime(query_object.begin_time, '%Y-%m-%d %H:%M:%S')
                if query_object.begin_time
                else True,
                AlertRecord.create_time <= datetime.strptime(query_object.end_time, '%Y-%m-%d %H:%M:%S')
                if query_object.end_time
                else True,
            )
            .order_by(AlertRecord.alert_id.desc())
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def edit_record_dao(cls, db: AsyncSession, data: dict) -> None:
        await db.execute(update(AlertRecord), [data])

    @classmethod
    async def delete_record_dao(cls, db: AsyncSession, alert_ids: list[int]) -> None:
        await db.execute(delete(AlertRecord).where(AlertRecord.alert_id.in_(alert_ids)))

    @classmethod
    def sync_add_record(cls, db: Session, values: dict[str, Any]) -> None:
        """同步新增告警记录(供 Celery worker 使用)"""
        db.add(AlertRecord(**values))
        db.commit()
