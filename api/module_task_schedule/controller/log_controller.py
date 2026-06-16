from typing import Annotated

from fastapi import Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel
from module_task_schedule.entity.vo.task_vo import TaskLogModel, TaskLogQueryModel
from module_task_schedule.service.log_service import TaskLogService
from utils.log_util import logger
from utils.response_util import ResponseUtil

task_log_controller = APIRouterPro(
    prefix='/task/log', order_num=14, tags=['任务调度-执行明细日志'], dependencies=[PreAuthDependency()]
)


@task_log_controller.get(
    '/viewable',
    summary='查询任务执行明细日志是否支持在线查看(file后端返回false)',
    response_model=DataResponseModel[bool],
)
async def get_task_log_viewable(request: Request) -> Response:
    return ResponseUtil.success(data=TaskLogService.is_viewable())


@task_log_controller.get(
    '/list',
    summary='按执行实例ID(task_instance.id)分页查询任务执行明细日志',
    response_model=PageResponseModel[TaskLogModel],
    dependencies=[UserInterfaceAuthDependency('task:instance:query')],
)
async def get_task_log_list(
    request: Request,
    log_page_query: Annotated[TaskLogQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TaskLogService.get_task_log_list_services(query_db, log_page_query, is_page=True)
    logger.info('获取成功')
    return ResponseUtil.success(model_content=result)
