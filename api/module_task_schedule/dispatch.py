"""
任务分发入口(APScheduler 触发模板任务时调用)

定时任务在 sys_job 上维护，invoke_target 统一指向 module_task_schedule.dispatch.run_task，
job_args 为 task_id。run_task 读取任务的运行队列并投递到 Celery，由 worker 分布式执行。
"""

from typing import Any

from loguru import logger as loguru_logger
from sqlalchemy import select

from module_task_schedule.sync_db import get_sync_session_local


def _load_run_queue(task_id: str) -> str:
    """读取任务的运行队列"""
    from module_task_schedule.entity.do.task_do import Task

    session_local = get_sync_session_local()
    db = session_local()
    try:
        task = db.execute(select(Task).where(Task.id == task_id)).scalars().first()
        if task is None or not task.run_queue:
            return 'default'
        return task.run_queue
    finally:
        db.close()


def run_task(task_id: Any, *args: Any, **kwargs: Any) -> str | None:
    """模板任务分发入口(被 APScheduler 调度触发或手动执行)：投递到 Celery 队列"""
    task_id = str(task_id)
    queue = _load_run_queue(task_id)

    from config.celery_app import celery_app

    async_result = celery_app.send_task('module_task_schedule.run_task', args=[task_id], queue=queue)
    loguru_logger.info(f'任务已投递到 Celery: task_id={task_id} queue={queue} instance={async_result.id}')
    return async_result.id


def run_dag(dag_task_id: Any, source: str = 'published') -> str | None:
    """DAG 分发入口:投递 run_dag 到 Celery(返回的 task id 即 DAG run 实例id)。"""
    dag_task_id = str(dag_task_id)
    queue = _load_run_queue(dag_task_id)

    from config.celery_app import celery_app

    async_result = celery_app.send_task(
        'module_task_schedule.run_dag', args=[dag_task_id, source], queue=queue)
    loguru_logger.info(f'DAG 已投递: dag={dag_task_id} source={source} queue={queue} run={async_result.id}')
    return async_result.id


def run_single_node(dag_task_id: Any, node_key: str, source: str = 'draft') -> str | None:
    """单独运行 DAG 节点(调试)。"""
    dag_task_id = str(dag_task_id)
    queue = _load_run_queue(dag_task_id)

    from config.celery_app import celery_app

    async_result = celery_app.send_task(
        'module_task_schedule.run_single_node', args=[dag_task_id, node_key, source], queue=queue)
    return async_result.id
