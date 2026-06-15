from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_task_schedule.entity.do.task_do import TaskTemplate
from module_task_schedule.entity.vo.task_vo import TaskTemplateModel, TaskTemplatePageQueryModel
from utils.page_util import PageUtil


class TaskTemplateDao:
    """
    任务模板数据库操作层
    """

    @classmethod
    async def get_template_by_id(cls, db: AsyncSession, template_id: str) -> TaskTemplate | None:
        """根据模板id获取模板详情"""
        return (await db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))).scalars().first()

    @classmethod
    async def get_template_by_code(cls, db: AsyncSession, code: str) -> TaskTemplate | None:
        """根据模板编码获取模板"""
        return (await db.execute(select(TaskTemplate).where(TaskTemplate.code == code))).scalars().first()

    @classmethod
    async def get_template_list(
        cls, db: AsyncSession, query_object: TaskTemplatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """根据查询参数获取模板列表"""
        query = (
            select(TaskTemplate)
            .where(
                TaskTemplate.name.like(f'%{query_object.name}%') if query_object.name else True,
                TaskTemplate.code.like(f'%{query_object.code}%') if query_object.code else True,
                TaskTemplate.status == query_object.status if query_object.status is not None else True,
                TaskTemplate.create_time.between(query_object.begin_time, query_object.end_time)
                if query_object.begin_time and query_object.end_time
                else True,
            )
            .order_by(TaskTemplate.create_time.desc())
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def add_template_dao(cls, db: AsyncSession, template: TaskTemplateModel) -> TaskTemplate:
        """新增模板"""
        db_obj = TaskTemplate(**template.model_dump(exclude_unset=True))
        db.add(db_obj)
        await db.flush()
        return db_obj

    @classmethod
    async def edit_template_dao(cls, db: AsyncSession, template: dict) -> None:
        """编辑模板"""
        await db.execute(update(TaskTemplate), [template])

    @classmethod
    async def delete_template_dao(cls, db: AsyncSession, template_ids: list[str]) -> None:
        """删除模板"""
        await db.execute(delete(TaskTemplate).where(TaskTemplate.id.in_(template_ids)))
