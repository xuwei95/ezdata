from __future__ import annotations

from http import HTTPStatus


class TaskException(Exception):
    """
    任务执行异常
    """
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
