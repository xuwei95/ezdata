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


_ROW_CAP = 500  # 表格产物最多回传行数(避免大表撑爆传输;LLM 文本摘要已含总数)


class SandboxCodeTools(Toolkit):
    """沙箱代码执行工具集(供 agent 调用)。"""

    def __init__(self, artifacts: list | None = None, allowed_codes: list | None = None, **kwargs: Any) -> None:
        # 结构化产物收集器(图表/表格):工具产出时 append,_stream_agent 排空发给前端渲染。
        # 给 LLM 的返回值仍是文本摘要,不污染上下文。
        self.artifacts: list = artifacts if artifacts is not None else []
        # allowed_codes 非空时,取数仅限这些数据源(应用「数据分析」选定的源);None=不限。
        self.allowed_codes = set(allowed_codes) if allowed_codes else None
        super().__init__(name='sandbox_code',
                         tools=[self.run_python_code, self.run_datasource_query], **kwargs)

    def _collect(self, res: dict) -> None:
        """把沙箱结果里的 html/dataframe 归一成前端可渲染的产物,append 到收集器。"""
        if not (res and res.get('success')):
            return
        result = res.get('result')
        if not (isinstance(result, dict) and 'type' in result and 'value' in result):
            return
        t, val = result['type'], result['value']
        if t == 'html':
            self.artifacts.append({'kind': 'chart', 'html': str(val)})
        elif t == 'dataframe':
            rows = val if isinstance(val, list) else []
            self.artifacts.append({'kind': 'table', 'rows': rows[:_ROW_CAP], 'total': len(rows)})

    def run_python_code(self, code: str, variable_to_return: str | None = None) -> str:
        """运行 Python 代码做计算或数据处理,返回结果。

        可用库:math、json、datetime、re、statistics、pandas、numpy、pyecharts 等;禁止文件/网络/系统访问。
        把结果赋值给变量并用 variable_to_return 指定返回,或直接 print。结果可加工成结构化格式——
        把变量赋为 {type, value} 字典:
          - {'type':'string','value':'结论文本'}              文本结论
          - {'type':'dataframe','value': df}                   表格(df 为 pandas DataFrame,自动转换)
          - {'type':'html','value': chart.render_embed()}      图表(用 pyecharts 绘图)
        也可直接返回数字/字符串/列表。

        :param code: 要执行的 Python 代码
        :param variable_to_return: 要返回其值的变量名(可选)
        :return: 执行结果摘要(结论 / 表格预览 / 图表提示 / 标准输出)
        """
        from module_data import sandbox_client

        try:
            res = sandbox_client.run_python(code, variable_to_return)
        except Exception as e:  # noqa: BLE001
            return f'调用沙箱失败: {e}'
        self._collect(res)
        return _format_result(res)

    def run_datasource_query(self, datasource_code: str, code: str,
                             variable_to_return: str = 'result') -> str:
        """对指定数据源运行取数代码,可对数据加工后返回结论 / 表格 / 图表。

        code 中可直接使用预置的 `handler` 对象访问数据源:
            - SQL 源(mysql/pg…):rows = handler.query("SELECT * FROM users LIMIT 10")
            - 非 SQL 源:statement 形态随源而定,**不是 SQL**。如 akshare 财经接口:
              rows = handler.query("stock_hk_spot_em", {})   # 函数名 + 参数 dict,返回 list[dict](带重试)
              先用 get_table_schema 查该源的函数名/参数,再调;勿对 akshare 写 SQL。
        把结果赋值给 result(或用 variable_to_return 指定),可加工成 {type, value}:
          - {'type':'string','value':'共 100 个用户'}                 文本结论
          - {'type':'dataframe','value': pd.DataFrame(rows)}          表格(自动转换)
          - {'type':'html','value': chart.render_embed()}             图表(用 pyecharts 绘图)
        也可直接返回 list/数字/字符串。可用 pandas、numpy、pyecharts 等做加工。

        :param datasource_code: 数据源编码(平台已配置的数据源)
        :param code: 取数 Python 代码,内部可用 handler 对象
        :param variable_to_return: 要返回其值的变量名(默认 result)
        :return: 结果摘要(结论 / 表格预览 / 图表提示)
        """
        from module_data import sandbox_client

        if self.allowed_codes is not None and datasource_code not in self.allowed_codes:
            return f'该应用未授权访问数据源: {datasource_code}(仅可用: {", ".join(self.allowed_codes)})'
        try:
            datasource = _resolve_datasource(datasource_code)
        except Exception as e:  # noqa: BLE001
            return f'数据源解析失败: {e}'
        try:
            res = sandbox_client.run_python_data(code, datasource, variable_to_return)
        except Exception as e:  # noqa: BLE001
            return f'调用沙箱失败: {e}'
        self._collect(res)
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


def _preview(v: Any, limit: int = 500) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
    return s[:limit] + '…' if len(s) > limit else s


def _summarize(result: Any) -> str:
    """把结果摘要成给 LLM 的文本:html/大表不全量回传,避免污染上下文。"""
    if result is None:
        return ''
    if isinstance(result, dict) and 'type' in result and 'value' in result:
        t, val = result['type'], result['value']
        if t == 'html':
            return f'已生成图表(html,{len(str(val))} 字符),将展示给用户。'
        if t == 'dataframe':
            rows = val if isinstance(val, list) else []
            return f'数据表格 {len(rows)} 行。前 3 行预览:\n{_preview(rows[:3])}'
        if t == 'string':
            return f'结论: {val}'
        return f'结果({t}): {_preview(val)}'
    return f'结果: {_preview(result)}'


def _format_result(res: dict) -> str:
    """把沙箱响应拼成给 LLM 的文本(按结果类型摘要)。"""
    if not res.get('success'):
        return f'执行失败: {res.get("error") or "未知错误"}'
    parts: list[str] = [_summarize(res.get('result'))]
    if (res.get('stdout') or '').strip():
        parts.append(f'输出:\n{res["stdout"].rstrip()}')
    return '\n'.join(p for p in parts if p) or '执行成功(无返回值/输出)'
