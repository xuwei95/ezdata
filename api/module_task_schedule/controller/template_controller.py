import uuid
from datetime import datetime
from typing import Annotated

from fastapi import Path, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from exceptions.exception import PermissionException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_task_schedule.entity.vo.task_vo import (
    DeleteTaskTemplateModel,
    TaskTemplateModel,
    TaskTemplatePageQueryModel,
)
from module_task_schedule.service.template_service import TaskTemplateService
from utils.log_util import logger
from utils.response_util import ResponseUtil

task_template_controller = APIRouterPro(
    prefix='/task/template', order_num=13, tags=['任务调度-任务模板'], dependencies=[PreAuthDependency()]
)


def _require_super_admin(current_user: CurrentUserModel) -> None:
    """模板含可执行代码(runner_code)，创建/修改仅允许超级管理员"""
    if not current_user.user.admin:
        raise PermissionException(data='', message='任务模板包含可执行代码，仅超级管理员可维护')


@task_template_controller.get(
    '/list',
    summary='获取任务模板分页列表',
    response_model=PageResponseModel[TaskTemplateModel],
    dependencies=[UserInterfaceAuthDependency('task:template:list')],
)
async def get_template_list(
    request: Request,
    template_page_query: Annotated[TaskTemplatePageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskTemplateService.get_template_list_services(query_db, template_page_query, is_page=True)
    logger.info('获取成功')
    return ResponseUtil.success(model_content=result)


@task_template_controller.get(
    '/all',
    summary='获取启用的任务模板(不分页,供任务表单选择)',
    response_model=DataResponseModel[TaskTemplateModel],
)
async def get_template_all(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskTemplateService.get_template_list_services(
        query_db, TaskTemplatePageQueryModel(status=1), is_page=False
    )
    return ResponseUtil.success(data=result)


@task_template_controller.post(
    '',
    summary='新增任务模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:template:add')],
)
@Log(title='任务模板', business_type=BusinessType.INSERT)
async def add_template(
    request: Request,
    add_template: TaskTemplateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    _require_super_admin(current_user)
    add_template.id = uuid.uuid4().hex
    add_template.built_in = 0
    add_template.create_by = current_user.user.user_name
    add_template.create_time = datetime.now()
    add_template.update_by = current_user.user.user_name
    add_template.update_time = datetime.now()
    result = await TaskTemplateService.add_template_services(query_db, add_template)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@task_template_controller.put(
    '',
    summary='编辑任务模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:template:edit')],
)
@Log(title='任务模板', business_type=BusinessType.UPDATE)
async def edit_template(
    request: Request,
    edit_template: TaskTemplateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    _require_super_admin(current_user)
    edit_template.update_by = current_user.user.user_name
    edit_template.update_time = datetime.now()
    result = await TaskTemplateService.edit_template_services(query_db, edit_template)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@task_template_controller.delete(
    '/{template_ids}',
    summary='删除任务模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:template:remove')],
)
@Log(title='任务模板', business_type=BusinessType.DELETE)
async def delete_template(
    request: Request,
    template_ids: Annotated[str, Path(description='需要删除的模板ID(逗号分隔)')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    _require_super_admin(current_user)
    result = await TaskTemplateService.delete_template_services(query_db, DeleteTaskTemplateModel(ids=template_ids))
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@task_template_controller.get(
    '/{template_id}',
    summary='获取任务模板详情',
    response_model=DataResponseModel[TaskTemplateModel],
    dependencies=[UserInterfaceAuthDependency('task:template:query')],
)
async def get_template_detail(
    request: Request,
    template_id: Annotated[str, Path(description='模板ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskTemplateService.template_detail_services(query_db, template_id)
    logger.info(f'获取模板{template_id}信息成功')
    return ResponseUtil.success(data=result)
