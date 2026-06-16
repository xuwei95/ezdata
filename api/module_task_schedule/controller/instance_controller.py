from typing import Annotated

from fastapi import Path, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_task_schedule.entity.vo.task_vo import TaskInstanceModel, TaskInstancePageQueryModel
from module_task_schedule.service.instance_service import TaskInstanceService
from utils.log_util import logger
from utils.response_util import ResponseUtil

task_instance_controller = APIRouterPro(
    prefix='/task/instance', order_num=12, tags=['任务调度-执行记录'], dependencies=[PreAuthDependency()]
)


@task_instance_controller.get(
    '/list',
    summary='获取任务执行记录分页列表',
    response_model=PageResponseModel[TaskInstanceModel],
    dependencies=[UserInterfaceAuthDependency('task:instance:list')],
)
async def get_instance_list(
    request: Request,
    instance_page_query: Annotated[TaskInstancePageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskInstanceService.get_instance_list_services(query_db, instance_page_query, is_page=True)
    logger.info('获取成功')
    return ResponseUtil.success(model_content=result)


@task_instance_controller.put(
    '/stop/{instance_id}',
    summary='终止正在运行的执行实例',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:instance:stop')],
)
@Log(title='任务执行记录', business_type=BusinessType.OTHER)
async def stop_instance(
    request: Request,
    instance_id: Annotated[str, Path(description='执行实例ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskInstanceService.stop_instance_services(query_db, instance_id)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@task_instance_controller.delete(
    '/{instance_ids}',
    summary='删除执行记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:instance:remove')],
)
@Log(title='任务执行记录', business_type=BusinessType.DELETE)
async def delete_instance(
    request: Request,
    instance_ids: Annotated[str, Path(description='需要删除的执行记录ID(逗号分隔)')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskInstanceService.delete_instance_services(query_db, instance_ids)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@task_instance_controller.get(
    '/{instance_id}',
    summary='获取执行记录详情',
    response_model=DataResponseModel[TaskInstanceModel],
    dependencies=[UserInterfaceAuthDependency('task:instance:query')],
)
async def get_instance_detail(
    request: Request,
    instance_id: Annotated[str, Path(description='执行实例ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskInstanceService.instance_detail_services(query_db, instance_id)
    logger.info(f'获取执行记录{instance_id}信息成功')
    return ResponseUtil.success(data=result)
