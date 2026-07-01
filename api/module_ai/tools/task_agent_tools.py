"""给 AI agent 的「任务提议」工具:把一份预填好的任务配置推给前端,由用户确认后再创建/运行。

设计要点:这些工具**不直接创建任务**,只把一份提议(task_proposal)append 到 `ui_actions`
收集器(同 SandboxCodeTools 的 artifacts 侧信道模式),由 `_stream_agent` 排空成
`{type:'ui_action', action:{...}}` 推给前端,前端渲染成可编辑表单卡片;用户在卡片上确认后
才走 `addTask`/`runTask`。即「AI 填表、人拍板」,AI 不擅自落库生产任务。

返回给 LLM 的是一句文本(已弹表单、等待用户确认),让 LLM 就此停手、勿再自行取数执行。
"""

from __future__ import annotations

import json
from typing import Any

from agno.tools import Toolkit

DEFAULT_TRANSFORM = 'def transform(row):\n    # row 为一条记录(dict),返回修改后的 dict\n    return row'

# 模板编码 → 中文标签(用于列出任务时可读展示)
_TPL_LABEL = {'DataIntegrationTask': '数据集成', 'PythonTask': 'Python 脚本', 'ShellTask': 'Shell 脚本'}


def _effective_tenant_id() -> Any:
    """当前请求的有效租户(拿不到则 None,不做租户过滤)。"""
    try:
        from common.context import RequestContext  # noqa: PLC0415

        return RequestContext.get_effective_tenant_id()
    except Exception:  # noqa: BLE001
        return None


def _search_tasks(keyword: str, limit: int) -> list[dict]:
    """按名称模糊搜索任务(agent 进程内,复用任务模块的同步会话),租户内、按更新时间倒序。"""
    from sqlalchemy import select  # noqa: PLC0415

    from module_task_schedule.entity.do.task_do import Task  # noqa: PLC0415
    from module_task_schedule.sync_db import get_sync_session_local  # noqa: PLC0415

    db = get_sync_session_local()()
    try:
        stmt = select(Task.id, Task.name, Task.template_code, Task.trigger_type,
                      Task.crontab, Task.status, Task.built_in)
        kw = (keyword or '').strip()
        if kw:
            stmt = stmt.where(Task.name.like(f'%{kw}%'))
        tid = _effective_tenant_id()
        if tid is not None:
            stmt = stmt.where(Task.tenant_id == tid)
        stmt = stmt.order_by(Task.update_time.desc()).limit(max(1, min(limit or 10, 50)))
        return [{'id': r[0], 'name': r[1], 'template_code': r[2], 'trigger_type': r[3],
                 'crontab': r[4], 'status': r[5], 'built_in': r[6]} for r in db.execute(stmt).all()]
    finally:
        db.close()


def _get_task(task_id: str) -> dict | None:
    """取单个任务的完整配置(用于修改前回填表单)。"""
    from sqlalchemy import select  # noqa: PLC0415

    from module_task_schedule.entity.do.task_do import Task  # noqa: PLC0415
    from module_task_schedule.sync_db import get_sync_session_local  # noqa: PLC0415

    db = get_sync_session_local()()
    try:
        stmt = select(Task.id, Task.name, Task.template_code, Task.params, Task.trigger_type,
                      Task.crontab, Task.status, Task.built_in)
        tid = _effective_tenant_id()
        if tid is not None:
            stmt = stmt.where(Task.tenant_id == tid)
        r = db.execute(stmt.where(Task.id == str(task_id))).first()
        if not r:
            return None
        try:
            params = json.loads(r[3]) if r[3] else {}
        except (ValueError, TypeError):
            params = {}
        return {'id': r[0], 'name': r[1], 'template_code': r[2], 'params': params,
                'trigger_type': r[4], 'crontab': r[5], 'status': r[6], 'built_in': r[7]}
    finally:
        db.close()


