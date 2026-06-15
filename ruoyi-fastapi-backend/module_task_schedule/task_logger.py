"""
任务执行明细日志抽象层

区分两层日志：
- 执行记录(task_instance)：任务每次执行的状态/起止时间/进度/结果，由 executor 维护。
- 任务执行明细日志(本模块)：runner 运行时的明细输出，按 task_uuid(执行实例ID)关联到
  task_instance，后端由 TaskLogConfig.task_log_type 控制：
    db   -> 写入 task_log 表(兼容 MySQL/PostgreSQL)，UI 可直接查看(默认)
    file -> 按 task_uuid 写入文件，UI 不开放查看任务执行日志
    es   -> 写入 Elasticsearch，适合大规模检索

所有后端的日志都会同时回显一份到 loguru(带 task_uuid)，保证控制台/系统日志可见。
"""

import os
import threading
from datetime import datetime
from typing import Any

from loguru import logger as loguru_logger

from config.env import TaskLogConfig
from module_task_schedule.sync_db import get_sync_session_local

# 批量后端(db/es)的默认批大小
_BATCH_SIZE = 50


def is_task_log_viewable() -> bool:
    """任务执行日志是否支持在 UI 直接查看(file 后端不支持)"""
    return TaskLogConfig.task_log_type != 'file'


# ---------------------------------------------------------------------------
# 各后端 writer
# ---------------------------------------------------------------------------
class BaseTaskLogWriter:
    """任务执行日志写入后端基类"""

    def write(self, task_uuid: str, level: str, message: str, log_time: datetime) -> None:
        raise NotImplementedError

    def flush(self) -> None:
        """刷盘(批量后端使用)"""

    def close(self) -> None:
        self.flush()


class DbTaskLogWriter(BaseTaskLogWriter):
    """数据库后端：批量写入 task_log 表(兼容 MySQL/PostgreSQL)"""

    def __init__(self, batch_size: int = _BATCH_SIZE) -> None:
        self._buffer: list[dict[str, Any]] = []
        self._batch_size = max(1, batch_size)
        self._lock = threading.Lock()

    def write(self, task_uuid: str, level: str, message: str, log_time: datetime) -> None:
        with self._lock:
            self._buffer.append(
                {
                    'task_uuid': task_uuid,
                    'level': level,
                    'content': message,
                    'create_time': log_time,
                }
            )
            need_flush = len(self._buffer) >= self._batch_size
        if need_flush:
            self.flush()

    def flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            rows = self._buffer
            self._buffer = []
        from module_task_schedule.entity.do.task_do import TaskLog

        session_local = get_sync_session_local()
        session = session_local()
        try:
            session.bulk_insert_mappings(TaskLog, rows)
            session.commit()
        except Exception as e:  # noqa: BLE001
            session.rollback()
            loguru_logger.error(f'任务执行日志写入数据库失败: {e}')
        finally:
            session.close()


class FileTaskLogWriter(BaseTaskLogWriter):
    """文件后端：按 task_uuid 写入 <dir>/<YYYY-MM-DD>/<task_uuid>.log"""

    def __init__(self, base_dir: str) -> None:
        self._base_dir = base_dir
        self._lock = threading.Lock()

    def write(self, task_uuid: str, level: str, message: str, log_time: datetime) -> None:
        day_dir = os.path.join(self._base_dir, log_time.strftime('%Y-%m-%d'))
        line = f'{log_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]} | {level:<8} | {message}\n'
        with self._lock:
            try:
                os.makedirs(day_dir, exist_ok=True)
                with open(os.path.join(day_dir, f'{task_uuid}.log'), 'a', encoding='utf-8') as f:
                    f.write(line)
            except Exception as e:  # noqa: BLE001
                loguru_logger.error(f'任务执行日志写入文件失败: {e}')


