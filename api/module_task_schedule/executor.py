"""
任务执行核心

独立于 Celery 的执行函数：加载任务与模板 -> 维护 task_instance 执行记录(开始/结束/进度) ->
选择 runner 执行 -> 通过 TaskLogger 写执行明细日志。单任务与 DAG 节点都复用本核心。

不在此处做重试编排(由 Celery 任务负责)，本函数只负责"执行 + 记录 + 抛出"。
"""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.context import RequestContext
from module_task_schedule.entity.do.task_do import Task, TaskInstance, TaskTemplate
from module_task_schedule.runners.base import get_runner
from module_task_schedule.runners.dynamic_runner import DynamicRunner
from module_task_schedule.sync_db import get_sync_session_local
from module_task_schedule.task_logger import get_task_logger


def _load_task(db: Session, task_id: str) -> Task | None:
    return db.execute(select(Task).where(Task.id == task_id)).scalars().first()


def _load_template(db: Session, template_code: str) -> TaskTemplate | None:
    return db.execute(select(TaskTemplate).where(TaskTemplate.code == template_code)).scalars().first()


def _upsert_instance(db: Session, instance_id: str, values: dict[str, Any]) -> None:
    """按 id(celery task uuid)创建或更新 task_instance 执行记录(重试时复用同一行)"""
    obj = db.execute(select(TaskInstance).where(TaskInstance.id == instance_id)).scalars().first()
    if obj is None:
        obj = TaskInstance(id=instance_id)
        for k, v in values.items():
            setattr(obj, k, v)
        db.add(obj)
    else:
        for k, v in values.items():
            setattr(obj, k, v)
    db.commit()


def execute_task(task_id: str, instance_id: str, worker: str | None = None, retry_num: int = 0) -> str:
    """
    执行一个模板任务并维护执行记录与明细日志。

    :param task_id: task 主键
    :param instance_id: 执行实例ID(Celery任务UUID)
    :param worker: 执行节点标识
    :param retry_num: 当前重试次数
    :return: 执行结果摘要
    :raises: 执行失败时记录后向上抛出，供上层(Celery)重试
    """
    session_local = get_sync_session_local()
    db = session_local()
    # 多租户：Worker 无请求上下文。先(无租户上下文=不过滤)按主键加载任务，
    # 读出其 tenant_id 后设置上下文，使后续 task_instance/task_log 写入自动盖章、按租户查询。
    tenant_token = None
    try:
        task = _load_task(db, task_id)
        if task is None:
            raise ValueError(f'任务不存在: task_id={task_id}')

        tenant_token = RequestContext.set_current_tenant_id(task.tenant_id)
        template_code = task.template_code
        params: dict[str, Any] = json.loads(task.params) if task.params else {}

        # 记录执行开始
        _upsert_instance(
            db,
            instance_id,
            {
                'task_id': task_id,
                'name': task.name,
                'status': 'STARTED',
                'worker': worker,
                'retry_num': retry_num,
                'progress': 0,
                'start_time': datetime.now(),
                'closed': 0,
            },
        )
    except Exception:
        if tenant_token is not None:
            RequestContext.reset_current_tenant_id(tenant_token)
        db.close()
        raise

    logger = get_task_logger(instance_id)
    try:
        template = _load_template(db, template_code) if template_code else None
        if template is None:
            raise ValueError(f'任务模板不存在: {template_code}')

        logger.info(f'任务开始 task_id={task_id} 模板={template_code} worker={worker} 重试={retry_num}')
        logger.info(f'任务参数: {params}')

        if template.runner_type == 2:
            runner = DynamicRunner(params, logger, context={'runner_code': template.runner_code, 'sandbox': True})
        else:
            runner_cls = get_runner(template_code)
            if runner_cls is None:
                raise ValueError(f'未找到内置执行器: {template_code}')
            runner = runner_cls(params, logger, context={'sandbox': True})

        result = runner.run()
        result_summary = str(result)[:500] if result is not None else '执行成功'
        logger.info(f'任务完成: {result_summary}')

        _upsert_instance(
            db,
            instance_id,
            {
                'status': 'SUCCESS',
                'progress': 100,
                'end_time': datetime.now(),
                'result': result_summary,
                'closed': 1,
            },
        )
        return result_summary
    except Exception as e:
        err = str(e)
        try:
            logger.exception(f'任务执行失败: {err}')  # 完整堆栈进日志
        except Exception:
            pass
        # 执行记录的 result 仅存简短摘要(完整信息看明细日志),避免列表/详情里超长
        brief = ' '.join(err.split())
        if len(brief) > 500:
            brief = f'{brief[:440]} …(已截断,完整见执行日志)'
        _upsert_instance(
            db,
            instance_id,
            {'status': 'FAILURE', 'end_time': datetime.now(), 'result': brief, 'closed': 1},
        )
        raise
    finally:
        try:
            logger.close()
        except Exception:
            pass
        if tenant_token is not None:
            RequestContext.reset_current_tenant_id(tenant_token)
        db.close()
