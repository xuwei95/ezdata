"""数据探索工具:让 agent「看见」数据 —— 发现数据源、查表结构、检索数据源知识库。

与 SandboxCodeTools(执行代码)互补:这里是只读元信息查询(在 backend 进程直接查,
不走沙箱),让 LLM 先搞清"有哪些数据源/表/字段/业务口径",再去写取数代码。
"""

from __future__ import annotations

from typing import Any

from agno.tools import Toolkit


class DataAgentTools(Toolkit):
    """数据探索工具集(供数据 agent 调用)。"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name='data_explore',
            tools=[
                self.list_data_models, self.get_model_fields,      # 业务建模层(优先)
                self.list_datasources, self.get_table_schema,      # 数据源原始表层(兜底)
                self.search_datasource_knowledge,
            ],
            **kwargs,
        )

    def list_data_models(self, keyword: str = '') -> str:
        """列出已建的数据模型(业务名 / 对应表 / 数据源)。

        ⭐ 回答数据或业务问题时**优先用这个**:数据模型是对原始表的业务建模,带中文业务名和字段注释,
        比直接翻原始数据源表精准得多。按业务名搜到模型后,用 get_model_fields 看字段、再用
        run_datasource_query(数据源, SQL) 取数(SQL 里用模型的「表名」)。

        :param keyword: 可选,按业务名/编码模糊筛选(如"任务"、"订单");为空返回全部
        :return: 数据模型清单(业务名 | 模型编码 | 数据源编码 | 表名)
        """
        rows = _list_models(keyword.strip() or None)
        if not rows:
            return '未找到数据模型。' + ('换个关键词试试,或用 list_datasources 看原始数据源。' if keyword else '')
        def _rmk(r: dict) -> str:
            rk = (r['remark'] or '').strip(" '\"　")
            return f'  ({rk})' if rk else ''

        return '数据模型(业务名 | 模型编码 | 数据源编码 | 表名):\n' + '\n'.join(
            f"- {r['name']} | {r['code']} | {r['datasource_code']} | {r['object_name']}{_rmk(r)}"
            for r in rows)

    def get_model_fields(self, model_code: str) -> str:
        """查数据模型的字段(含业务注释),帮助写正确的取数 SQL。

        :param model_code: 数据模型编码(来自 list_data_models)
        :return: 字段清单(字段名 类型 -- 注释)+ 该模型对应的数据源/表名
        """
        m = _get_model(model_code)
        if not m:
            return f'数据模型不存在: {model_code}'
        head = f"模型「{m['name']}」→ 数据源 {m['datasource_code']} 的表 {m['object_name']}"
        fields = m.get('fields') or []
        if not fields:
            return head + '\n(字段未缓存,可用 get_table_schema 查实时结构)'
        lines = [f"  {f.get('name')} {f.get('type', '')}".rstrip()
                 + (f"  -- {f.get('comment')}" if f.get('comment') else '') for f in fields]
        return head + '\n字段:\n' + '\n'.join(lines)

    def list_datasources(self, codes: str = '') -> str:
        """列出平台可用的数据源(编码 / 名称 / 类型)。

        数据源很多时,传 codes(逗号分隔的数据源编码)只看指定的几个,避免一次性返回过多、不精准;
        为空则返回全部。拿到 code 后可用 get_table_schema 查表结构、run_datasource_query 取数。

        :param codes: 可选,逗号分隔的数据源编码,只返回这几个;为空返回全部
        :return: 数据源清单文本
        """
        code_list = [c.strip() for c in codes.split(',') if c.strip()] or None
        rows = _list_datasources(code_list)
        if not rows:
            return '未找到数据源。'
        return '可用数据源(编码 | 名称 | 类型):\n' + '\n'.join(
            f"- {r['code']} | {r['name'] or ''} | {r['source_type'] or ''}" for r in rows)

    def get_table_schema(self, datasource_code: str, tables: str = '') -> str:
        """查指定数据源的表结构。

        不传 tables 时返回「表名列表」;表很多时,先看表名再传 tables(逗号分隔)只查指定表的字段,
        避免一次性拉取所有表字段。

        :param datasource_code: 数据源编码
        :param tables: 可选,逗号分隔的表名,只返回这几个表的字段;为空只返回表名列表
        :return: 表结构文本
        """
        try:
            handler = _build_handler(datasource_code)
        except Exception as e:  # noqa: BLE001
            return f'数据源连接失败: {e}'
        table_list = [t.strip() for t in tables.split(',') if t.strip()]
        try:
            if not table_list:
                names = handler.list_tables()
                if not names:
                    return '该数据源无可见表。'
                return ('表列表(共 %d 张,用 tables 参数查指定表的字段):\n' % len(names)) + \
                    '\n'.join(f'- {t}' for t in names)
            out: list[str] = []
            for t in table_list:
                cols = handler.get_columns(t)
                lines = [f'  {c.name} {getattr(c, "type", "")}'.rstrip()
                         + (f'  -- {c.comment}' if getattr(c, 'comment', '') else '') for c in cols]
                out.append(f'表 {t} 字段:\n' + '\n'.join(lines))
            return '\n\n'.join(out)
        except Exception as e:  # noqa: BLE001
            return f'查询表结构失败(该源可能不支持 schema): {e}'

    def search_datasource_knowledge(self, datasource_code: str, query: str) -> str:
        """检索数据源的专属知识库(字段口径 / 业务规则 / 术语解释),辅助理解该数据源怎么取数。

        :param datasource_code: 数据源编码
        :param query: 检索问题(如「订单状态字段有哪些取值」)
        :return: 检索到的知识片段文本
        """
        from module_rag.agent_tools import search_knowledge_base

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


def _list_models(keyword: str | None) -> list[dict]:
    from sqlalchemy import or_, select

    from module_data.entity.do.data_do import DataModel
    from module_task_schedule.sync_db import get_sync_session_local

    db = get_sync_session_local()()
    try:
        stmt = select(DataModel.name, DataModel.code, DataModel.datasource_code,
                      DataModel.object_name, DataModel.remark).where(DataModel.status == 1)
        if keyword:
            like = f'%{keyword}%'
            stmt = stmt.where(or_(DataModel.name.like(like), DataModel.code.like(like)))
        return [{'name': r[0], 'code': r[1], 'datasource_code': r[2], 'object_name': r[3], 'remark': r[4]}
                for r in db.execute(stmt).all()]
    finally:
        db.close()


def _get_model(code: str) -> dict | None:
    from sqlalchemy import select

    from module_data.entity.do.data_do import DataModel
    from module_task_schedule.sync_db import get_sync_session_local

    db = get_sync_session_local()()
    try:
        r = db.execute(select(DataModel.name, DataModel.datasource_code, DataModel.object_name,
                              DataModel.fields).where(DataModel.code == code)).first()
        if not r:
            return None
        return {'name': r[0], 'datasource_code': r[1], 'object_name': r[2], 'fields': r[3]}
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
