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
    from celery.exceptions import SoftTimeLimitExceeded

    instance_id = self.request.id
    worker = self.request.hostname
    retries = self.request.retries
    try:
        return execute_task(task_id, instance_id, worker=worker, retry_num=retries)
    except SoftTimeLimitExceeded as e:
        # 超时:视为失败,直接告警、不重试(重试大概率还会超时);硬超时会 SIGKILL 释放槽位
        from module_task_schedule.alert_hook import trigger_task_fail_alert

        trigger_task_fail_alert(task_id, instance_id, worker, retries, e)
        raise
    except Exception as e:
        retry_count, retry_interval = _load_retry_conf(task_id)
        if retries < retry_count:
            raise self.retry(exc=e, countdown=retry_interval, max_retries=retry_count)
        # 重试耗尽 -> 触发失败告警(按任务绑定的告警策略转发)
        from module_task_schedule.alert_hook import trigger_task_fail_alert

        trigger_task_fail_alert(task_id, instance_id, worker, retries, e)
        raise


@celery_app.task(bind=True, name='module_task_schedule.run_dag')
def run_dag(self: Any, dag_task_id: str, source: str = 'published') -> str:
    """DAG 调度入口:建 run 实例,按运行模式分布式派发或单机顺序执行。"""
    from module_task_schedule.dag_orchestrator import advance_dag, run_dag_single, start_dag_run

    dag_run_id = self.request.id
    run_type = start_dag_run(dag_run_id, dag_task_id, source, self.request.hostname)
    if run_type == 2:  # 单机:本进程顺序跑完
        run_dag_single(dag_run_id, self.request.hostname)
    else:  # 分布式:事件驱动派发,各节点独立 celery 任务
        advance_dag(dag_run_id)
    return dag_run_id


@celery_app.task(bind=True, name='module_task_schedule.run_single_node')
def run_single_node(self: Any, dag_task_id: str, node_key: str, source: str = 'draft') -> str:
    """单独运行 DAG 的某个节点(调试用)。"""
    from module_task_schedule.dag_orchestrator import execute_single_node

    return execute_single_node(dag_task_id, node_key, self.request.id, self.request.hostname, source)


@celery_app.task(bind=True, name='module_task_schedule.run_dag_node')
def run_dag_node(self: Any, dag_run_id: str, node_key: str) -> str:
    """执行单个 DAG 节点,完成后推进下游;节点级失败重试。"""
    from module_task_schedule.dag_orchestrator import advance_dag, execute_dag_node, node_retry_conf

    instance_id = self.request.id
    worker = self.request.hostname
    retries = self.request.retries
    try:
        res = execute_dag_node(dag_run_id, node_key, instance_id, worker=worker, retry_num=retries)
        advance_dag(dag_run_id)  # 成功 -> 触发下游
        return res
    except Exception as e:
        retry_count, retry_interval = node_retry_conf(dag_run_id, node_key)
        if retries < retry_count:
            raise self.retry(exc=e, countdown=retry_interval, max_retries=retry_count)
        advance_dag(dag_run_id)  # 终态失败 -> DAG 置失败 + 下游 SKIPPED
        raise


@celery_app.task(bind=True, name='module_data.sync_catalog_index')
def sync_catalog_index(self: Any, datasource_code: str | None = None) -> str:
    """同步数据目录检索索引(Agent 按问题检索表用)。

    datasource_code 有值 → 只同步该源的模型(数据源管理「同步」按钮);为空 → 全量重建。
    embedding 大库可能耗时,故走 worker 异步执行,不阻塞 Web。
    """
    from module_ai.tools.catalog_index import CatalogRetrievalService

    if datasource_code:
        n = CatalogRetrievalService.sync_datasource(datasource_code)
    else:
        n = CatalogRetrievalService.rebuild()
    return f'catalog index synced: {n} tables (source={datasource_code or "ALL"})'