class EsTaskLogWriter(BaseTaskLogWriter):
    """Elasticsearch 后端：批量写入索引(按 task_uuid 查询)"""

    def __init__(self, hosts: str, index: str, user: str = '', password: str = '', batch_size: int = _BATCH_SIZE) -> None:
        self._index = index
        self._batch_size = max(1, batch_size)
        self._buffer: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        from elasticsearch import Elasticsearch  # 延迟导入，未启用 es 时无需安装依赖

        es_kwargs: dict[str, Any] = {'hosts': [h for h in hosts.split(',') if h]}
        if user:
            es_kwargs['http_auth'] = (user, password)
        self._client = Elasticsearch(**es_kwargs)

    def write(self, task_uuid: str, level: str, message: str, log_time: datetime) -> None:
        with self._lock:
            self._buffer.append(
                {
                    'task_uuid': task_uuid,
                    'level': level,
                    'content': message,
                    '@timestamp': log_time.isoformat(),
                }
            )
            need_flush = len(self._buffer) >= self._batch_size
        if need_flush:
            self.flush()

    def flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            rows = self._buffer
            self._buffer = []
        try:
            from elasticsearch import helpers

            actions = [{'_index': self._index, '_source': row} for row in rows]
            helpers.bulk(self._client, actions, stats_only=True)
        except Exception as e:  # noqa: BLE001
            loguru_logger.error(f'任务执行日志写入ES失败: {e}')


def _build_writer() -> BaseTaskLogWriter:
    """按配置构建日志后端 writer；构建失败时降级为 file 后端"""
    backend = TaskLogConfig.task_log_type
    if backend == 'db':
        return DbTaskLogWriter()
    if backend == 'es':
        try:
            return EsTaskLogWriter(
                hosts=TaskLogConfig.task_es_hosts,
                index=TaskLogConfig.task_es_index,
                user=TaskLogConfig.task_es_username,
                password=TaskLogConfig.task_es_password,
            )
        except Exception as e:  # noqa: BLE001
            loguru_logger.error(f'初始化ES日志后端失败,降级为文件后端: {e}')
            return FileTaskLogWriter(base_dir=TaskLogConfig.task_log_file_dir)
    return FileTaskLogWriter(base_dir=TaskLogConfig.task_log_file_dir)


# ---------------------------------------------------------------------------
# 对外的 TaskLogger
# ---------------------------------------------------------------------------
class TaskLogger:
    """
    任务执行日志记录器，runner 通过它输出日志。

    用法::

        logger = get_task_logger(task_uuid)
        try:
            logger.info('开始执行')
            ...
        finally:
            logger.close()   # 刷盘
    """

    def __init__(self, task_uuid: str, writer: BaseTaskLogWriter) -> None:
        self.task_uuid = task_uuid
        self._writer = writer
        self._bound = loguru_logger.bind(task_instance=task_uuid)

    def _log(self, level: str, message: Any, exc: bool = False) -> None:
        text = str(message)
        log_time = datetime.now()
        # 回显到 loguru(控制台/系统日志可见)
        try:
            self._bound.opt(exception=exc).log(level, f'[task:{self.task_uuid}] {text}')
        except Exception:  # noqa: BLE001
            pass
        # 写入执行日志后端
        if exc:
            import traceback

            text = f'{text}\n{traceback.format_exc()}'
        self._writer.write(self.task_uuid, level, text, log_time)

    def debug(self, message: Any) -> None:
        self._log('DEBUG', message)

    def info(self, message: Any) -> None:
        self._log('INFO', message)

    def warning(self, message: Any) -> None:
        self._log('WARNING', message)

    def error(self, message: Any) -> None:
        self._log('ERROR', message)

    def exception(self, message: Any) -> None:
        self._log('ERROR', message, exc=True)

    def flush(self) -> None:
        self._writer.flush()

    def close(self) -> None:
        self._writer.close()


def get_task_logger(task_uuid: str) -> TaskLogger:
    """
    构建任务执行日志记录器

    :param task_uuid: 执行实例ID(Celery任务UUID)
    :return: TaskLogger 实例
    """
    return TaskLogger(task_uuid, _build_writer())
