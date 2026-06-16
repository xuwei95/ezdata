from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_task_schedule.dao.template_dao import TaskTemplateDao
from module_task_schedule.entity.vo.task_vo import (
    DeleteTaskTemplateModel,
    TaskTemplateModel,
    TaskTemplatePageQueryModel,
)
from utils.common_util import CamelCaseUtil


class TaskTemplateService:
    """
    任务模板服务层
    """

    @classmethod
    async def get_template_list_services(
        cls, query_db: AsyncSession, query_object: TaskTemplatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """获取模板列表service"""
        return await TaskTemplateDao.get_template_list(query_db, query_object, is_page)

    @classmethod
    async def template_detail_services(cls, query_db: AsyncSession, template_id: str) -> TaskTemplateModel:
        """获取模板详情service"""
        template = await TaskTemplateDao.get_template_by_id(query_db, template_id)
        return TaskTemplateModel(**CamelCaseUtil.transform_result(template)) if template else TaskTemplateModel()

    @classmethod
    async def add_template_services(cls, query_db: AsyncSession, page_object: TaskTemplateModel) -> CrudResponseModel:
        """新增模板service"""
        exist = await TaskTemplateDao.get_template_by_code(query_db, page_object.code)
        if exist:
            raise ServiceException(message=f'模板编码已存在: {page_object.code}')
        try:
            await TaskTemplateDao.add_template_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_template_services(cls, query_db: AsyncSession, page_object: TaskTemplateModel) -> CrudResponseModel:
        """编辑模板service"""
        template = await TaskTemplateDao.get_template_by_id(query_db, page_object.id)
        if not template or not template.id:
            raise ServiceException(message='任务模板不存在')
        if template.built_in == 1:
            # 内置模板仅允许改名称/状态/参数，不允许改编码与执行器类型
            page_object.code = template.code
            page_object.runner_type = template.runner_type
        try:
            await TaskTemplateDao.edit_template_dao(query_db, page_object.model_dump(exclude_unset=True))
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_template_services(
        cls, query_db: AsyncSession, page_object: DeleteTaskTemplateModel
    ) -> CrudResponseModel:
        """删除模板service(内置模板不可删除；存在关联任务不可删除)"""
        from module_task_schedule.dao.task_dao import TaskDao

        if not page_object.ids:
            raise ServiceException(message='传入模板id为空')
        id_list = [i for i in page_object.ids.split(',') if i]
        for tid in id_list:
            template = await TaskTemplateDao.get_template_by_id(query_db, tid)
            if not template:
                continue
            if template.built_in == 1:
                raise ServiceException(message=f'内置模板不可删除: {template.name}')
            # 存在关联任务时禁止删除
            task_count = await TaskDao.count_by_template_code(query_db, template.code)
            if task_count > 0:
                raise ServiceException(message=f'模板[{template.name}]存在{task_count}个关联任务，无法删除')
        try:
            await TaskTemplateDao.delete_template_dao(query_db, id_list)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e
