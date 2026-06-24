"""给 AI agent 的「任务提议」工具:把一份预填好的任务配置推给前端,由用户确认后再创建/运行。

设计要点:这些工具**不直接创建任务**,只把一份提议(task_proposal)append 到 `ui_actions`
收集器(同 SandboxCodeTools 的 artifacts 侧信道模式),由 `_stream_agent` 排空成
`{type:'ui_action', action:{...}}` 推给前端,前端渲染成可编辑表单卡片;用户在卡片上确认后
才走 `addTask`/`runTask`。即「AI 填表、人拍板」,AI 不擅自落库生产任务。

返回给 LLM 的是一句文本(已弹表单、等待用户确认),让 LLM 就此停手、勿再自行取数执行。
"""

from __future__ import annotations

from typing import Any

from agno.tools import Toolkit

DEFAULT_TRANSFORM = 'def transform(row):\n    # row 为一条记录(dict),返回修改后的 dict\n    return row'


class TaskAgentTools(Toolkit):
    """任务提议工具集:把任务配置预填进对话表单,等用户确认(供数据 agent 调用)。"""

    def __init__(self, ui_actions: list | None = None, **kwargs: Any) -> None:
        # 任务提议收集器:工具产出时 append,_stream_agent 排空发给前端渲染成确认表单卡片。
        self.ui_actions: list = ui_actions if ui_actions is not None else []
        super().__init__(
            name='task_propose',
            tools=[self.propose_data_integration_task, self.propose_python_task, self.propose_shell_task],
            **kwargs,
        )

    # ---------- 内部:推一条提议 ----------
    def _push(self, template_code: str, name: str, params: dict, schedule_cron: str, summary: str) -> str:
        cron = (schedule_cron or '').strip()
        self.ui_actions.append({
            'kind': 'task_proposal',
            'template_code': template_code,
            'name': name or '未命名任务',
            'trigger_type': 2 if cron else 1,  # 1 单次 / 2 定时
            'crontab': cron,
            'params': params,
            'summary': summary,
        })
        sched = f'定时(cron: {cron})' if cron else '单次'
        return (f'已向用户弹出「{name}」的任务确认表单({template_code},{sched}),'
                f'等待用户在表单上确认并创建/运行。请不要再自行执行该任务,交给用户确认即可。')

    # ---------- 数据集成(ETL)----------
    def propose_data_integration_task(
        self,
        name: str,
        source_datasource_code: str,
        source_query: str,
        target_datasource_code: str,
        target_table: str,
        write_mode: str = 'append',
        target_format: str = 'csv',
        transform_code: str = '',
        schedule_cron: str = '',
    ) -> str:
        """提议一个数据集成(ETL)任务:从源数据源取数 → 写入目标数据源,弹出确认表单给用户。

        当用户要求「把 A 同步/导入/抽取到 B」「定时同步数据」「建个数据管道」等数据集成需求时使用。
        先用 list_datasources / get_table_schema 摸清源与目标的数据源编码、表名、字段,再调本工具。
        本工具不会创建任务,只是把预填好的配置弹给用户确认。

        :param name: 任务名称(简短可读,如「订单同步到ES」)
        :param source_datasource_code: 源数据源编码
        :param source_query: 取数语句。SQL 源写 SQL(如 SELECT * FROM orders);非 SQL 源按其规则
        :param target_datasource_code: 目标数据源编码
        :param target_table: 目标表名 / 对象 key(文件源如 exports/orders.csv)
        :param write_mode: 写入模式 append 追加 / replace 覆盖 / merge 合并(默认 append)
        :param target_format: 目标为文件源时的格式 csv/json/jsonl(默认 csv)
        :param transform_code: 可选,逐行转换函数 def transform(row): ...(留空则不转换)
        :param schedule_cron: 可选,定时 cron 表达式(如 0 2 * * *);留空为单次任务
        :return: 操作结果文本(已弹表单,等待用户确认)
        """
        tcode = (transform_code or '').strip()
        params = {
            'extract': {
                'datasource_code': source_datasource_code,
                'native': source_query,
                'object': target_table,
            },
            'transform': {'enabled': bool(tcode), 'code': tcode or DEFAULT_TRANSFORM},
            'load': {
                'datasource_code': target_datasource_code,
                'table': target_table,
                'mode': write_mode or 'append',
                'dataset': 'public',
                'format': target_format or 'csv',
            },
        }
        summary = f'{source_datasource_code} → {target_datasource_code}.{target_table}（{write_mode}）'
        return self._push('DataIntegrationTask', name, params, schedule_cron, summary)

    # ---------- Python 脚本 ----------
    def propose_python_task(self, name: str, code: str, run_params: str = '', schedule_cron: str = '') -> str:
        """提议一个 Python 脚本任务,弹出确认表单给用户。

        当用户要求「写个 Python 任务/脚本定时跑」「用 Python 处理/计算并落地」等需求时使用。
        代码须定义 run(params, logger) 函数,返回值即任务结果。本工具不会创建任务,只弹给用户确认。

        :param name: 任务名称
        :param code: Python 代码,须包含 def run(params, logger): ... 入口
        :param run_params: 可选,运行参数(JSON 字符串)
        :param schedule_cron: 可选,定时 cron 表达式;留空为单次任务
        :return: 操作结果文本(已弹表单,等待用户确认)
        """
        params = {'run_type': 'code', 'code': code, 'file': '', 'run_params': run_params or ''}
        return self._push('PythonTask', name, params, schedule_cron, 'Python 脚本任务')

    # ---------- Shell 脚本 ----------
    def propose_shell_task(self, name: str, command: str, run_params: str = '', schedule_cron: str = '') -> str:
        """提议一个 Shell 脚本任务,弹出确认表单给用户。

        当用户要求「跑个 shell 命令/脚本」「定时执行某命令」等需求时使用。
        本工具不会创建任务,只弹给用户确认。

        :param name: 任务名称
        :param command: Shell 脚本内容
        :param run_params: 可选,运行参数(JSON 字符串)
        :param schedule_cron: 可选,定时 cron 表达式;留空为单次任务
        :return: 操作结果文本(已弹表单,等待用户确认)
        """
        params = {'run_type': 'code', 'code': command, 'file': '', 'run_params': run_params or ''}
        return self._push('ShellTask', name, params, schedule_cron, 'Shell 脚本任务')
