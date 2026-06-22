from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_task_schedule.entity.do.task_do import Task
from module_task_schedule.entity.vo.task_vo import TaskModel, TaskPageQueryModel
from utils.page_util import PageUtil


class TaskDao:
    """
    任务数据库操作层
    """

    @classmethod
    async def get_task_by_id(cls, db: AsyncSession, task_id: str) -> Task | None:
        """根据任务id获取任务详情"""
        return (await db.execute(select(Task).where(Task.id == task_id))).scalars().first()

    @classmethod
    async def count_by_template_code(cls, db: AsyncSession, template_code: str) -> int:
        """统计使用指定模板编码的任务数量(用于模板删除前的关联校验)"""
        result = await db.execute(select(func.count()).select_from(Task).where(Task.template_code == template_code))
        return int(result.scalar() or 0)

    @classmethod
    async def get_task_list(
        cls, db: AsyncSession, query_object: TaskPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """根据查询参数获取任务列表"""
        query = (
            select(Task)
            .where(
                Task.name.like(f'%{query_object.name}%') if query_object.name else True,
                Task.template_code == query_object.template_code if query_object.template_code else True,
                Task.task_type == (query_object.task_type if query_object.task_type is not None else 1),
                Task.trigger_type == query_object.trigger_type if query_object.trigger_type is not None else True,
                Task.status == query_object.status if query_object.status is not None else True,
                Task.create_time.between(query_object.begin_time, query_object.end_time)
                if query_object.begin_time and query_object.end_time
                else True,
            )
            .order_by(Task.create_time.desc())
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def add_task_dao(cls, db: AsyncSession, task: TaskModel) -> Task:
        """新增任务"""
        db_obj = Task(**task.model_dump(exclude_unset=True))
        db.add(db_obj)
        await db.flush()
        return db_obj

    @classmethod
    async def edit_task_dao(cls, db: AsyncSession, task: dict) -> None:
        """编辑任务"""
        await db.execute(update(Task), [task])

    @classmethod
    async def delete_task_dao(cls, db: AsyncSession, task_ids: list[str]) -> None:
        """删除任务"""
        await db.execute(delete(Task).where(Task.id.in_(task_ids)))
