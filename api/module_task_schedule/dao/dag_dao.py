from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from module_task_schedule.entity.do.task_do import DagGraph


class DagGraphDao:
    """DAG 图文档数据访问层。"""

    @classmethod
    async def get_by_id(cls, db: AsyncSession, gid: str) -> DagGraph | None:
        return (await db.execute(select(DagGraph).where(DagGraph.id == gid))).scalars().first()

    @classmethod
    async def get_draft(cls, db: AsyncSession, dag_task_id: str) -> DagGraph | None:
        return (
            (await db.execute(select(DagGraph).where(DagGraph.dag_task_id == dag_task_id, DagGraph.version == 'draft')))
            .scalars()
            .first()
        )

    @classmethod
    async def list_versions(cls, db: AsyncSession, dag_task_id: str) -> list[DagGraph]:
        """所有版本(草稿 + 发布版),按时间倒序。"""
        return list(
            (
                await db.execute(
                    select(DagGraph).where(DagGraph.dag_task_id == dag_task_id).order_by(DagGraph.create_time.desc())
                )
            )
            .scalars()
            .all()
        )

    @classmethod
    async def add(cls, db: AsyncSession, obj: dict[str, Any]) -> DagGraph:
        do = DagGraph(**obj)
        db.add(do)
        await db.flush()
        return do

    @classmethod
    async def update(cls, db: AsyncSession, gid: str, data: dict[str, Any]) -> None:
        do = await cls.get_by_id(db, gid)
        if do:
            for k, v in data.items():
                setattr(do, k, v)
            await db.flush()

    @classmethod
    async def remove_by_dag(cls, db: AsyncSession, dag_task_id: str) -> None:
        await db.execute(delete(DagGraph).where(DagGraph.dag_task_id == dag_task_id))
