from typing import Annotated

from fastapi import Query, Request, Response

from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel, ResponseBaseModel
from module_task_schedule.entity.vo.worker_vo import (
    WorkerAutoscaleModel,
    WorkerConsumerModel,
    WorkerScaleModel,
)
from module_task_schedule.service.worker_service import WorkerService
from utils.log_util import logger
from utils.response_util import ResponseUtil

worker_controller = APIRouterPro(
    prefix='/task/worker', order_num=14, tags=['任务调度-Worker管理'], dependencies=[PreAuthDependency()]
)


@worker_controller.get(
    '/list',
    summary='获取 Worker 列表(实时)',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('task:worker:list')],
)
async def get_worker_list(request: Request) -> Response:
    result = WorkerService.get_worker_list()
    logger.info('获取 Worker 列表成功')
    return ResponseUtil.success(data=result)


@worker_controller.get(
    '/tasks',
    summary='获取 Worker 当前运行任务',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('task:worker:list')],
)
async def get_active_tasks(request: Request, worker: Annotated[str | None, Query(description='worker 名称')] = None) -> Response:
    result = WorkerService.get_active_tasks(worker)
    logger.info('获取 Worker 运行任务成功')
    return ResponseUtil.success(data=result)


@worker_controller.put(
    '/consumer/add',
    summary='增加 Worker 消费队列',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:worker:consumer')],
)
async def add_consumer(request: Request, body: WorkerConsumerModel) -> Response:
    WorkerService.add_consumer(body.worker, body.queue)
    logger.info(f'worker {body.worker} 增加消费队列 {body.queue}')
    return ResponseUtil.success(msg='增加消费队列成功')


@worker_controller.put(
    '/consumer/cancel',
    summary='移除 Worker 消费队列',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:worker:consumer')],
)
async def cancel_consumer(request: Request, body: WorkerConsumerModel) -> Response:
    WorkerService.cancel_consumer(body.worker, body.queue)
    logger.info(f'worker {body.worker} 移除消费队列 {body.queue}')
    return ResponseUtil.success(msg='移除消费队列成功')


@worker_controller.put(
    '/pool/grow',
    summary='增加 Worker 并发',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:worker:scale')],
)
async def pool_grow(request: Request, body: WorkerScaleModel) -> Response:
    WorkerService.pool_grow(body.worker, body.n)
    logger.info(f'worker {body.worker} 增加并发 {body.n}')
    return ResponseUtil.success(msg='增加并发成功')


@worker_controller.put(
    '/pool/shrink',
    summary='减少 Worker 并发',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:worker:scale')],
)
async def pool_shrink(request: Request, body: WorkerScaleModel) -> Response:
    WorkerService.pool_shrink(body.worker, body.n)
    logger.info(f'worker {body.worker} 减少并发 {body.n}')
    return ResponseUtil.success(msg='减少并发成功')


@worker_controller.put(
    '/pool/autoscale',
    summary='设置 Worker 弹性并发',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('task:worker:scale')],
)
async def autoscale(request: Request, body: WorkerAutoscaleModel) -> Response:
    WorkerService.autoscale(body.worker, body.max, body.min)
    logger.info(f'worker {body.worker} 设置弹性并发 {body.min}-{body.max}')
    return ResponseUtil.success(msg='设置弹性并发成功')
