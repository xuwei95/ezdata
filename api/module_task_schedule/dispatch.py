"""
任务分发入口(APScheduler 触发模板任务时调用)

定时任务在 sys_job 上维护，invoke_target 统一指向 module_task_schedule.dispatch.run_task，
job_args 为 task_id。run_task 读取任务的运行队列并投递到 Celery，由 worker 分布式执行。
"""

from typing import Any

from loguru import logger as loguru_logger
from sqlalchemy import select

from module_task_schedule.sync_db import get_sync_session_local

_HARD_GRACE_SECONDS = 300  # 自定义超时时,硬超时 = 软超时 + 该宽限
_UNLIMITED_SECONDS = 10 * 365 * 24 * 3600  # timeout=-1(不限)时用的极大值(≈10年)


def _load_run_conf(task_id: str) -> tuple[str, int]:
    """读取任务的运行队列与超时配置 (queue, timeout 秒)。"""
    from module_task_schedule.entity.do.task_do import Task

    session_local = get_sync_session_local()
    db = session_local()
    try:
        task = db.execute(select(Task).where(Task.id == task_id)).scalars().first()
        if task is None:
            return 'default', 0
        return (task.run_queue or 'default'), int(task.timeout or 0)
    finally:
        db.close()


def _timeout_opts(timeout: int) -> dict:
    """按任务级 timeout 生成 Celery 每任务超时选项:0=用全局默认(不覆盖)/-1=不限/>0=自定义。"""
    if timeout == 0:
        return {}
    if timeout < 0:
        return {'soft_time_limit': _UNLIMITED_SECONDS, 'time_limit': _UNLIMITED_SECONDS}
    return {'soft_time_limit': timeout, 'time_limit': timeout + _HARD_GRACE_SECONDS}


def _load_run_queue(task_id: str) -> str:
    """读取任务的运行队列(兼容旧调用)。"""
    return _load_run_conf(task_id)[0]


def run_task(task_id: Any, *args: Any, **kwargs: Any) -> str | None:
    """模板任务分发入口(被 APScheduler 调度触发或手动执行)：投递到 Celery 队列"""
    task_id = str(task_id)
    queue, timeout = _load_run_conf(task_id)

    from config.celery_app import celery_app

    async_result = celery_app.send_task(
        'module_task_schedule.run_task', args=[task_id], queue=queue, **_timeout_opts(timeout)
    )
    loguru_logger.info(
        f'任务已投递到 Celery: task_id={task_id} queue={queue} timeout={timeout} instance={async_result.id}'
    )
    return async_result.id


def run_dag(dag_task_id: Any, source: str = 'published') -> str | None:
    """DAG 分发入口:投递 run_dag 到 Celery(返回的 task id 即 DAG run 实例id)。"""
    dag_task_id = str(dag_task_id)
    queue, timeout = _load_run_conf(dag_task_id)

    from config.celery_app import celery_app

    async_result = celery_app.send_task(
        'module_task_schedule.run_dag', args=[dag_task_id, source], queue=queue, **_timeout_opts(timeout)
    )
    loguru_logger.info(f'DAG 已投递: dag={dag_task_id} source={source} queue={queue} run={async_result.id}')
    return async_result.id


def run_single_node(dag_task_id: Any, node_key: str, source: str = 'draft') -> str | None:
    """单独运行 DAG 节点(调试)。"""
    dag_task_id = str(dag_task_id)
    queue = _load_run_queue(dag_task_id)

    from config.celery_app import celery_app

    async_result = celery_app.send_task(
        'module_task_schedule.run_single_node', args=[dag_task_id, node_key, source], queue=queue
    )
    return async_result.id
