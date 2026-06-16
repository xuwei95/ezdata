"""
Celery 任务：单任务的分布式执行入口

run_task 由 dispatch 投递；它调用执行核心 execute_task，并负责失败重试。
重试沿用同一 instance_id(self.request.id 在 retry 间保持不变)。
"""

from typing import Any

from sqlalchemy import select

from config.celery_app import celery_app
from module_task_schedule.executor import execute_task
from module_task_schedule.sync_db import get_sync_session_local


def _load_retry_conf(task_id: str) -> tuple[int, int]:
    """读取任务的重试次数与重试间隔(秒)"""
    from module_task_schedule.entity.do.task_do import Task

    session_local = get_sync_session_local()
    db = session_local()
    try:
        task = db.execute(select(Task).where(Task.id == task_id)).scalars().first()
        if task is None:
            return 0, 60
        return int(task.retry or 0), int(task.countdown or 60)
    finally:
        db.close()


@celery_app.task(bind=True, name='module_task_schedule.run_task')
def run_task(self: Any, task_id: str) -> str:
    """执行模板任务(单任务)"""
    instance_id = self.request.id
    worker = self.request.hostname
    retries = self.request.retries
    try:
        return execute_task(task_id, instance_id, worker=worker, retry_num=retries)
    except Exception as e:  # noqa: BLE001
        retry_count, retry_interval = _load_retry_conf(task_id)
        if retries < retry_count:
            raise self.retry(exc=e, countdown=retry_interval, max_retries=retry_count)
        # 重试耗尽 -> 触发失败告警(按任务绑定的告警策略转发)
        from module_task_schedule.alert_hook import trigger_task_fail_alert

        trigger_task_fail_alert(task_id, instance_id, worker, retries, e)
        raise
