"""
任务模块共享的同步数据库会话

Celery worker 是同步上下文，统一复用项目已有的同步引擎
(config.database.create_sync_db_engine)。引擎懒加载，并提供 reset 供
celery worker_process_init 在 prefork 之后重建，避免子进程复用父进程连接。
"""

import threading

_engine = None
_session_local = None
_lock = threading.Lock()


def get_sync_session_local():
    """懒加载获取任务模块专用的同步 Session 工厂"""
    global _engine, _session_local
    if _session_local is None:
        with _lock:
            if _session_local is None:
                from config.database import create_sync_db_engine, create_sync_session_local

                _engine = create_sync_db_engine(echo=False)
                _session_local = create_sync_session_local(_engine)
    return _session_local


def reset_sync_engine() -> None:
    """重置同步引擎(供 celery worker_process_init 在 fork 后调用)"""
    global _engine, _session_local
    with _lock:
        if _engine is not None:
            try:
                _engine.dispose()
            except Exception:
                pass
        _engine = None
        _session_local = None
