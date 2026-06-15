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

from celery import Celery
from celery.signals import worker_process_init
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
