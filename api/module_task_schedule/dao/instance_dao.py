from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_task_schedule.entity.do.task_do import TaskInstance
from module_task_schedule.entity.vo.task_vo import TaskInstancePageQueryModel
from utils.page_util import PageUtil


class TaskInstanceDao:
    """
    任务实例(执行记录)数据库操作层
    """

    @classmethod
    async def get_instance_by_id(cls, db: AsyncSession, instance_id: str) -> TaskInstance | None:
        """根据实例id获取执行记录详情"""
        return (await db.execute(select(TaskInstance).where(TaskInstance.id == instance_id))).scalars().first()

    @classmethod
    async def get_instance_list(
        cls, db: AsyncSession, query_object: TaskInstancePageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """根据查询参数获取执行记录列表"""
        query = (
            select(TaskInstance)
            .where(
                TaskInstance.task_id == query_object.task_id if query_object.task_id else True,
                TaskInstance.name.like(f'%{query_object.name}%') if query_object.name else True,
                TaskInstance.status == query_object.status if query_object.status else True,
                TaskInstance.start_time.between(query_object.begin_time, query_object.end_time)
                if query_object.begin_time and query_object.end_time
                else True,
            )
            .order_by(TaskInstance.start_time.desc())
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def delete_instance_dao(cls, db: AsyncSession, instance_ids: list[str]) -> None:
        """删除执行记录"""
        await db.execute(delete(TaskInstance).where(TaskInstance.id.in_(instance_ids)))
