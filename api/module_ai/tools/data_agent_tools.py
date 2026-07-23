"""数据探索工具:查数据源原始表结构(实时、准确),并用数据模型里的业务描述把它"讲明白"。

设计取舍:结构(表、字段、类型、字段注释)一律以**实时 introspect** 为准——数据模型缓存的字段可能过时、失真;
只把数据模型里**人工写的表级业务描述**(业务名、表说明 remark)叠加到实时表列表上,帮 LLM 认出表的业务含义。
"""

from __future__ import annotations

from typing import Any

from agno.tools import Toolkit

from utils.log_util import logger

# 输出瘦身:未建模表名最多列这么多(其余提示用 keyword 搜);API 接口文档最多保留这么多行。
# 目的是控制工具输出体积——这些结果会留在对话 history、每轮重发,越小越省 token。
_UNMODELED_CAP = 60
_DOC_LINE_CAP = 30
# 注入取数上下文的业务文档(remark)最多这么多字符:超了截断,避免长文档每轮重发烧 token。
# 完整内容仍在数据源备注里可查/可编辑。
_BIZ_CTX_CAP = 2000

# search_knowledge_base 命中为空时返回的固定提示语(见 module_rag.agent_tools):
# 命中这些即视为「无检索结果」,此时才回落返回整段业务上下文。
_KB_EMPTY_HINTS = ('未找到可用知识库。', '知识库中未检索到相关内容。')