class TaskAgentTools(Toolkit):
    """任务提议工具集:把任务配置预填进对话表单,等用户确认(供数据 agent 调用)。"""

    def __init__(self, ui_actions: list | None = None, **kwargs: Any) -> None:
        # 任务提议收集器:工具产出时 append,_stream_agent 排空发给前端渲染成确认表单卡片。
        self.ui_actions: list = ui_actions if ui_actions is not None else []
        super().__init__(
            name='task_propose',
            tools=[self.propose_data_integration_task, self.propose_code_extract_task,
                   self.propose_python_task, self.propose_shell_task,
                   self.find_tasks, self.get_task_detail, self.propose_task_update, self.propose_task_copy],
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
        source_object: str = '',
        write_mode: str = 'append',
        target_format: str = 'csv',
        transform_code: str = '',
        schedule_cron: str = '',
    ) -> str:
        """提议一个数据集成(ETL)任务:从源数据源取数 → 写入目标数据源,弹出确认表单给用户。

        当用户要求「把 A 同步/导入/抽取到 B」「定时同步数据」「建个数据管道」等数据集成需求时使用。
        **务必先用 get_table_schema 摸清源的表/函数/字段及其原生查询写法**(尤其:akshare/ccxt 的查询是
        「函数名+参数」、Elasticsearch 是 DSL,都不是 SQL),再据此写 source_query。本工具只弹表单待用户确认。

        :param name: 任务名称(简短可读,如「订单同步到ES」)
        :param source_datasource_code: 源数据源编码
        :param source_query: 取数语句,**按源类型用其原生写法**(写前先 get_table_schema 查清):
            - SQL 源(mysql/pg/tdengine 等):只读 SELECT,如 `SELECT * FROM orders WHERE status='PAID'`
            - 接口源 akshare/ccxt:JSON `{"func":"函数名","params":{...}}`,
              如 `{"func":"stock_zh_a_daily","params":{"symbol":"sh600519","adjust":"qfq"}}`(无参则 params 写 {})
            - Elasticsearch:JSON `{"index":"索引名","body":{"query":{...},"size":50}}`(聚合用 body.aggs 且 size:0)
            - 其他非 SQL 源(Mongo/图/KV 等):用该源自身的查询语法/DSL(JSON 形式)
        :param target_datasource_code: 目标数据源编码
        :param target_table: 目标表名 / 索引 / 对象 key(文件源如 exports/orders.csv)
        :param source_object: 源端表名/索引/函数名(可选,用于表单预选与展示;SQL 源可留空,native 已含表名)
        :param write_mode: 写入模式 append 追加 / replace 覆盖 / merge 合并(默认 append)
        :param target_format: 目标为文件源时的格式 csv/json/jsonl(默认 csv)
        :param transform_code: 可选,逐行转换函数 def transform(row): ...(留空则不转换)
        :param schedule_cron: 可选,定时 cron 表达式(如 0 2 * * *);留空为单次任务
        :return: 操作结果文本(已弹表单,等待用户确认)
        """
        tcode = (transform_code or '').strip()
        src_obj = (source_object or '').strip()
        params = {
            'extract': {
                'datasource_code': source_datasource_code,
                'native': source_query,
                'object': src_obj,
                'tables': [src_obj] if src_obj else [],
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

    # ---------- 代码取数(爬虫/脚本化取数)ETL ----------
    def propose_code_extract_task(
        self, name: str, code: str, target_datasource_code: str, target_table: str,
        source_datasource_codes: str = '', write_mode: str = 'append',
        target_format: str = 'csv', schedule_cron: str = '',
    ) -> str:
        """提议一个「代码取数」数据集成任务:用 Python 代码取数(爬虫/分页/多步/自定义)→ 写入目标,弹确认表单。

        适合无法用一句原生查询表达的取数(分页爬取、多步抓取、自定义清洗),如「抓取某股票行情」这类脚本化取数。
        与 propose_data_integration_task 的区别:那个用一句 native 查询,这个用整段 Python 代码。
        典型配合:先 find_tasks + get_task_detail 看到某个现有代码取数任务的代码 → 改一改 → 调本工具新建。
        代码里可用:get_handler(code) 取某数据源 handler;emit(rows) 分批流式装载;或把结果赋给 result(list[dict]);
        print()/log() 即日志。本工具只弹表单待用户确认。

        :param name: 任务名称
        :param code: 取数 Python 代码(产出 result=list[dict],或用 emit(rows) 分批装载)
        :param target_datasource_code: 目标数据源编码
        :param target_table: 目标表/索引名
        :param source_datasource_codes: 代码中允许 get_handler 访问的数据源编码(逗号分隔,可空)
        :param write_mode: append 追加 / replace 覆盖 / merge 合并(默认 append)
        :param target_format: 目标为文件源时的格式(默认 csv)
        :param schedule_cron: 可选,定时 6 段 Quartz cron;留空为单次
        :return: 操作结果文本(已弹表单,等待用户确认)
        """
        codes = [c.strip() for c in (source_datasource_codes or '').split(',') if c.strip()]
        params = {
            'extract': {'mode': 'code', 'code': code, 'datasource_codes': codes},
            'transform': {'enabled': False, 'code': DEFAULT_TRANSFORM},
            'load': {'datasource_code': target_datasource_code, 'table': target_table,
                     'mode': write_mode or 'append', 'dataset': 'public', 'format': target_format or 'csv'},
        }
        return self._push('DataIntegrationTask', name, params, schedule_cron,
                          f'代码取数 → {target_datasource_code}.{target_table}')

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

    # ---------- 查已有任务 ----------
    def find_tasks(self, keyword: str = '', limit: int = 10) -> str:
        """按名称模糊查找已有任务,返回任务列表(含 task_id、模板、触发方式、定时、状态)。

        当用户想「改某个已有任务」——如调整定时频率、启用/停用、改名——但你还不知道其 task_id 时,
        先用本工具按关键词搜出目标任务,拿到 task_id 后再调用 propose_task_update 弹出修改表单。

        :param keyword: 任务名关键词(模糊匹配;留空则列最近更新的任务)
        :param limit: 最多返回条数(默认 10,上限 50)
        :return: 任务清单文本(每行含 task_id,供 propose_task_update 使用)
        """
        rows = _search_tasks(keyword, limit)
        if not rows:
            kw = (keyword or '').strip()
            return f'未找到名称含「{kw}」的任务。' if kw else '当前没有任务。'
        lines = [f'找到 {len(rows)} 个任务(用 propose_task_update(task_id=...) 修改):']
        for i, r in enumerate(rows, 1):
            tpl = _TPL_LABEL.get(r['template_code'], r['template_code'] or '?')
            sched = f'定时({r["crontab"]})' if (r['trigger_type'] == 2 and r['crontab']) else '单次'
            st = '启用' if r['status'] == 1 else '停用'
            tag = ' [内置]' if r['built_in'] == 1 else ''
            lines.append(f'{i}. [task_id={r["id"]}] {r["name"]} — {tpl} · {sched} · {st}{tag}')
        lines.append('查看某任务完整配置(代码/取数语句等)用 get_task_detail(task_id);改配置新建用对应 propose_* 工具。')
        return '\n'.join(lines)

    # ---------- 查任务完整配置(供据此修改后新建)----------
    def get_task_detail(self, task_id: str) -> str:
        """获取一个已有任务的**完整配置**(含代码/取数语句/装载目标等具体参数),供你查看或据此改动后新建。

        用于「基于某任务改一改再建一个」:先 find_tasks 拿 task_id → get_task_detail 看清它的代码/配置
        → 你按需修改 → 用 propose_code_extract_task / propose_python_task / propose_shell_task /
        propose_data_integration_task 新建。(与 propose_task_copy 区别:copy 原样复制不改;本工具让你看清内容以便改后再建。)

        :param task_id: 任务 id(来自 find_tasks)
        :return: 该任务的可读完整配置文本
        """
        task = _get_task(task_id)
        if not task:
            return f'未找到 task_id={task_id} 的任务,请先用 find_tasks 确认正确的 task_id。'
        p = task['params'] or {}
        tpl = task['template_code']
        sched = f'定时({task["crontab"]})' if (task['trigger_type'] == 2 and task['crontab']) else '单次'
        st = '启用' if task['status'] == 1 else '停用'
        lines = [f'任务「{task["name"]}」 task_id={task["id"]}  模板={_TPL_LABEL.get(tpl, tpl)}  触发={sched}  状态={st}']
        if tpl in ('PythonTask', 'ShellTask'):
            lines.append(f'运行方式={p.get("run_type", "code")}  运行参数={p.get("run_params") or "(无)"}')
            lines.append('【代码】\n' + (p.get('code') or ''))
        elif tpl == 'DataIntegrationTask':
            ex = p.get('extract') or {}
            tr = p.get('transform') or {}
            ld = p.get('load') or {}
            if (ex.get('mode') or '') == 'code':
                lines.append(f'抽取方式=代码取数  可用数据源={ex.get("datasource_codes") or []}')
                lines.append('【取数代码】\n' + (ex.get('code') or ''))
            else:
                lines.append(f'抽取: 源={ex.get("datasource_code")}  对象={ex.get("object") or ex.get("tables")}')
                lines.append('【取数语句 native】\n' + str(ex.get('native') or ''))
            if tr.get('enabled') and (tr.get('code') or '').strip():
                lines.append('【转换 transform】\n' + tr['code'])
            lines.append(f'装载: 目标={ld.get("datasource_code")}  表/索引={ld.get("table")}  '
                         f'模式={ld.get("mode")}  格式={ld.get("format") or "-"}')
        else:
            lines.append('【参数】\n' + json.dumps(p, ensure_ascii=False, indent=2))
        lines.append('如需据此新建:改好上面内容后调用对应 propose_* 工具(代码取数→propose_code_extract_task)。')
        return '\n'.join(lines)

    # ---------- 修改已有任务(弹编辑表单)----------
    def propose_task_update(
        self, task_id: str, name: str = '', schedule_cron: str = '',
        to_single_run: bool = False, status: str = '',
    ) -> str:
        """提议修改一个**已有任务**:载入其当前配置、应用你要改的项,弹出预填好的编辑表单给用户确认。

        典型场景:「把 XX 任务定时调成 20 分钟一次」「暂停 XX 任务」「给 XX 任务改个名」。
        本工具**不直接落库**,只弹表单(已带入该任务现有配置 + 你的改动),用户在表单上确认后才保存。
        若不知道 task_id,先用 find_tasks 搜出来。只需传要改的项,其余留空表示保持不变。

        :param task_id: 目标任务 id(来自 find_tasks)
        :param name: 新任务名(留空=不改名)
        :param schedule_cron: 新的定时 **6 段 Quartz cron**(秒 分 时 日 月 周),北京时区;
            **星期只用数字**(周日=1..周六=7,周一到周五=2-6,别用名称/0);定了星期则"日"写 ?。
            例:每 20 分钟 `0 */20 * * * ?`;每天 8 点 `0 0 8 * * ?`;交易时段每 5 分钟 `0 */5 9-15 ? * 2-6`。留空=不改定时。
        :param to_single_run: 置 True 表示改为「单次」任务(取消定时);与 schedule_cron 互斥
        :param status: 'enable' 启用 / 'disable' 停用 / 留空=不改状态
        :return: 操作结果文本(已弹修改表单,等待用户确认)
        """
        task = _get_task(task_id)
        if not task:
            return f'未找到 task_id={task_id} 的任务,请先用 find_tasks 确认正确的 task_id。'

        cron = (schedule_cron or '').strip()
        changes: list[str] = []
        new_name = (name or '').strip() or task['name']
        if name and name.strip() != task['name']:
            changes.append(f'改名为「{new_name}」')

        # 触发方式/定时
        trigger_type = task['trigger_type'] or 1
        crontab = task['crontab'] or ''
        if to_single_run:
            trigger_type, crontab = 1, ''
            changes.append('改为单次运行(取消定时)')
        elif cron:
            trigger_type, crontab = 2, cron
            changes.append(f'定时调整为 {cron}')

        # 状态
        new_status = task['status']
        if status.lower() in ('enable', 'on', '1', '启用'):
            new_status = 1
            changes.append('启用')
        elif status.lower() in ('disable', 'off', '0', '停用'):
            new_status = 0
            changes.append('停用')

        self.ui_actions.append({
            'kind': 'task_update_proposal',
            'task_id': task['id'],
            'template_code': task['template_code'],
            'name': new_name,
            'trigger_type': trigger_type,
            'crontab': crontab,
            'status': new_status,
            'params': task['params'],
            'summary': ';'.join(changes) if changes else '打开编辑表单',
        })
        chg = ';'.join(changes) if changes else '未指定改动(可在表单里手动调整)'
        return (f'已向用户弹出「{new_name}」的任务修改确认表单({chg}),'
                f'等待用户在表单上确认保存。请不要再自行改动该任务。')

    # ---------- 复制已有任务(弹新建表单)----------
    def propose_task_copy(
        self, task_id: str, new_name: str = '', schedule_cron: str = '', to_single_run: bool = False,
    ) -> str:
        """复制一个**已有任务**:载入其完整配置作为**新任务**的初值,弹出预填好的新建确认表单。

        典型场景:「照 XX 任务复制一个」「基于 XX 任务再建一个,改成每天跑」。
        与 propose_task_update 的区别:这是**新建**(用户确认后 addTask,生成新任务、不动原任务);
        propose_task_update 是原地改同一个任务。若不知道 task_id,先用 find_tasks 搜出来。

        :param task_id: 被复制的源任务 id(来自 find_tasks)
        :param new_name: 新任务名(留空则用「原名_副本」)
        :param schedule_cron: 新任务的定时 6 段 Quartz cron(留空=沿用源任务的定时;每20分钟 `0 */20 * * * ?`)
        :param to_single_run: 置 True 表示新任务为「单次」(忽略源任务的定时);与 schedule_cron 互斥
        :return: 操作结果文本(已弹新建表单,等待用户确认创建)
        """
        task = _get_task(task_id)
        if not task:
            return f'未找到 task_id={task_id} 的任务,请先用 find_tasks 确认正确的 task_id。'
        # 定时:默认沿用源任务;to_single_run 取消定时;或用传入 cron 覆盖
        if to_single_run:
            eff_cron = ''
        elif (schedule_cron or '').strip():
            eff_cron = schedule_cron.strip()
        else:
            eff_cron = task['crontab'] if (task['trigger_type'] == 2) else ''
        name = (new_name or '').strip() or f'{task["name"]}_副本'
        # 复用 _push:产出 kind=task_proposal 的「新建」提议(不带 task_id)→ 前端走 addTask 生成新任务
        return self._push(task['template_code'], name, task['params'], eff_cron, f'复制自「{task["name"]}」')
