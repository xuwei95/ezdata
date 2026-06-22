"""调试层沙箱客户端:把「已抽取的数据行 + 转换代码」发给沙箱服务执行。

只在 ETL 调试(预览)用;生产 ETL 任务直跑,不经此处。
worker 侧绝不把任何连接凭据发进沙箱——只发数据行与代码。
"""

from __future__ import annotations

from typing import Any

import requests

from config.env import SandboxConfig


def enabled() -> bool:
    return bool(SandboxConfig.sandbox_enabled)


def transform_rows(code: str, rows: list[dict], timeout: int | None = None) -> dict[str, Any]:
    """调用沙箱执行逐行 transform(row)。返回 {success, transformed, output, error}。

    网络/服务异常向上抛(由调用方决定是否兜底),业务错误(代码错/超时)在返回体里。
    """
    t = int(timeout or SandboxConfig.sandbox_timeout)
    url = SandboxConfig.sandbox_api_url.rstrip('/') + '/transform'
    resp = requests.post(
        url,
        json={'code': code, 'rows': rows, 'timeout': t},
        headers={'Authorization': f'Bearer {SandboxConfig.sandbox_bearer_key}', 'Content-Type': 'application/json'},
        timeout=t + 10,
    )
    resp.raise_for_status()
    return resp.json()