class DataAgentTools(Toolkit):
    """数据探索工具集(供数据 agent 调用)。"""

    def __init__(self, allowed_codes: list | None = None, skills: list | None = None, **kwargs: Any) -> None:
        # allowed_codes 非空时,数据探索仅限这些数据源(应用「数据分析」选定的源);None=不限。
        self.allowed_codes = set(allowed_codes) if allowed_codes else None
        # 知识型技能→按数据源浮现:{datasource_code: [(skill_code, name), ...]}
        # 认源(search_datasource_knowledge)时提示"本源有专属技能,可 load_skill",实现按需发现、不占常驻。
        self._src_skills: dict[str, list] = {}
        for s in skills or []:
            if (s.get('skill_type') == 'knowledge') and s.get('code'):
                for dc in s.get('ds_codes') or []:
                    self._src_skills.setdefault(dc, []).append((s['code'], s.get('name') or s['code']))
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
            code_list = list(self.allowed_codes) if not code_list else [c for c in code_list if c in self.allowed_codes]
        rows = _list_datasources(code_list)
        if not rows:
            return '未找到数据源。'
        blocks: list[str] = []
        for r in rows:
            header = f'【{r["code"]}】{r["name"] or ""} ({r["source_type"] or ""})'
            try:
                names = _build_handler(r['code']).list_tables()
            except Exception:
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
                parts.append(f'  - {t} — {m["name"]}{(": " + m["remark"]) if m.get("remark") else ""}')
            # 未建模的表(多为系统/中间表):表名紧凑列成一行,仍全在可搜,但不逐行占空间
            if unmodeled:
                label = '  其余未建模表' if modeled else '  表(均未建模)'
                shown = ', '.join(unmodeled[:_UNMODELED_CAP])
                more = (
                    f' …(共 {len(unmodeled)},其余用 get_table_schema(源, keyword=) 搜)'
                    if len(unmodeled) > _UNMODELED_CAP
                    else ''
                )
                parts.append(f'{label}({len(unmodeled)}): ' + shown + more)
            blocks.append('\n'.join(parts))
        return (
            '数据源及其表(表名后「— 业务名: 描述」是已建模的):\n\n'
            + '\n\n'.join(blocks)
            + '\n\n认出目标表后:get_table_schema(数据源编码, tables="表名") 查字段 → run_datasource_query 取数。'
        )

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
        except Exception as e:
            return f'数据源连接失败: {e}'
        models = _models_of_source(datasource_code)  # {object_name: {name, remark, fdesc}}
        tl = handler.table_labels() if hasattr(handler, 'table_labels') else {}  # 内置说明(如 akshare 函数中文名)
        family = getattr(handler, 'family', '')
        is_api = family == 'api'
        # handler.query 的调用形态随 family 不同——务必按对应写法。弱模型最易犯的错:
        # 把 ES/Mongo 也当成 (名, 参数) 两参调用(如 handler.query("索引", {DSL})),必报错。
        if is_api:
            usage_hint = (
                '【API 数据源用法】每个“表”是一个数据接口函数(akshare 财经函数 / ccxt 交易所方法等);'
                '取数在 run_datasource_query 里写 `result = handler.query("函数名", {参数})`'
                '(返回 list[dict],已带重试),参数见下方各函数说明/接口文档;**勿用 SQL**。\n'
            )
        elif family == 'search':  # Elasticsearch
            usage_hint = (
                '【ES 数据源用法】取数写 `result = handler.query({"index":"索引名","body":{<ES 查询 DSL>}})`——'
                '**单个 dict 参数**(index + body),切勿写成 handler.query("索引", {DSL}) 这种两参形式。'
                '要汇总/分组/取前 N 时把聚合放 body.aggs 且 body.size=0(handler 会把聚合桶拍平成行);'
                '文本字段(text)做 terms 分组/排序/精确过滤用 `字段.keyword`。例:\n'
                '  result = handler.query({"index":"idx","body":{"size":0,"aggs":{"g":{"terms":'
                '{"field":"名称.keyword","size":10},"aggs":{"amt":{"sum":{"field":"成交额"}}}}}}})\n'
            )
        elif family == 'document':  # MongoDB
            usage_hint = (
                '【Mongo 数据源用法】取数写 `result = handler.query({"collection":"集合名","pipeline":[<聚合管道>]})`'
                '——单个 dict 参数(collection + pipeline)。\n'
            )
        elif family == 'rdbms':  # SQL 族
            usage_hint = (
                '【SQL 数据源用法】取数写 `result = handler.query("SELECT ... FROM 表 ...")`'
                '——一条只读 SQL 字符串(单条、不改数据)。\n'
            )
        else:
            usage_hint = ''

        def _label(t: str) -> str:
            m = models.get(t)
            if m:
                return f'{m["name"]}{(": " + m["remark"]) if m.get("remark") else ""}'
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
                    return (
                        f'没有匹配「{keyword}」的表;换个关键词,或不传 keyword 看全部表。'
                        if kw
                        else '该数据源无可见表。'
                    )
                tip = '(括号内为业务名/说明)'
                return (
                    usage_hint
                    + f'表(共 {len(rows)} 张){tip}:\n'
                    + '\n'.join(rows)
                    + '\n\n认出目标表后,用 tables 参数查它的字段/调用参数。'
                )
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
                # 血缘来源:该表由哪个任务从哪个上游源抽取(让 agent 懂数据从哪来/多新/怎么刷新)
                try:
                    from module_data.service.lineage_service import LineageService

                    prov = LineageService.provenance_sync(datasource_code, t)
                    if prov:
                        block += '\n  ' + prov
                except Exception:
                    pass
                # API 源(akshare 等):附完整接口文档(参数可选值/返回列/示例),便于精准调用
                if hasattr(handler, 'describe'):
                    doc = handler.describe(t)
                    if doc:
                        dl = doc.splitlines()
                        if len(dl) > _DOC_LINE_CAP:
                            dl = dl[:_DOC_LINE_CAP] + ['…(接口文档已截断,需要更多参数说明再问)']
                        block += '\n  【接口文档】\n' + '\n'.join('    ' + ln for ln in dl)
                out.append(block)
            return usage_hint + '\n\n'.join(out)
        except Exception as e:
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
        # 该源的业务上下文(remark):表关系/口径/术语。命中知识库时不再每次附带这一整坨,
        # 只在检索为空时才回落返回它(避免空手而归);命中则只返回检索结果,减少上下文冗余。
        ctx = _datasource_business_context(datasource_code)
        if len(ctx) > _BIZ_CTX_CAP:
            ctx = ctx[:_BIZ_CTX_CAP] + '\n…(业务上下文较长已截断,完整内容见数据源备注)'
        try:
            kb = search_knowledge_base(query, source_id=ds_id)
        except Exception as e:
            kb = f'(知识库检索失败: {e})'
        # 知识型技能浮现:认到该源时提示可加载其专属操作手册(渐进披露,不占常驻清单)
        hint = ''
        for scode, sname in self._src_skills.get(datasource_code, []):
            hint += f'\n\n【本数据源专属技能】{sname} —— 需要时 load_skill("{scode}") 获取操作手册。'
        if kb.strip() in _KB_EMPTY_HINTS:
            # 知识库无命中 → 回落到业务上下文这一坨
            if ctx:
                return f'【业务上下文】\n{ctx}\n\n(知识库暂无匹配「{query}」的条目){hint}'
            return kb + hint
        # 命中 → 只返回检索结果(+ 专属技能提示)
        return kb + hint


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
        rows = db.execute(
            select(DataModel.name, DataModel.object_name, DataModel.remark).where(
                DataModel.datasource_code == datasource_code, DataModel.status == 1
            )
        ).all()
        out: dict[str, dict] = {}
        for name, obj, remark in rows:
            if not obj:
                continue
            out[obj] = {'name': name, 'remark': (remark or '').strip(' \'"　')}
        return out
    finally:
        db.close()


