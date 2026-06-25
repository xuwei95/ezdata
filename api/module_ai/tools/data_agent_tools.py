"""数据探索工具:查数据源原始表结构(实时、准确),并用数据模型里的业务描述把它"讲明白"。

设计取舍:结构(表、字段、类型、字段注释)一律以**实时 introspect** 为准——数据模型缓存的字段可能过时、失真;
只把数据模型里**人工写的表级业务描述**(业务名、表说明 remark)叠加到实时表列表上,帮 LLM 认出表的业务含义。
"""

from __future__ import annotations

from typing import Any

from agno.tools import Toolkit


class DataAgentTools(Toolkit):
    """数据探索工具集(供数据 agent 调用)。"""

    def __init__(self, allowed_codes: list | None = None, **kwargs: Any) -> None:
        # allowed_codes 非空时,数据探索仅限这些数据源(应用「数据分析」选定的源);None=不限。
        self.allowed_codes = set(allowed_codes) if allowed_codes else None
        super().__init__(
            name='data_explore',
            tools=[self.list_datasources, self.get_table_schema, self.search_datasource_knowledge],
            **kwargs,
        )

    def list_datasources(self, codes: str = '') -> str:
        """列出数据源,并**直接带出每个源的所有表名**(已建数据模型的表标上业务名/描述)。

        一次就能看到"哪些数据源、各有哪些表、哪些是什么业务",据此直接认出目标表,
        无需再调一次工具列表名。已建模的表逐行详列(业务名+描述);未建模的表名紧凑列出(仍可搜到)。
        数据源多时传 codes(逗号分隔)只看指定的几个。

        :param codes: 可选,逗号分隔的数据源编码;为空返回全部
        :return: 数据源及其表清单(表名后「— 业务名: 描述」来自数据模型)
        """
        code_list = [c.strip() for c in codes.split(',') if c.strip()] or None
        if self.allowed_codes is not None:  # 限定数据源范围:只在授权的源里探索
            code_list = (list(self.allowed_codes) if not code_list
                         else [c for c in code_list if c in self.allowed_codes])
        rows = _list_datasources(code_list)
        if not rows:
            return '未找到数据源。'
        blocks: list[str] = []
        for r in rows:
            header = f"【{r['code']}】{r['name'] or ''} ({r['source_type'] or ''})"
            try:
                names = _build_handler(r['code']).list_tables()
            except Exception:  # noqa: BLE001 不支持 schema / 连不上的源,跳过表名
                blocks.append(header + '  (表列表暂不可用)')
                continue
            if not names:
                blocks.append(header + '  (无表)')
                continue
            models = _models_of_source(r['code'])
            modeled = [t for t in names if t in models]
            unmodeled = [t for t in names if t not in models]
            parts = [f'{header} 共 {len(names)} 张表:']
            # 已建模的表:逐行详列(业务名+描述,这些是业务相关、最常用的)
            for t in modeled:
                m = models[t]
                parts.append(f"  - {t} — {m['name']}{(': ' + m['remark']) if m.get('remark') else ''}")
            # 未建模的表(多为系统/中间表):表名紧凑列成一行,仍全在可搜,但不逐行占空间
            if unmodeled:
                label = '  其余未建模表' if modeled else '  表(均未建模)'
                parts.append(f'{label}({len(unmodeled)}): ' + ', '.join(unmodeled))
            blocks.append('\n'.join(parts))
        return ('数据源及其表(表名后「— 业务名: 描述」是已建模的):\n\n' + '\n\n'.join(blocks)
                + '\n\n认出目标表后:get_table_schema(数据源编码, tables="表名") 查字段 → run_datasource_query 取数。')

    def get_table_schema(self, datasource_code: str, tables: str = '', keyword: str = '') -> str:
        """查数据源的表结构(实时、准确),并叠加数据模型里的业务描述。

        - 不传 tables:返回表名列表;**已建数据模型的表会标上业务名和描述**,据此认出目标表。
          表很多时传 keyword(按 表名 或 业务名 模糊筛选,如"任务"、"用户"、"user")。
        - 传 tables(逗号分隔):返回这些表的字段(实时类型 + 业务说明)。

        :param datasource_code: 数据源编码
        :param tables: 可选,逗号分隔的表名,查这些表的字段
        :param keyword: 可选,列表名时按 表名/业务名 筛选
        :return: 表结构文本(结构实时,描述来自数据模型)
        """
        if self.allowed_codes is not None and datasource_code not in self.allowed_codes:
            return f'该应用未授权访问数据源: {datasource_code}(仅可用: {", ".join(self.allowed_codes)})'
        try:
            handler = _build_handler(datasource_code)
        except Exception as e:  # noqa: BLE001
            return f'数据源连接失败: {e}'
        models = _models_of_source(datasource_code)  # {object_name: {name, remark, fdesc}}
        tl = handler.table_labels() if hasattr(handler, 'table_labels') else {}  # 内置说明(如 akshare 函数中文名)
        is_api = getattr(handler, 'family', '') == 'api'
        api_hint = ('【API 数据源用法】每个“表”是一个数据接口函数(akshare 财经函数 / ccxt 交易所方法等);'
                    '取数在 run_datasource_query 里写 `result = handler.query("函数名", {参数})`'
                    '(返回 list[dict],已带重试),参数见下方各函数说明/接口文档;**勿用 SQL**。\n')

        def _label(t: str) -> str:
            m = models.get(t)
            if m:
                return f"{m['name']}{(': ' + m['remark']) if m.get('remark') else ''}"
            return tl.get(t, '')  # 回退到 handler 内置说明

        table_list = [t.strip() for t in tables.split(',') if t.strip()]
        try:
            if not table_list:
                names = handler.list_tables()
                kw = keyword.strip().lower()
                rows: list[str] = []
                for t in names:
                    label = _label(t)
                    if kw and kw not in t.lower() and kw not in label.lower():
                        continue
                    rows.append(f'- {t}' + (f'  ({label})' if label else ''))
                if not rows:
                    return (f'没有匹配「{keyword}」的表;换个关键词,或不传 keyword 看全部表。'
                            if kw else '该数据源无可见表。')
                tip = '(括号内为业务名/说明)'
                return ((api_hint if is_api else '') + f'表(共 {len(rows)} 张){tip}:\n' + '\n'.join(rows)
                        + '\n\n认出目标表后,用 tables 参数查它的字段/调用参数。')
            out: list[str] = []
            for t in table_list:
                cols = handler.get_columns(t)
                lbl = _label(t)
                head = f'表 {t}' + (f'「{lbl}」' if lbl else '')
                lines = []
                for c in cols:
                    cm = getattr(c, 'comment', '') or ''  # 字段注释用实时 introspect(准),不叠加数据模型
                    lines.append(f'  {c.name} {getattr(c, "type", "")}'.rstrip() + (f'  -- {cm}' if cm else ''))
                block = head + '\n' + '\n'.join(lines)
                # API 源(akshare 等):附完整接口文档(参数可选值/返回列/示例),便于精准调用
                if hasattr(handler, 'describe'):
                    doc = handler.describe(t)
                    if doc:
                        block += '\n  【接口文档】\n' + '\n'.join('    ' + ln for ln in doc.splitlines())
                out.append(block)
            return (api_hint if is_api else '') + '\n\n'.join(out)
        except Exception as e:  # noqa: BLE001
            return f'查询表结构失败(该源可能不支持 schema): {e}'

    def search_datasource_knowledge(self, datasource_code: str, query: str) -> str:
        """检索数据源的专属知识库:字段口径/业务规则/术语,**以及用户收藏的“验证过的取数解法”**。

        **写取数代码前必先调用**:结果里标 (QA) 的条目,其内容就是针对类似问题、已跑通的取数/分析代码,
        命中后应直接复用或仅按本次差异微调,不要从零重写。query 传用户的原始问题(尽量原文,利于精确命中)。

        :param datasource_code: 数据源编码
        :param query: 检索问题(传用户原始问题,如「拉出小米近一年走势并画 MACD」;或字段口径类问题)
        :return: 检索到的知识片段(含可复用的历史解法代码)
        """
        from module_rag.agent_tools import search_knowledge_base

        if self.allowed_codes is not None and datasource_code not in self.allowed_codes:
            return f'该应用未授权访问数据源: {datasource_code}'
        ds_id = _datasource_id(datasource_code)
        if not ds_id:
            return f'数据源不存在: {datasource_code}'
        try:
            return search_knowledge_base(query, source_id=ds_id)
        except Exception as e:  # noqa: BLE001
            return f'知识库检索失败: {e}'


