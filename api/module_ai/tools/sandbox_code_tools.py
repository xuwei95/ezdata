"""给 AI agent 的代码执行工具:在隔离沙箱里跑 Python(计算 / 数据源取数)。

基于 ezdata 沙箱(无持久凭据、子进程隔离、可超时 kill),替代 agno 自带 PythonTools 的本地 exec。
两个工具:
- run_python_code:跑普通 Python 做计算/数据处理
- run_datasource_query:对指定数据源跑取数代码(沙箱注入 handler)

数据源连接由本工具在 agent 进程内同步查库+解密后,以明文随请求注入沙箱(沙箱本身 env 为空)。
"""

from __future__ import annotations

import json
from typing import Any

from agno.tools import Toolkit


class SandboxCodeTools(Toolkit):
    """沙箱代码执行工具集(供 agent 调用)。"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(name='sandbox_code',
                         tools=[self.run_python_code, self.run_datasource_query], **kwargs)

    def run_python_code(self, code: str, variable_to_return: str | None = None) -> str:
        """运行 Python 代码做计算或数据处理,返回结果。

        可用库:math、json、datetime、re、statistics、pandas、numpy 等;禁止文件/网络/系统访问。
        把结果赋值给一个变量并通过 variable_to_return 指定要返回的变量名,或直接 print 输出。

        :param code: 要执行的 Python 代码
        :param variable_to_return: 要返回其值的变量名(可选)
        :return: 执行结果(变量值 / 标准输出 / 错误信息)
        """
        from module_data import sandbox_client

        try:
            res = sandbox_client.run_python(code, variable_to_return)
        except Exception as e:  # noqa: BLE001
            return f'调用沙箱失败: {e}'
        return _format_result(res)

    def run_datasource_query(self, datasource_code: str, code: str,
                             variable_to_return: str = 'result') -> str:
        """对指定数据源运行取数代码,返回查询结果。

        code 中可直接使用预置的 `handler` 对象访问数据源,例如:
            result = handler.query("SELECT * FROM users LIMIT 10")
        把取到的数据赋值给变量(默认 result),通过 variable_to_return 指定要返回的变量名。

        :param datasource_code: 数据源编码(平台已配置的数据源)
        :param code: 取数 Python 代码,内部可用 handler 对象
        :param variable_to_return: 要返回其值的变量名(默认 result)
        :return: 查询结果 / 错误信息
        """
        from module_data import sandbox_client

        try:
            datasource = _resolve_datasource(datasource_code)
        except Exception as e:  # noqa: BLE001
            return f'数据源解析失败: {e}'
        try:
            res = sandbox_client.run_python_data(code, datasource, variable_to_return)
        except Exception as e:  # noqa: BLE001
            return f'调用沙箱失败: {e}'
        return _format_result(res)


def _resolve_datasource(code: str) -> dict:
    """同步查数据源 + 解密 secrets 为明文 dict(沙箱无凭据,连接随请求注入)。"""
    from module_task_schedule.runners.data_integration_runner import _load_datasource
    from utils.crypto_util import CryptoUtil

    rec = _load_datasource(code)  # {source_type, config, secrets(AES 密文)}
    secrets: dict = {}
    if rec.get('secrets'):
        try:
            secrets = json.loads(CryptoUtil.decrypt(rec['secrets']))
        except Exception:  # noqa: BLE001 解密失败按空密钥,由 handler 报连接错误
            secrets = {}
    return {'source_type': rec['source_type'], 'config': rec.get('config') or {}, 'secrets': secrets}


def _format_result(res: dict) -> str:
    """把沙箱响应拼成给 LLM 的文本。"""
    if not res.get('success'):
        return f'执行失败: {res.get("error") or "未知错误"}'
    parts: list[str] = []
    if res.get('result') is not None:
        parts.append(f'结果: {json.dumps(res["result"], ensure_ascii=False, default=str)}')
    if (res.get('stdout') or '').strip():
        parts.append(f'输出:\n{res["stdout"].rstrip()}')
    return '\n'.join(parts) if parts else '执行成功(无返回值/输出)'