# 表数 ≤ 此值时直接全量注入(小库检索收窄意义不大);超过才启用向量检索 Top-K。
_CATALOG_RETRIEVAL_MIN_TABLES = 20
_CATALOG_REMARK_CAP = 60  # Tier B 每表备注截断(注入压缩;完整语义仍在 embedding 文档里)


def build_data_catalog(
    allowed_codes: list | None = None, *, question: str | None = None, k: int = 8, max_sources: int = 30, max_tables: int = 12
) -> str:
    """构造数据目录注入 system prompt,减少 agent 发现往返。

    检索收窄(见 docs/catalog-retrieval-narrowing-design.md):
    - question 非空 + embedding 可用 + 表数 > 阈值 → Tier A(源级全列)+ Tier B(按问题检索 Top-K 表带备注)。
    - 否则 / 检索异常 / 小库 → 回退全量目录 `_full_data_catalog`(永不比现状差)。
    """
    if question:
        try:
            narrowed = _retrieved_catalog(allowed_codes, question, k, max_sources)
            if narrowed:
                return narrowed
        except Exception as e:
            logger.warning(f'[catalog] 检索收窄失败,回退全量目录: {e}')
    return _full_data_catalog(allowed_codes, max_sources=max_sources, max_tables=max_tables)


def _retrieved_catalog(allowed_codes: list | None, question: str, k: int, max_sources: int) -> str | None:
    """Tier A 源级 + Tier B 检索表。不满足启用条件(小库/无 embedding/无命中)返回 None → 上层回退全量。"""
    from module_ai.tools.catalog_index import CatalogRetrievalService

    if not CatalogRetrievalService.available():
        return None
    from sqlalchemy import func, select

    from module_data.entity.do.data_do import DataModel, DataSource
    from module_task_schedule.sync_db import get_sync_session_local

    tenant = None
    try:
        from common.context import RequestContext

        tenant = RequestContext.get_effective_tenant_id()
    except Exception:
        tenant = None

    db = get_sync_session_local()()
    try:
        ds_stmt = select(DataSource.code, DataSource.name, DataSource.source_type)
        if allowed_codes:
            ds_stmt = ds_stmt.where(DataSource.code.in_(list(allowed_codes)))
        sources = [{'code': r[0], 'name': r[1], 'source_type': r[2]} for r in db.execute(ds_stmt).all()]
        if not sources:
            return None
        codes = [s['code'] for s in sources]
        total = db.execute(
            select(func.count()).select_from(DataModel).where(
                DataModel.datasource_code.in_(codes), DataModel.status == 1, DataModel.object_name != ''
            )
        ).scalar() or 0
    finally:
        db.close()
    if total <= _CATALOG_RETRIEVAL_MIN_TABLES:
        return None  # 小库:回退全量更简单

    hits = CatalogRetrievalService.retrieve_tables(question, scope_codes=allowed_codes, tenant_id=tenant, k=k)
    if not hits:
        return None
    # Tier A:源级(不含表)
    a_lines = [f'【{s["code"]}】{s["name"] or ""}({s["source_type"] or ""})' for s in sources[:max_sources]]
    # Tier B:与问题最相关的表——对齐全量目录的密度(仅「表名=业务名」),相关性由 embedding 内部处理;
    # 备注不注入(agent 仍会 get_table_schema 取精确字段,注入 remark 省不下这步、只增 token)。
    b_lines = []
    for h in hits:
        obj, nm = h.get('object_name'), h.get('model_name')
        b_lines.append(f'· [{h.get("datasource_code")}] {obj}' + (f'={nm}' if nm else ''))
    return (
        '可用数据源(源级):\n'
        + '\n'.join(a_lines)
        + '\n\n与当前问题最相关的表(已按相关度筛选,认得出就直接用;其余表用 list_datasources/get_table_schema 探索):\n'
        + '\n'.join(b_lines)
    )


