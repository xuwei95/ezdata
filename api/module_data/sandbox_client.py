"""调试层沙箱客户端:把「任务描述 + 上下文」发给独立沙箱服务执行。

无状态全注入模型:沙箱进程 env 为空、不持凭据;执行所需的一切(代码、数据源明文连接、
日志库连接)都由本客户端随请求传入。SANDBOX_ENABLED 关闭时调用方应回落本地真实跑(不经此处)。

- transform_rows:逐行 transform(row)(ETL 预览,worker 先抽好数据行,只发行+代码)
- execute_task:通用任务执行(沙箱即远程 executor,按 template_code/runner_type 复用平台 runner)
"""

from __future__ import annotations

from typing import Any

import requests

from config.env import SandboxConfig


def enabled() -> bool:
    return bool(SandboxConfig.sandbox_enabled)


def build_logger_config(task_uuid: str | None) -> dict | None:
    """按任务日志后端构造 logger_config:db/es 注入连接参数(沙箱直写),file/缺省回传。

    沙箱 env 为空,故连接参数必须在此组装后随请求传入。
    """
    if not task_uuid:
        return None
    from config.env import TaskLogConfig  # noqa: PLC0415

    typ = TaskLogConfig.task_log_type
    cfg: dict[str, Any] = {'type': typ, 'task_uuid': task_uuid}
    if typ == 'db':
        from config.database import build_sync_sqlalchemy_database_url  # noqa: PLC0415

        cfg['db_url'] = build_sync_sqlalchemy_database_url()
    elif typ == 'es':
        cfg.update(hosts=TaskLogConfig.task_es_hosts, index=TaskLogConfig.task_es_index,
                   user=TaskLogConfig.task_es_username, password=TaskLogConfig.task_es_password)
    return cfg


def _post(path: str, body: dict, timeout: int) -> dict[str, Any]:
    url = SandboxConfig.sandbox_api_url.rstrip('/') + path
    resp = requests.post(
        url, json=body,
        headers={'Authorization': f'Bearer {SandboxConfig.sandbox_bearer_key}', 'Content-Type': 'application/json'},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def transform_rows(code: str, rows: list[dict], timeout: int | None = None) -> dict[str, Any]:
    """逐行 transform(row)。返回 {success, transformed, output, error}。"""
    t = int(timeout or SandboxConfig.sandbox_timeout)
    return _post('/transform', {'code': code, 'rows': rows, 'timeout': t}, t + 10)


def execute_task(template_code: str, params: dict, runner_type: int = 1, runner_code: str | None = None,
                 datasources: dict | None = None, task_uuid: str | None = None,
                 timeout: int | None = None) -> dict[str, Any]:
    """通用任务执行(沙箱即远程 executor)。返回 {success, result, output, logs, error}。

    datasources={code:{source_type, config, secrets(明文 dict)}} 仅 ETL 用,由调用方预解密。
    """
    t = int(timeout or SandboxConfig.sandbox_timeout)
    body = {
        'template_code': template_code, 'runner_type': runner_type, 'runner_code': runner_code,
        'params': params or {}, 'datasources': datasources or {},
        'logger_config': build_logger_config(task_uuid), 'timeout': t,
    }
    return _post('/task/execute', body, t + 50)
