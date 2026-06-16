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
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_task_schedule.entity.vo.task_vo import (
    DeleteTaskModel,
    EditTaskStatusModel,
    TaskModel,
    TaskPageQueryModel,
)
from module_task_schedule.service.task_service import TaskService
from utils.log_util import logger
from utils.response_util import ResponseUtil

task_controller = APIRouterPro(
    prefix='/task/info', order_num=11, tags=['任务调度-任务管理'], dependencies=[PreAuthDependency()]
)


@task_controller.get(
    '/list',
    summary='获取任务分页列表',
    response_model=PageResponseModel[TaskModel],
    dependencies=[UserInterfaceAuthDependency('task:info:list')],
)
async def get_task_list(
    request: Request,
    task_page_query: Annotated[TaskPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskService.get_task_list_services(query_db, task_page_query, is_page=True)
    logger.info('获取成功')
    return ResponseUtil.success(model_content=result)


@task_controller.post(
    '',
    summary='新增任务',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:info:add')],
)
@Log(title='任务管理', business_type=BusinessType.INSERT)
async def add_task(
    request: Request,
    add_task: TaskModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_task.built_in = 0
    add_task.create_by = current_user.user.user_name
    add_task.create_time = datetime.now()
    add_task.update_by = current_user.user.user_name
    add_task.update_time = datetime.now()
    result = await TaskService.add_task_services(query_db, add_task)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@task_controller.put(
    '',
    summary='编辑任务',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:info:edit')],
)
@Log(title='任务管理', business_type=BusinessType.UPDATE)
async def edit_task(
    request: Request,
    edit_task: TaskModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_task.update_by = current_user.user.user_name
    edit_task.update_time = datetime.now()
    result = await TaskService.edit_task_services(query_db, edit_task)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@task_controller.put(
    '/changeStatus',
    summary='修改任务状态(启用/停用)',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:info:changeStatus')],
)
@Log(title='任务管理', business_type=BusinessType.UPDATE)
async def change_task_status(
    request: Request,
    edit_status: EditTaskStatusModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskService.edit_task_status_services(query_db, edit_status)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@task_controller.put(
    '/run/{task_id}',
    summary='手动执行一次任务',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:info:run')],
)
@Log(title='任务管理', business_type=BusinessType.OTHER)
async def run_task_once(
    request: Request,
    task_id: Annotated[str, Path(description='任务ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskService.run_task_once_services(query_db, task_id)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message, data=result.result)


@task_controller.delete(
    '/{task_ids}',
    summary='删除任务',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:info:remove')],
)
@Log(title='任务管理', business_type=BusinessType.DELETE)
async def delete_task(
    request: Request,
    task_ids: Annotated[str, Path(description='需要删除的任务ID(逗号分隔)')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskService.delete_task_services(query_db, DeleteTaskModel(ids=task_ids))
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@task_controller.get(
    '/queues',
    summary='实时获取可用运行队列',
    response_model=DataResponseModel[list[str]],
    dependencies=[UserInterfaceAuthDependency('task:info:list')],
)
async def get_run_queues(request: Request) -> Response:
    result = TaskService.get_run_queues()
    logger.info('获取运行队列成功')
    return ResponseUtil.success(data=result)


@task_controller.get(
    '/{task_id}',
    summary='获取任务详情',
    response_model=DataResponseModel[TaskModel],
    dependencies=[UserInterfaceAuthDependency('task:info:query')],
)
async def get_task_detail(
    request: Request,
    task_id: Annotated[str, Path(description='任务ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskService.task_detail_services(query_db, task_id)
    logger.info(f'获取任务{task_id}信息成功')
    return ResponseUtil.success(data=result)
