from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_task_schedule.entity.do.task_do import TaskLog
from module_task_schedule.entity.vo.task_vo import TaskLogQueryModel
from utils.common_util import CamelCaseUtil


class TaskLogDao:
    """
    任务执行明细日志数据库操作层(task_log_type=db 时使用)

    执行明细日志按 task_uuid(执行实例ID,即 task_instance.id)关联。
    """

    @classmethod
    async def get_task_log_list(
        cls, db: AsyncSession, query_object: TaskLogQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """获取某执行实例的「最近 page_size 条」执行明细日志(不分页，按时间正序返回用于滚动展示)。

        日志为持续追加，查看时只关心最新若干条：先按 id 倒序取最近 N 条，再反转为正序展示。
        """
        cond = TaskLog.task_uuid == query_object.task_uuid if query_object.task_uuid else True
        limit = query_object.page_size or 100
        total = (await db.execute(select(func.count()).select_from(TaskLog).where(cond))).scalar() or 0
        latest = (
            (await db.execute(select(TaskLog).where(cond).order_by(TaskLog.id.desc()).limit(limit)))
            .scalars()
            .all()
        )
        rows = list(reversed(latest))  # 反转为时间正序(老->新)，便于控制台式滚动到底部
        return PageModel(
            rows=CamelCaseUtil.transform_result(rows),
            pageNum=1,
            pageSize=limit,
            total=total,
            hasNext=False,
        )

    @classmethod
    async def delete_task_log_by_uuid(cls, db: AsyncSession, task_uuids: list[str]) -> None:
        """按实例ID删除执行明细日志"""
        await db.execute(delete(TaskLog).where(TaskLog.task_uuid.in_(task_uuids)))