def _full_data_catalog(allowed_codes: list | None = None, *, max_sources: int = 30, max_tables: int = 12) -> str:
    """全量精简目录(源 + 已建模表业务名)。检索不可用时的回退,也是小库默认路径。"""
    try:
        from sqlalchemy import select

        from module_data.entity.do.data_do import DataModel, DataSource
        from module_task_schedule.sync_db import get_sync_session_local

        db = get_sync_session_local()()
        try:
            ds_stmt = select(DataSource.code, DataSource.name, DataSource.source_type)
            if allowed_codes:
                ds_stmt = ds_stmt.where(DataSource.code.in_(list(allowed_codes)))
            sources = [{'code': r[0], 'name': r[1], 'source_type': r[2]} for r in db.execute(ds_stmt).all()]
            if not sources:
                return ''
            m_rows = db.execute(
                select(DataModel.datasource_code, DataModel.object_name, DataModel.name).where(
                    DataModel.datasource_code.in_([s['code'] for s in sources]), DataModel.status == 1
                )
            ).all()
        finally:
            db.close()

        by_src: dict[str, list] = {}
        for dcode, obj, nm in m_rows:
            if obj:
                by_src.setdefault(dcode, []).append((obj, nm))
        lines: list[str] = []
        for s in sources[:max_sources]:
            head = f'【{s["code"]}】{s["name"] or ""}({s["source_type"] or ""})'
            mods = by_src.get(s['code']) or []
            if mods:
                items = [f'{obj}={nm}' if nm else obj for obj, nm in mods[:max_tables]]
                more = f' …等{len(mods)}张' if len(mods) > max_tables else ''
                lines.append(head + ': ' + ', '.join(items) + more)
            else:
                lines.append(head + '(未建模,用 get_table_schema 探索)')
        if len(sources) > max_sources:
            lines.append(f'…(共 {len(sources)} 个数据源)')
        return '已有数据源与关键表(表名=业务名,均已建模;认得出目标就直接用,不必再调 list_datasources):\n' + '\n'.join(
            lines
        )
    except Exception:
        return ''


def _datasource_id(code: str) -> str | None:
    from sqlalchemy import select

    from module_data.entity.do.data_do import DataSource
    from module_task_schedule.sync_db import get_sync_session_local

    db = get_sync_session_local()()
    try:
        return db.execute(select(DataSource.id).where(DataSource.code == code)).scalars().first()
    finally:
        db.close()


def _datasource_business_context(code: str) -> str:
    """读该数据源的 remark(=业务上下文文档),取数前置顶注入。无则空串。"""
    from sqlalchemy import select

    from module_data.entity.do.data_do import DataSource
    from module_task_schedule.sync_db import get_sync_session_local

    db = get_sync_session_local()()
    try:
        r = db.execute(select(DataSource.remark).where(DataSource.code == code)).scalars().first()
        return (r or '').strip()
    finally:
        db.close()


def _build_handler(code: str) -> Any:
    """用明文连接(查库+解密)在 backend 进程建 handler,查只读元信息。"""
    from ezdata.handlers import create_handler
    from module_ai.tools.sandbox_code_tools import _resolve_datasource

    ds = _resolve_datasource(code)
    return create_handler(ds['source_type'], ds['config'], ds['secrets'])
