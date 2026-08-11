"""数据访问审计:异步批量写入器 + audit() 上下文管理器。

设计对齐 module_task_schedule/task_logger.py 的批缓冲:入队走内存(请求线程,零阻塞),
后台守护线程按批大小/间隔刷盘。上下文(user/tenant/trace)在请求线程 __enter__ 时捕获,
因为刷盘线程无请求 contextvar。MVP 落 MySQL(data_access_log);预留 es 后端开关。

用法(service 层):
    with audit(access_type='query', datasource_code=code, object_name=table,
               statement=native, filters=None, source='web', model_id=m.id,
               source_type=ds.source_type) as a:
        rows = await run_in_threadpool(handler.query, native, None, limit)
        a.rows = len(rows)
    return rows
异常自动记为 success=0 + error_msg,并向上抛(不吞)。
"""

import os
import threading
import time
from datetime import datetime
from typing import Any

from loguru import logger as loguru_logger

_ENABLED = os.environ.get('DATA_ACCESS_AUDIT', '1') not in ('0', 'false', 'False')
_BATCH_SIZE = 50
_FLUSH_INTERVAL = 2.0
_STMT_CAP = 8000  # 语句截断上限(超长 SQL/DSL)


class _AuditWriter:
    """内存缓冲 + 后台守护线程刷盘(bulk_insert_mappings 到 data_access_log)。"""

    def __init__(self) -> None:
        self._buffer: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._started = False

    def _ensure_started(self) -> None:
        if self._started:
            return
        with self._lock:
            if self._started:
                return
            t = threading.Thread(target=self._loop, name='data-access-audit', daemon=True)
            t.start()
            self._started = True

    def enqueue(self, row: dict[str, Any]) -> None:
        self._ensure_started()
        with self._lock:
            self._buffer.append(row)
            over = len(self._buffer) >= _BATCH_SIZE
        if over:
            self.flush()

    def _loop(self) -> None:
        while True:
            time.sleep(_FLUSH_INTERVAL)
            try:
                self.flush()
            except Exception as e:  # 守护线程绝不退出
                loguru_logger.error(f'数据访问审计刷盘异常: {e}')

    def flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            rows = self._buffer
            self._buffer = []
        from module_data.entity.do.data_access_log_do import DataAccessLog
        from module_task_schedule.sync_db import get_sync_session_local

        session = get_sync_session_local()()
        try:
            session.bulk_insert_mappings(DataAccessLog, rows)
            session.commit()
        except Exception as e:
            session.rollback()
            loguru_logger.error(f'数据访问审计写入失败({len(rows)} 条): {e}')
        finally:
            session.close()


_writer = _AuditWriter()


def _capture_context() -> dict[str, Any]:
    """在请求线程读取 user/tenant/trace(刷盘线程无这些 contextvar)。"""
    ctx: dict[str, Any] = {'tenant_id': None, 'user_id': None, 'user_name': None, 'trace_id': None, 'request_path': None}
    try:
        from common.context import RequestContext

        ctx['tenant_id'] = RequestContext.get_effective_tenant_id()
        cu = RequestContext.get_current_user()
        if cu and getattr(cu, 'user', None):
            ctx['user_id'] = getattr(cu.user, 'user_id', None)
            ctx['user_name'] = getattr(cu.user, 'user_name', None)
    except Exception:
        pass
    try:
        from middlewares.trace_middleware.ctx import TraceCtx

        ctx['trace_id'] = TraceCtx.get_trace_id() or None
        ctx['request_path'] = TraceCtx.get_request_path() or None
    except Exception:
        pass
    return ctx


class audit:  # noqa: N801 - 作上下文管理器用,小写更贴近 with 语义
    """数据访问审计上下文管理器:进入记时+捕获上下文,退出补行数/成败并入队。"""

    def __init__(
        self,
        *,
        access_type: str,
        datasource_code: str | None = None,
        object_name: str | None = None,
        statement: Any = None,
        filters: Any = None,
        source: str = 'web',
        model_id: str | None = None,
        source_type: str | None = None,
    ) -> None:
        self.rows: int | None = None  # 调用方在 with 体内设置返回行数
        self._enabled = _ENABLED
        self._t0 = 0.0
        self._rec = {
            'access_type': access_type,
            'datasource_code': datasource_code,
            'object_name': object_name,
            'statement': (str(statement)[:_STMT_CAP] if statement is not None else None),
            'filters': filters if isinstance(filters, (list, dict)) else None,
            'source': source,
            'model_id': model_id,
            'source_type': source_type,
        }

    def __enter__(self) -> 'audit':
        if self._enabled:
            self._t0 = time.monotonic()
            self._rec.update(_capture_context())
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        if not self._enabled:
            return False  # 不吞异常
        try:
            self._rec['exec_ms'] = int((time.monotonic() - self._t0) * 1000)
            self._rec['result_rows'] = self.rows
            self._rec['success'] = 0 if exc_type is not None else 1
            self._rec['error_msg'] = (str(exc)[:1000] if exc is not None else None)
            self._rec['access_time'] = datetime.now()
            _writer.enqueue(dict(self._rec))
        except Exception as e:
            loguru_logger.error(f'数据访问审计入队失败: {e}')
        return False  # 永不吞异常


def flush_audit() -> None:
    """强制刷盘(供 lifespan shutdown / 测试用)。"""
    _writer.flush()
