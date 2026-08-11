"""
Celery 应用：任务调度的分布式执行层

broker / result backend 默认复用项目已有 Redis(独立 db，见 CeleryConfig.celery_redis_database)，
也可通过 celery_broker_url / celery_result_backend 显式指定。Worker 为独立同步进程，
prefork 后通过 worker_process_init 重建任务模块的同步数据库引擎，避免子进程复用父进程连接。

启动 worker(开发,Windows)：
    celery -A config.celery_app worker -Q default -P solo --loglevel=INFO
启动 worker(Linux)：
    celery -A config.celery_app worker -Q default --loglevel=INFO
"""

import os
import sys

# 确保项目根目录在 sys.path 中，使 Celery worker(含 prefork 子进程)能稳定解析
# 命名空间包。Web 端由 RouterRegister 注入，worker 需在此自行注入。
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import time as _time

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun, task_retry, task_success, worker_process_init
from kombu import Queue

from config.env import CeleryConfig, RedisConfig


def _redis_url(db: int) -> str:
    auth = ''
    if RedisConfig.redis_password:
        user = RedisConfig.redis_username or ''
        auth = f'{user}:{RedisConfig.redis_password}@'
    return f'redis://{auth}{RedisConfig.redis_host}:{RedisConfig.redis_port}/{db}'


# broker / backend：优先使用显式配置，否则复用 Redis(独立 db，与应用缓存隔离)
_broker_url = CeleryConfig.celery_broker_url or _redis_url(CeleryConfig.celery_redis_database)
_backend_url = CeleryConfig.celery_result_backend or _redis_url(CeleryConfig.celery_redis_database)

celery_app = Celery(
    'ruoyi_task',
    broker=_broker_url,
    backend=_backend_url,
    include=['module_task_schedule.celery_tasks'],
)

celery_app.conf.update(
    task_default_queue=CeleryConfig.celery_default_queue,
    task_queues=tuple(Queue(name) for name in CeleryConfig.queue_list),
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone=CeleryConfig.celery_timezone,
    enable_utc=False,
    task_track_started=True,
    result_expires=CeleryConfig.celery_result_expires,
    worker_max_tasks_per_child=CeleryConfig.celery_worker_max_tasks_per_child,
    # 全局超时:软超时抛 SoftTimeLimitExceeded(任务内捕获→失败告警);硬超时 SIGKILL 卡死子进程,释放槽位。
    # 任务级 Task.timeout 会在 dispatch 时按任务覆盖(0=默认/-1=不限/>0=自定义)。
    task_soft_time_limit=CeleryConfig.celery_task_soft_time_limit,
    task_time_limit=CeleryConfig.celery_task_time_limit,
    # 一次只预取 1 个任务:卡死的任务不会连累它预取的其它任务,减少队列堵塞。
    worker_prefetch_multiplier=CeleryConfig.celery_worker_prefetch_multiplier,
    worker_hijack_root_logger=False,
    broker_connection_retry_on_startup=True,
    # 允许通过 control.pool_restart 远程重启 worker 池(Worker 管理用)
    worker_pool_restarts=True,
)


@worker_process_init.connect
def _init_worker_process(**kwargs) -> None:
    """worker 子进程初始化：重建同步数据库引擎"""
    from module_task_schedule.sync_db import reset_sync_engine

    reset_sync_engine()


# —— 链路追踪 + Prometheus 指标(任务级信号,覆盖所有 celery 任务) ——
_task_start: dict[str, float] = {}


@task_prerun.connect
def _on_task_prerun(task_id=None, task=None, **kwargs) -> None:
    """继承 HTTP 派发的 trace_id(headers 无则用 task_id),使 worker 日志与 backend 同链路;并计时。"""
    try:
        from middlewares.trace_middleware.ctx import TraceCtx

        headers = getattr(getattr(task, 'request', None), 'headers', None) or {}
        TraceCtx.set_trace_id_value(headers.get('trace_id') or task_id or '')
    except Exception:
        pass
    if task_id:
        _task_start[task_id] = _time.monotonic()


@task_postrun.connect
def _on_task_postrun(task_id=None, task=None, **kwargs) -> None:
    """记录任务时长并清理链路上下文。"""
    try:
        from common import metrics

        started = _task_start.pop(task_id, None)
        if started is not None:
            metrics.observe_celery_duration(getattr(task, 'name', 'unknown'), _time.monotonic() - started)
    except Exception:
        pass
    try:
        from middlewares.trace_middleware.ctx import TraceCtx

        TraceCtx.set_trace_id_value('')
    except Exception:
        pass


@task_success.connect
def _on_task_success(sender=None, **kwargs) -> None:
    _inc_celery(getattr(sender, 'name', 'unknown'), 'success')


@task_failure.connect
def _on_task_failure(sender=None, **kwargs) -> None:
    _inc_celery(getattr(sender, 'name', 'unknown'), 'failure')


@task_retry.connect
def _on_task_retry(sender=None, **kwargs) -> None:
    _inc_celery(getattr(sender, 'name', 'unknown'), 'retry')


def _inc_celery(name: str, status: str) -> None:
    try:
        from common import metrics

        metrics.inc_celery_task(name, status)
    except Exception:
        pass