# ---------------------------------------------------------------------------
# 同步元信息查询(agent 进程内,复用任务模块的同步会话)
# ---------------------------------------------------------------------------
def _list_datasources(codes: list[str] | None) -> list[dict]:
    from sqlalchemy import select

    from module_data.entity.do.data_do import DataSource
    from module_task_schedule.sync_db import get_sync_session_local

    db = get_sync_session_local()()
    try:
        stmt = select(DataSource.code, DataSource.name, DataSource.source_type)
        if codes:
            stmt = stmt.where(DataSource.code.in_(codes))
        return [{'code': r[0], 'name': r[1], 'source_type': r[2]} for r in db.execute(stmt).all()]
    finally:
        db.close()


def _models_of_source(datasource_code: str) -> dict:
    """该数据源下所有数据模型 → {object_name: {name, remark, fdesc:{字段:业务说明}}}。

    仅取业务描述(用于丰富实时结构),不取字段类型等结构信息(那些以实时 introspect 为准)。
    """
    from sqlalchemy import select

    from module_data.entity.do.data_do import DataModel
    from module_task_schedule.sync_db import get_sync_session_local

    db = get_sync_session_local()()
    try:
        rows = db.execute(select(DataModel.name, DataModel.object_name, DataModel.remark)
                          .where(DataModel.datasource_code == datasource_code, DataModel.status == 1)).all()
        out: dict[str, dict] = {}
        for name, obj, remark in rows:
            if not obj:
                continue
            out[obj] = {'name': name, 'remark': (remark or '').strip(" '\"　")}
        return out
    finally:
        db.close()


def _datasource_id(code: str) -> str | None:
    from sqlalchemy import select

    from module_data.entity.do.data_do import DataSource
    from module_task_schedule.sync_db import get_sync_session_local

    db = get_sync_session_local()()
    try:
        return db.execute(select(DataSource.id).where(DataSource.code == code)).scalars().first()
    finally:
        db.close()


def _build_handler(code: str) -> Any:
    """用明文连接(查库+解密)在 backend 进程建 handler,查只读元信息。"""
    from module_ai.tools.sandbox_code_tools import _resolve_datasource
    from module_data.handlers import create_handler

    ds = _resolve_datasource(code)
    return create_handler(ds['source_type'], ds['config'], ds['secrets'])
