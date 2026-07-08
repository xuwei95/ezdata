"""
任务失败告警钩子

解耦执行层与告警中心：任务重试耗尽失败时调用本钩子，由它把上下文转交给告警中心
(module_alert)。告警中心未就绪时安全降级为日志，不影响任务执行流程。
"""

import traceback
from typing import Any


def _exc_location(exception: Any) -> tuple[str, str]:
    """从异常回溯中提取出错文件与行号(对齐 ezdata 告警上下文)"""
    tb = getattr(exception, '__traceback__', None)
    if tb is None:
        return '', ''
    last = traceback.extract_tb(tb)[-1] if traceback.extract_tb(tb) else None
    if last is None:
        return '', ''
    return last.filename or '', str(last.lineno or '')


def trigger_task_fail_alert(task_id: str, instance_id: str, worker: str | None, retries: int, exception: Any) -> None:
    """触发任务失败告警(同步上下文，供 Celery worker 调用)"""
    from loguru import logger as loguru_logger

    try:
        from module_alert.service.alert_service import AlertService
    except ImportError as ie:
        loguru_logger.warning(
            f'告警中心未就绪，跳过告警: task_id={task_id} instance={instance_id} err={exception} importError={ie!r}'
        )
        return
    exc_file, exc_line = _exc_location(exception)
    try:
        AlertService.handle_task_fail_alert_sync(
            task_id=task_id,
            instance_id=instance_id,
            worker=worker,
            retries=retries,
            exception=str(exception),
            exception_file=exc_file,
            exception_line=exc_line,
            task_type='normal_task',
        )
    except Exception as e:
        loguru_logger.error(f'触发任务失败告警异常: {e}')
