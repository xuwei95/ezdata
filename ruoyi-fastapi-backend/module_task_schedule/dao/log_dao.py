from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_task_schedule.entity.do.task_do import TaskLog
from module_task_schedule.entity.vo.task_vo import TaskLogQueryModel
from utils.page_util import PageUtil


class TaskLogDao:
    """
    任务执行明细日志数据库操作层(task_log_type=db 时使用)

    执行明细日志按 task_uuid(执行实例ID,即 task_instance.id)关联。
    """

    @classmethod
    async def get_task_log_list(
        cls, db: AsyncSession, query_object: TaskLogQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """根据实例ID分页查询执行明细日志"""
        query = (
            select(TaskLog)
            .where(TaskLog.task_uuid == query_object.task_uuid if query_object.task_uuid else True)
            .order_by(TaskLog.id.asc())
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def delete_task_log_by_uuid(cls, db: AsyncSession, task_uuids: list[str]) -> None:
        """按实例ID删除执行明细日志"""
        await db.execute(delete(TaskLog).where(TaskLog.task_uuid.in_(task_uuids)))
