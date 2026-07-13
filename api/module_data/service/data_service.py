import json
import uuid
from datetime import datetime
from typing import Any

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from ezdata import prompts as ez_prompts
from ezdata import services as ez_services
from ezdata.handlers import Capability, create_handler, get_handler_cls
from ezdata.utils.etl_util import (
    assert_readonly_sql,
    is_file_target,
    json_safe_rows,
    serialize_records,
    short_err,
    stream_statement,
)
from module_data.dao.data_dao import AnalysisTemplateDao, DataModelDao, DataSourceDao
from module_data.entity.do.data_do import DataModel, DataSource
from module_data.entity.vo.data_vo import (
    AnalysisTemplateVo,
    DataModelQuery,
    DataModelVo,
    DataSourceQuery,
    DataSourceVo,
    QueryReq,
    SearchReq,
    TestConnReq,
)
from utils.crypto_util import CryptoUtil

MASK = '******'


def _decrypt_secrets(ds: DataSource) -> dict:
    if not ds.secrets:
        return {}
    try:
        return json.loads(CryptoUtil.decrypt(ds.secrets))
    except Exception:
        return {}


def _build_handler(source_type: str, config: dict | None, secrets: dict | None, *, cache: bool = True) -> Any:
    return create_handler(source_type, config or {}, secrets or {}, cache=cache)


def _handler_from_ds(ds: DataSource) -> Any:
    return _build_handler(ds.source_type, ds.config or {}, _decrypt_secrets(ds))


def _source_structure_text(ds: DataSource, max_tables: int = 30, max_fields: int = 40) -> str:
    """采集数据源结构文本(表 + 字段),供 AI 分析业务上下文。有上限,避免超大库把 prompt 撑爆。同步阻塞,由调用方 threadpool 包裹。"""
    try:
        handler = _handler_from_ds(ds)
        tables = handler.list_tables() or []
    except Exception as e:
        return f'(无法读取结构: {e})'
    is_api = getattr(handler, 'family', '') == 'api'
    lines = [f'共 {len(tables)} 张{"接口" if is_api else "表"}:']
    for t in tables[:max_tables]:
        try:
            cols = handler.get_columns(t)
        except Exception:
            lines.append(f'- {t}')
            continue
        fs = ', '.join((f'{c.name}:{getattr(c, "type", "")}').rstrip(':') for c in cols[:max_fields])
        more = ' …' if len(cols) > max_fields else ''
        lines.append(f'- {t}({fs}{more})')
    if len(tables) > max_tables:
        lines.append(f'…(还有 {len(tables) - max_tables} 张未列)')
    return '\n'.join(lines)


async def _ai_resolve_cfg(db: AsyncSession) -> dict:
    """解析系统内部 AI 生成(ETL 取数/转换、数据查询 AI 取数)所用模型。

    这些入口没有"选模型"的 UI,统一用**系统兜底模型**(环境变量 LLM_*);
    仅当兜底未配置时,才回退到「AI 模型管理」里第一个启用的模型(便于纯库内配置的部署)。
    """
    from config.env import AiConfig

    if AiConfig.enabled:  # 首选:系统兜底模型(api_key 明文)
        return dict(
            provider=AiConfig.provider,
            model_code=AiConfig.llm_model,
            model_name=None,
            api_key=AiConfig.llm_api_key,
            base_url=AiConfig.llm_url or None,
            max_tokens=AiConfig.llm_max_tokens or 1024,
        )

    # 兜底未配置 → 回退库内第一个启用模型(api_key 为 AES 密文)
    from sqlalchemy import select

    from module_ai.entity.do.ai_model_do import AiModels

    mc = (
        (await db.execute(select(AiModels).where(AiModels.status == '0').order_by(AiModels.model_sort)))
        .scalars()
        .first()
    )
    if mc:
        if not mc.api_key:  # 启用了但没填 key:给清楚提示,而不是暴露 provider 的环境变量名
            raise ServiceException(
                message=f'启用的模型「{mc.model_name or mc.model_code}」未配置 API Key,'
                f'请在「AI 模型管理」补全,或配置环境变量兜底模型(LLM_TYPE/LLM_MODEL/LLM_API_KEY)'
            )
        return dict(
            provider=mc.provider,
            model_code=mc.model_code,
            model_name=mc.model_name,
            api_key=CryptoUtil.decrypt(mc.api_key),
            base_url=mc.base_url,
            max_tokens=mc.max_tokens or 1024,
        )
    raise ServiceException(
        message='未配置可用 AI 模型:请配置环境变量兜底模型(LLM_TYPE/LLM_MODEL/LLM_API_KEY[/LLM_URL]),或在「AI 模型管理」启用一个'
    )


def _strip_fence(text: str) -> str:
    """去掉 markdown ```lang ... ``` 代码围栏。"""
    t = (text or '').strip()
    if t.startswith('```'):
        t = t.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
    return t


async def _ai_complete(db: AsyncSession, prompt: str) -> str:
    """一次性补全并返回文本(自动去围栏)。"""
    from utils.ai_util import AiUtil

    cfg = await _ai_resolve_cfg(db)

    def _run() -> str:
        from agno.agent import Agent

        out = Agent(model=AiUtil.get_model_from_factory(**cfg)).run(prompt)
        return _strip_fence(getattr(out, 'content', None) or str(out))

    return await run_in_threadpool(_run)


def _ai_stream(cfg: dict, prompt: str):
    """同步生成器:流式产出文本增量,供 StreamingResponse 使用(围栏由前端采用时再去除)。"""
    from agno.agent import Agent

    from utils.ai_util import AiUtil

    try:
        agent = Agent(model=AiUtil.get_model_from_factory(**cfg))
        produced = False
        for ev in agent.run(prompt, stream=True):
            chunk = getattr(ev, 'content', None)
            if chunk:
                produced = True
                yield chunk
        if not produced:  # 个别模型/版本不产 content 增量事件,回退整段
            out = Agent(model=AiUtil.get_model_from_factory(**cfg)).run(prompt)
            yield getattr(out, 'content', None) or str(out)
    except Exception as e:
        yield f'\n[生成出错] {short_err(e)}'


class DataMetaService:
    """静态元信息:源类型 / 连接 schema / 操作符。"""

    @staticmethod
    def source_types() -> list[dict]:
        # 委托 ezdata,再转 camelCase 对齐前端/接口约定(source_type -> sourceType)
        return [
            {
                'sourceType': t['source_type'],
                'title': t['title'],
                'family': t['family'],
                'capabilities': t['capabilities'],
            }
            for t in ez_services.list_source_types()
        ]

    @staticmethod
    def connection_schema(source_type: str) -> dict:
        return ez_services.connection_schema(source_type)

    @staticmethod
    def source_type_icon(source_type: str) -> str | None:
        """该数据源类型的品牌图标 SVG 文本(供前端渲染);未注册/无图标返回 None。"""
        return ez_services.source_type_icon(source_type)

    @staticmethod
    def operators() -> list[dict]:
        return ez_services.operators()


class DataSourceService:
    """数据源服务。"""

    @classmethod
    async def get_list(cls, db: AsyncSession, q: DataSourceQuery, is_page: bool = False) -> Any:
        result = await DataSourceDao.get_list(db, q, is_page)
        for row in result.rows if is_page else result:
            row['secrets'] = None  # 列表不回密文
        return result

    @classmethod
    async def detail(cls, db: AsyncSession, ds_id: str) -> DataSourceVo:
        ds = await DataSourceDao.get_by_id(db, ds_id)
        if not ds:
            raise ServiceException(message='数据源不存在')
        # 不读 DO 的密文 secrets,手动构造 + 脱敏
        vo = DataSourceVo(
            id=ds.id,
            name=ds.name,
            code=ds.code,
            source_type=ds.source_type,
            family=ds.family,
            config=ds.config,
            status=ds.status,
            last_test_at=ds.last_test_at,
            remark=ds.remark,
            create_by=ds.create_by,
            create_time=ds.create_time,
            update_by=ds.update_by,
            update_time=ds.update_time,
        )
        secret_fields = get_handler_cls(ds.source_type).secret_fields() if ds.source_type else []
        vo.secrets = dict.fromkeys(secret_fields, MASK) if secret_fields else None
        return vo

    @classmethod
    async def prep_analyze_context(cls, db: AsyncSession, ds_id: str) -> tuple[dict, str]:
        """AI 解析业务上下文:读**现有描述 + 整体结构**,拼提示词 + 模型配置(供流式生成)。"""
        ds = await DataSourceDao.get_by_id(db, ds_id)
        if not ds:
            raise ServiceException(message='数据源不存在')
        structure = await run_in_threadpool(_source_structure_text, ds)
        current = (ds.remark or '').strip() or '(暂无)'
        prompt = (
            f'你是数据平台的建模与业务分析专家。下面是数据源「{ds.name}」(类型 {ds.source_type})的**现有描述**与**整体结构**。'
            '请先读懂现有描述,再结合结构,产出/完善这个数据源的**业务上下文文档**,供后续 AI 取数时参考。\n'
            '覆盖(有则写、无则略;简洁 Markdown,中文):① 数据源用途与主要业务对象;② 关键表/接口及含义;'
            '③ 表间关系/常用 join;④ 重要指标口径(怎么算);⑤ 常见问法 → 用哪张表/哪些字段;'
            '⑥ 取数注意(如 ES 文本聚合用 .keyword、akshare 是函数调用非 SQL、时间字段格式等)。\n'
            '只输出业务上下文文档本身,不要寒暄、不要代码块包裹整篇。\n\n'
            f'【现有描述】\n{current}\n\n【整体结构】\n{structure}'
        )
        cfg = await _ai_resolve_cfg(db)
        return cfg, prompt

    @classmethod
    async def add(cls, db: AsyncSession, vo: DataSourceVo, operator: str) -> CrudResponseModel:
        try:
            obj = {
                'id': uuid.uuid4().hex,
                'name': vo.name,
                'code': vo.code or uuid.uuid4().hex[:8],
                'source_type': vo.source_type,
                'family': get_handler_cls(vo.source_type).family if vo.source_type else None,
                'config': vo.config or {},
                'secrets': CryptoUtil.encrypt(json.dumps(vo.secrets)) if vo.secrets else None,
                'status': 'untested',
                'remark': vo.remark,
                'create_by': operator,
                'create_time': datetime.now(),
            }
            await DataSourceDao.add(db, obj)
            await db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def edit(cls, db: AsyncSession, vo: DataSourceVo, operator: str) -> CrudResponseModel:
        ds = await DataSourceDao.get_by_id(db, vo.id)
        if not ds:
            raise ServiceException(message='数据源不存在')
        try:
            data: dict[str, Any] = {'update_by': operator, 'update_time': datetime.now()}
            # code / source_type / family 是引用锚点,创建后不可改(防止下游引用串掉)
            for f in ('name', 'config', 'remark'):
                if getattr(vo, f) is not None:
                    data[f] = getattr(vo, f)
            # 仅当传了非脱敏 secrets 才更新
            if vo.secrets and MASK not in vo.secrets.values():
                data['secrets'] = CryptoUtil.encrypt(json.dumps(vo.secrets))
            await DataSourceDao.edit(db, vo.id, data)
            await db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def delete(cls, db: AsyncSession, ids: str) -> CrudResponseModel:
        try:
            await DataSourceDao.remove(db, [i for i in ids.split(',') if i])
            await db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def test_connection(cls, db: AsyncSession, req: TestConnReq) -> dict:
        if req.id:
            ds = await DataSourceDao.get_by_id(db, req.id)
            if not ds:
                raise ServiceException(message='数据源不存在')
            handler = _handler_from_ds(ds)
        else:
            handler = _build_handler(req.source_type, req.config, req.secrets, cache=False)  # 未保存配置不入缓存
        result = await run_in_threadpool(handler.test_connection)
        if req.id:
            await DataSourceDao.edit(
                db, req.id, {'status': 'ok' if result.success else 'failed', 'last_test_at': datetime.now()}
            )
            await db.commit()
        return {'success': result.success, 'message': result.message, 'latencyMs': result.latency_ms}

    @classmethod
    async def list_tables(cls, db: AsyncSession, ds_id: str) -> list[str]:
        ds = await DataSourceDao.get_by_id(db, ds_id)
        if not ds:
            raise ServiceException(message='数据源不存在')
        handler = _handler_from_ds(ds)
        return await run_in_threadpool(handler.list_tables)

    @classmethod
    async def get_columns(cls, db: AsyncSession, ds_id: str, table: str) -> list[dict]:
        ds = await DataSourceDao.get_by_id(db, ds_id)
        if not ds:
            raise ServiceException(message='数据源不存在')
        handler = _handler_from_ds(ds)
        cols = await run_in_threadpool(handler.get_columns, table)
        return [{'name': c.name, 'type': c.type, 'nullable': c.nullable, 'comment': c.comment} for c in cols]


class DataModelService:
    """数据模型服务。"""

    @classmethod
    async def get_list(cls, db: AsyncSession, q: DataModelQuery, is_page: bool = False) -> Any:
        return await DataModelDao.get_list(db, q, is_page)

    @classmethod
    async def detail(cls, db: AsyncSession, m_id: str) -> DataModelVo:
        m = await DataModelDao.get_by_id(db, m_id)
        if not m:
            raise ServiceException(message='数据模型不存在')
        vo = DataModelVo.model_validate(m)
        # 字段是 introspect 缓存:种子直插的模型 / 建模时底表还没数据(如 ES 索引当时为空)会留空。
        # 留空则按 数据源+object_name 实时取一次字段并回填缓存,使字段表格不再空(ES/SQL 通用)。
        if not vo.fields and m.datasource_code and m.object_name:
            cols = None
            try:
                ds = await DataSourceDao.get_by_code(db, m.datasource_code)
                if ds:
                    handler = _handler_from_ds(ds)
                    cols = await run_in_threadpool(handler.get_columns, m.object_name)
            except Exception:
                cols = None
            if cols:
                vo.fields = [
                    {'name': c.name, 'type': c.type, 'nullable': c.nullable, 'comment': c.comment} for c in cols
                ]
                try:  # 回填缓存,下次直接读库;失败不影响本次返回
                    await DataModelDao.edit(db, m_id, {'fields': vo.fields})
                    await db.commit()
                except Exception:
                    await db.rollback()
        return vo

    @classmethod
    async def ensure_custom_query_model(cls, db: AsyncSession, datasource_code: str, operator: str) -> str:
        """get-or-create 该数据源的 custom_query 模型(承接对话图表存看板);每源复用一个,返回 model_id。"""
        if not datasource_code:
            raise ServiceException(message='缺少数据源编码')
        existing = await DataModelDao.get_custom_query(db, datasource_code)
        if existing:
            return existing.id
        ds = await DataSourceDao.get_by_code(db, datasource_code)
        if not ds:
            raise ServiceException(message='数据源不存在')
        m = await DataModelDao.add(
            db,
            {
                'id': uuid.uuid4().hex,
                'name': f'自定义查询-{ds.name or datasource_code}',
                'code': 'cq_' + uuid.uuid4().hex[:8],
                'datasource_code': datasource_code,
                'kind': 'custom_query',
                'object_name': '',
                'auth': 'query',
                'status': 1,
                'create_by': operator,
                'create_time': datetime.now(),
            },
        )
        return m.id

    @classmethod
    async def add(cls, db: AsyncSession, vo: DataModelVo, operator: str) -> CrudResponseModel:
        try:
            obj = vo.model_dump(exclude={'id', 'create_time', 'update_time', 'create_by', 'update_by'})
            obj.update(
                id=uuid.uuid4().hex,
                code=vo.code or uuid.uuid4().hex[:8],
                create_by=operator,
                create_time=datetime.now(),
            )
            await DataModelDao.add(db, obj)
            await db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def edit(cls, db: AsyncSession, vo: DataModelVo, operator: str) -> CrudResponseModel:
        m = await DataModelDao.get_by_id(db, vo.id)
        if not m:
            raise ServiceException(message='数据模型不存在')
        try:
            data = vo.model_dump(exclude_unset=True, exclude={'id', 'create_time', 'create_by'})
            data.update(update_by=operator, update_time=datetime.now())
            await DataModelDao.edit(db, vo.id, data)
            await db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def delete(cls, db: AsyncSession, ids: str) -> CrudResponseModel:
        try:
            await DataModelDao.remove(db, [i for i in ids.split(',') if i])
            await db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e


_CHART_TYPES = frozenset({
    'bar', 'bar_stack', 'bar_percent', 'hbar', 'line', 'area', 'line_stack',
    'pie', 'donut', 'rose', 'scatter', 'radar', 'funnel', 'gauge', 'kpi', 'table',
})
_CHART_AGGS = frozenset({'sum', 'avg', 'count', 'max', 'min', 'none'})


def _chart_cfg_prompt(columns: list[str], question: str) -> str:
    """让 LLM 依据数据列 + 自然语言,产出 EchartsBuilder 的图表配置 JSON(只输出 JSON)。"""
    return (
        '你是数据可视化专家。现有数据列(必须严格使用这些列名,不要杜撰):\n'
        f'{", ".join(columns)}\n\n'
        f'用户需求:{question}\n\n'
        '请输出一个图表配置 JSON,字段说明:\n'
        '- type: 图表类型,取值之一 bar(柱)/bar_stack(堆叠柱)/bar_percent(百分比堆叠)/hbar(横向条)/'
        'line(折线)/area(面积)/line_stack(堆叠面积)/pie(饼)/donut(环形)/rose(玫瑰)/scatter(散点)/'
        'radar(雷达)/funnel(漏斗)/gauge(仪表盘)/kpi(指标卡)/table(明细表)\n'
        '- x: 类别/维度列名(kpi/table 可留空)\n'
        '- ys: 度量数组,每项 {"field":"列名","agg":"sum|avg|count|max|min|none"},可多个;'
        '若该列本身已是聚合结果(如查询里已写 SUM(x)/COUNT(*) 算好),agg 用 none 直接画,不要再二次聚合\n'
        '- series: 分组拆分列名(不需要则空字符串)\n'
        '- sort: {"by":"" 或 "__x__" 或某度量列名,"dir":"desc|asc"}\n'
        '- topN: 整数,只取前 N(不限填 0)\n'
        '- style: 可选,可含 {"title":"图表标题"}\n'
        '选型建议:占比看 pie/donut;趋势随时间看 line;类别对比看 bar;单一汇总指标看 kpi。'
        '只用上面列出的真实列名。**只输出 JSON 本身,不要 markdown 代码块、不要任何解释文字。**'
    )


def _normalize_chart_cfg(cfg: Any) -> dict:
    """清洗 LLM 产出的图表配置:类型白名单、ys 归一、sort/topN 兜底。字段合法性交前端 inferFields 再校。"""
    if not isinstance(cfg, dict):
        raise ServiceException(message='AI 生成的图表配置格式不正确,请换个说法重试')
    if cfg.get('type') not in _CHART_TYPES:
        cfg['type'] = 'bar'
    ys = cfg.get('ys')
    if isinstance(ys, dict):
        ys = [ys]
    if not isinstance(ys, list) or not ys:
        ys = [{'field': cfg['y'], 'agg': cfg.get('agg')}] if cfg.get('y') else []
    norm = []
    for it in ys:
        if isinstance(it, dict) and it.get('field'):
            norm.append({'field': str(it['field']), 'agg': it.get('agg') if it.get('agg') in _CHART_AGGS else 'sum'})
    cfg['ys'] = norm or [{'field': '', 'agg': 'sum'}]
    cfg['x'] = str(cfg.get('x') or '')
    cfg['series'] = str(cfg.get('series') or '')
    s = cfg.get('sort') if isinstance(cfg.get('sort'), dict) else {}
    cfg['sort'] = {'by': str(s.get('by') or ''), 'dir': 'asc' if s.get('dir') == 'asc' else 'desc'}
    try:
        cfg['topN'] = max(0, int(cfg.get('topN') or 0))
    except (TypeError, ValueError):
        cfg['topN'] = 0
    if not isinstance(cfg.get('style'), dict):
        cfg.pop('style', None)
    cfg.pop('y', None)
    cfg.pop('agg', None)
    return cfg


def _code_to_board_prompt(code: str, question: str) -> str:
    """把 agent 的「取数+绘图」代码转成看板配置 {native, cfg} 的提示词。"""
    return (
        '你是数据看板转换器。下面是一段在数据源上「取数+绘图」的 Python 代码'
        '(用 handler.query 取数,可能用 pandas 加工,用 pyecharts 画图)。请把它转换成可复用看板配置,输出 JSON:\n'
        '{"native": <一条只读、单条、可独立重跑的查询,返回图表所需数据集;SQL 源用 SQL 字符串,'
        'ES 用查询 DSL 对象,Mongo 用 pipeline 对象;尽量把聚合放进查询:GROUP BY / aggs / $group>,\n'
        ' "cfg": {"type": 图表类型(bar/hbar/bar_stack/line/area/pie/donut/rose/scatter/radar/funnel/gauge/kpi),'
        '"x": 维度列, "ys": [{"field": 度量列, "agg": "sum|avg|count|max|min|none"}], '
        '"series": 分组列或空串, "sort": {"by":"","dir":"desc"}, "topN": 0, "style": {"title": 标题}}}\n'
        '要求:native 必须**只读**、不依赖代码里的 pandas 中间变量、能独立重跑;'
        'cfg 里的列名必须是 native 结果的真实列名;若聚合已在查询里做,对应度量 agg 用 none。\n'
        '【聚合务必下推到 native,别只靠 pandas】常见写法示例:\n'
        '- SQL 分组求和:  native="SELECT city, SUM(amount) AS amount FROM t GROUP BY city ORDER BY amount DESC LIMIT 10",'
        ' cfg.x=city, ys=[{"field":"amount","agg":"none"}]\n'
        '- SQL 单指标:    native="SELECT MAX(price) AS max_price FROM t", cfg.type=kpi, ys=[{"field":"max_price","agg":"none"}]\n'
        '- ES 桶+指标:    native={"index":"idx","body":{"size":0,"aggs":{"by_ind":{"terms":{"field":"industry.keyword","size":10},'
        '"aggs":{"amt":{"sum":{"field":"amount"}}}}}}}(handler 会拍平成 by_ind/amt 两列),cfg.x=by_ind, ys=[{"field":"amt","agg":"none"}]\n'
        '- ES 单指标:     native={"index":"idx","body":{"size":0,"aggs":{"max_price":{"max":{"field":"price"}}}}},'
        ' cfg.type=kpi, ys=[{"field":"max_price","agg":"none"}]\n'
        '- Mongo 分组:    native={"collection":"c","pipeline":[{"$group":{"_id":"$city","amount":{"$sum":"$amount"}}}]},'
        ' cfg.x=_id, ys=[{"field":"amount","agg":"none"}]\n'
        '- Top-N 明细(非聚合):SQL 用 ORDER BY+LIMIT;ES 用 {"body":{"sort":[{"amount":"desc"}],"size":10,"_source":[...]}}。\n'
        '**只输出 JSON 本身,不要解释、不要 markdown 围栏。**\n'
        f'原始需求:{question or "(未知)"}\n代码:\n{code}'
    )


class DataQueryService:
    """数据查询/接口:基于模型 + 连接器。"""

    @classmethod
    async def _load(cls, db: AsyncSession, m_id: str) -> tuple[DataModel, Any]:
        m = await DataModelDao.get_by_id(db, m_id)
        if not m:
            raise ServiceException(message='数据模型不存在')
        ds = await DataSourceDao.get_by_code(db, m.datasource_code)
        if not ds:
            raise ServiceException(message='数据模型关联的数据源不存在')
        return m, _handler_from_ds(ds)

    @staticmethod
    def _check_fields(m: DataModel, filters: list[dict] | None) -> None:
        """字段白名单:filters 的 field 必须在模型已缓存字段里(防注入)。"""
        if not filters or not m.fields:
            return
        allowed = {f.get('name') for f in m.fields}
        bad = [r.get('field') for r in filters if r.get('field') not in allowed]
        if bad:
            raise ServiceException(message=f'非法字段: {bad}')

    @classmethod
    async def query(cls, db: AsyncSession, m_id: str, req: QueryReq) -> dict:
        """数据查询(不分页):native 或 filter,查出多少返回多少。"""
        m, handler = await cls._load(db, m_id)
        if req.native is not None:
            try:
                assert_readonly_sql(req.native, handler.family)  # 只读护栏(仅 SQL 文本族):拦截 DML/DDL
            except ValueError as e:
                raise ServiceException(message=str(e)) from None
            records = await run_in_threadpool(handler.query, req.native, None, req.limit)
        else:
            cls._check_fields(m, req.filters)
            if not handler.has(Capability.GEN_API):
                raise ServiceException(message=f'{handler.name} 不支持条件查询,请用原生查询')
            res = await run_in_threadpool(handler.search, m.object_name, req.filters, 1, req.limit or 5000)
            records = res['records']
        return {'records': json_safe_rows(records), 'total': len(records)}

    @classmethod
    async def sample_query(cls, db: AsyncSession, m_id: str) -> dict:
        """该模型的原生查询默认示例(前端预填,limit=100)。"""
        m, handler = await cls._load(db, m_id)
        return {'native': handler.sample_query(m.object_name or '', 100)}

    @classmethod
    async def ai_chart(cls, db: AsyncSession, m_id: str, question: str, columns: list[str]) -> dict:
        """自然语言 + 数据列 → 复用系统 LLM 生成 EchartsBuilder 图表配置(cfg)。走库内兜底 LLM,数据不外发。

        只需列名(前端由查询结果传入),字段合法性由前端 inferFields 二次校正;m_id 用于召回该源专属知识库。
        """
        if not (question or '').strip():
            raise ServiceException(message='请描述你想要的图表')
        cols = [str(c) for c in (columns or []) if c]
        if not cols:
            raise ServiceException(message='没有可用的数据列,请先执行查询')
        m = await DataModelDao.get_by_id(db, m_id) if m_id else None
        kb = await cls._kb_context(db, m, question) if m else ''
        kb_block = f'参考该数据源的业务知识(理解字段口径,据此选合适的列):\n{kb}\n\n' if kb else ''
        text = await _ai_complete(db, kb_block + _chart_cfg_prompt(cols, question))
        try:
            cfg = json.loads(_strip_fence(text))
        except (json.JSONDecodeError, ValueError) as e:
            raise ServiceException(message='AI 生成的图表配置不是合法 JSON,请换个说法重试') from e
        return _normalize_chart_cfg(cfg)

    @classmethod
    async def convert_code_to_board(cls, db: AsyncSession, datasource_code: str, code: str, question: str) -> dict:
        """把 agent 的取数+绘图代码经 LLM 转成 {native(可重跑只读查询), cfg}。转出后跑一次校验,失败自动纠错重试。"""
        if not (code or '').strip():
            raise ServiceException(message='无取数代码可转换')
        ds = await DataSourceDao.get_by_code(db, datasource_code)
        if not ds:
            raise ServiceException(message='数据源不存在')
        handler = _handler_from_ds(ds)
        base = _code_to_board_prompt(code, question)
        prompt, last_err = base, ''
        for _ in range(cls._QUERY_MAX_TRIES):
            text = await _ai_complete(db, prompt)
            try:
                obj = json.loads(_strip_fence(text))
            except (json.JSONDecodeError, ValueError) as e:
                last_err = f'输出不是合法 JSON:{short_err(e)}'
                prompt = base + f'\n\n【纠错】{last_err},请只输出 {{"native":..,"cfg":..}} 的 JSON。'
                continue
            native = obj.get('native')
            cfg = _normalize_chart_cfg(obj.get('cfg') or {})
            if isinstance(native, str):
                stmt = native.strip().rstrip(';')
                if not stmt.lower().lstrip().startswith(('select', 'with')):
                    last_err = f'native 不是只读查询:{stmt[:120]}'
                    prompt = base + f'\n\n【纠错】{last_err},请重出只读单查询。'
                    continue
                try:
                    assert_readonly_sql(stmt, handler.family)
                except ValueError as e:
                    last_err = str(e)
                    prompt = base + f'\n\n【纠错】native 被只读护栏拦截:{last_err},请重出只读查询。'
                    continue
            elif isinstance(native, dict):
                stmt = native
            else:
                last_err = '缺少 native'
                prompt = base + '\n\n【纠错】缺少 native 字段,请补全后重出 JSON。'
                continue
            try:
                await run_in_threadpool(handler.query, stmt, None, 50)  # 校验能跑通
            except Exception as e:
                last_err = short_err(e)
                prompt = base + f'\n\n【纠错】转换出的查询执行失败:{last_err}\n请修正 native 后重出 JSON。'
                continue
            return {'native': stmt, 'cfg': cfg}
        raise ServiceException(message=f'代码转看板失败(已自动纠错 {cls._QUERY_MAX_TRIES} 次):{last_err}')

    @classmethod
    async def _kb_context(cls, db: AsyncSession, m: Any, question: str) -> str:
        """取数前从该数据源的专属知识库召回业务知识(表义务/字段口径/QA),注入 prompt。无则空。"""
        try:
            from common.context import RequestContext
            from module_rag.agent_tools import search_knowledge_base

            ds = await DataSourceDao.get_by_code(db, m.datasource_code)
            if not ds:
                return ''
            tenant = RequestContext.get_effective_tenant_id()
            txt = await run_in_threadpool(search_knowledge_base, question, source_id=ds.id, tenant_id=tenant, top_k=5)
            return '' if (not txt or txt.startswith(('未找到', '未检索', '未指定'))) else txt
        except Exception:
            return ''

    # AI 取数自纠错:首次 + (N-1) 次纠错。执行报错→喂回错误+上次查询→让 LLM 修正,直到跑通或用尽。
    _QUERY_MAX_TRIES = 3

    @staticmethod
    def _is_es(handler: Any) -> bool:
        return getattr(handler, 'family', '') == 'search' or getattr(handler, 'name', '') == 'elasticsearch'

    @classmethod
    def _query_prompt(cls, handler: Any, object_name: str, cols: str, kb_block: str, question: str) -> str:
        """按源类型构造 AI 取数提示词(SQL 出只读 SELECT;ES 出 DSL JSON)。ai_query / prep_ai_query 共用。"""
        if cls._is_es(handler):
            fmt = (
                f'返回 Elasticsearch 查询 DSL 的 JSON,形如 '
                f'{{"index":"{object_name}","body":{{"query":{{...}},"size":50}}}};只输出 JSON,不要解释、不要 markdown 围栏。'
            )
        else:
            fmt = '写一条**只读 SELECT** 查询(单条语句、不要注释、不要 markdown 围栏、不要修改数据);只输出 SQL 本身。'
        return (
            kb_block + f'你是 {handler.name} 数据查询专家。表/索引:`{object_name}`,字段:\n{cols}\n\n'
            f'请根据下面的自然语言需求,{fmt}\n需求:{question}'
        )

    @classmethod
    def _prep_statement(cls, text: str, handler: Any) -> tuple[Any, str, str | None]:
        """LLM 产出文本 → 可执行语句 + 展示串 + 错误。SQL 校只读;ES 校 JSON。返回 (stmt, display, err)。"""
        raw = _strip_fence(text).strip()
        if cls._is_es(handler):
            try:
                dsl = json.loads(raw)
            except (json.JSONDecodeError, ValueError) as e:
                return None, raw, f'不是合法的 ES DSL JSON:{short_err(e)}'
            return dsl, raw, None
        sql = raw.rstrip(';')
        if not sql.lower().lstrip().startswith(('select', 'with')):
            return None, sql, '不是只读 SELECT/WITH 查询(疑似含写操作或非查询语句)'
        try:
            assert_readonly_sql(sql, handler.family)
        except ValueError as e:
            return None, sql, str(e)
        return sql, sql, None

    @staticmethod
    def _retry_prompt(base: str, prev: str, err: str) -> str:
        """把上次失败的查询 + 错误信息喂回,让 LLM 修正(Wren AI 式自纠错)。"""
        return (
            base + '\n\n【纠错】上一次生成的查询执行失败,请修正后重试。\n'
            f'上次查询:\n{prev}\n\n错误信息:\n{err}\n\n'
            '请仅输出修正后的查询本身,不要解释、不要 markdown 围栏。'
        )

    @classmethod
    async def ai_query(cls, db: AsyncSession, m_id: str, question: str, limit: int = 200) -> dict:
        """AI 取数:NL + 表结构(+专属知识库)→ 生成只读原生查询 → 执行,失败自动纠错重试。

        返回附带 attempts(总尝试次数)/corrected(是否经过纠错)/trace(失败尝试的查询+错误),便于前端提示。
        """
        m, handler = await cls._load(db, m_id)
        cols = '\n'.join(f'- {f["name"]} ({f.get("type", "")})' for f in (m.fields or []))
        kb = await cls._kb_context(db, m, question)
        kb_block = f'参考该数据源的业务知识(理解字段口径/表义务,可据此选字段写条件):\n{kb}\n\n' if kb else ''
        base = cls._query_prompt(handler, m.object_name, cols, kb_block, question)

        prompt = base
        last_err = ''
        trace: list[dict] = []
        for attempt in range(1, cls._QUERY_MAX_TRIES + 1):
            text = await _ai_complete(db, prompt)
            stmt, display, gen_err = cls._prep_statement(text, handler)
            if gen_err is None:
                try:
                    records = await run_in_threadpool(handler.query, stmt, None, limit)
                    return {
                        'query': display,
                        'records': json_safe_rows(records),
                        'total': len(records),
                        'attempts': attempt,
                        'corrected': attempt > 1,
                        'trace': trace,  # 之前失败的尝试(空=一次成功)
                    }
                except Exception as e:
                    last_err = short_err(e)
            else:
                last_err = gen_err
            trace.append({'attempt': attempt, 'query': display, 'error': last_err})
            prompt = cls._retry_prompt(base, display, last_err)
        raise ServiceException(
            message=f'AI 取数失败(已自动纠错 {cls._QUERY_MAX_TRIES} 次仍未跑通):{last_err}'
        )

    @classmethod
    async def prep_ai_query(cls, db: AsyncSession, m_id: str, question: str) -> tuple[dict, str]:
        """流式 AI 取数:解析模型配置 + 按源类型构造提示词(SQL 出 SELECT;ES 出 DSL JSON)。"""
        m, handler = await cls._load(db, m_id)
        cols = '\n'.join(f'- {f["name"]} ({f.get("type", "")})' for f in (m.fields or []))
        kb = await cls._kb_context(db, m, question)
        kb_block = f'参考该数据源的业务知识(理解字段口径/表义务):\n{kb}\n\n' if kb else ''
        prompt = cls._query_prompt(handler, m.object_name, cols, kb_block, question)
        cfg = await _ai_resolve_cfg(db)
        return cfg, prompt

    @classmethod
    async def search(cls, db: AsyncSession, m_id: str, req: SearchReq) -> dict:
        """数据接口(分页)。"""
        m, handler = await cls._load(db, m_id)
        if not handler.has(Capability.GEN_API):
            raise ServiceException(message=f'{handler.name} 不支持分页接口')
        cls._check_fields(m, req.filters)
        res = await run_in_threadpool(handler.search, m.object_name, req.filters, req.page, req.pagesize)
        if isinstance(res, dict) and 'records' in res:
            res['records'] = json_safe_rows(res['records'])
        return res


class EtlService:
    """ETL 调试:原生查询抽取预览 / 测试写入 / AI 生成查询与转换。"""

    @classmethod
    async def preview(cls, db: AsyncSession, req: Any) -> dict:
        """批量源按原生查询取样本;流式源抽 1 条事件;代码取数走沙箱跑 result。均支持逐行转换。"""
        if (getattr(req, 'mode', None) or '') == 'code':
            return await cls._preview_code(db, req)
        ds = await DataSourceDao.get_by_code(db, req.datasource_code)
        if not ds:
            raise ServiceException(message='数据源不存在')
        handler = _handler_from_ds(ds)

        try:
            if handler.has(Capability.READ):  # 批量源:原生查询
                native = req.native
                if not native or (isinstance(native, str) and not native.strip()):
                    raise ServiceException(message='请填写原生查询')
                try:
                    assert_readonly_sql(native, handler.family)  # 抽取预览同样只读(仅 SQL 文本族)
                except ValueError as e:
                    raise ServiceException(message=str(e)) from None
                limit = min(int(req.limit or 50), 200)
                rows = await run_in_threadpool(handler.query, native, None, limit)
            elif handler.has(Capability.STREAM):  # 流式源:有界抽 1 条
                stmt = stream_statement(req.object_name)
                rows = await run_in_threadpool(handler.query, stmt, None, 1)
            else:
                raise ServiceException(message=f'{handler.name} 不支持预览抽取')
        except ServiceException:
            raise
        except Exception as e:
            raise ServiceException(message=f'抽取失败:{short_err(e)}') from None

        transformed = None
        transform_log = ''
        if (req.transform_code or '').strip():
            transformed, transform_log = await run_in_threadpool(cls._apply_transform, req.transform_code, rows)
        cols = list((transformed or rows)[0].keys()) if (transformed or rows) else []
        return {
            'records': json_safe_rows(rows),
            'transformed': json_safe_rows(transformed),
            'columns': cols,
            'total': len(rows),
            'transformLog': transform_log,
        }

    @classmethod
    async def _preview_code(cls, db: AsyncSession, req: Any) -> dict:
        """代码取数预览:在沙箱跑用户代码产出 result(list[dict]),取样本。

        正式任务在 worker 跑(可访问任意外网);预览在沙箱(出网受白名单约束、隔离),用于安全调试。
        """
        from module_data import sandbox_client

        code = (req.code or '').strip()
        if not code:
            raise ServiceException(message='请填写取数代码(把结果赋值给 result)')
        if not sandbox_client.enabled():
            raise ServiceException(message='沙箱未启用,无法预览代码取数(保存后正式任务仍可在 worker 运行)')
        # 预解密所选数据源(沙箱无凭据,连接随请求注入,仅限所选源)
        dsmap: dict[str, dict] = {}
        for c in req.datasource_codes or []:
            ds = await DataSourceDao.get_by_code(db, c)
            if not ds:
                raise ServiceException(message=f'数据源不存在: {c}')
            dsmap[c] = {'source_type': ds.source_type, 'config': ds.config or {}, 'secrets': _decrypt_secrets(ds)}
        # 代码取数/爬虫预览较慢,沙箱超时放到 300s(与前端一致)
        res = await run_in_threadpool(sandbox_client.run_python_extract, code, dsmap, 'result', 300)
        if not res.get('success'):
            raise ServiceException(message=f'代码取数失败:{short_err(res.get("error") or "未知错误")}')
        rows = res.get('result')
        if isinstance(rows, dict) and 'value' in rows:  # 沙箱把 DataFrame 归一成 {type,value}
            rows = rows.get('value')
        if not isinstance(rows, list):
            raise ServiceException(message='代码未产出 list[dict]:请把结果赋值给变量 result')
        rows = rows[: min(int(req.limit or 50), 200)]
        transformed = None
        transform_log = res.get('stdout') or ''
        if (req.transform_code or '').strip():
            transformed, tlog = await run_in_threadpool(cls._apply_transform, req.transform_code, rows)
            transform_log = (transform_log + '\n' + tlog).strip() if tlog else transform_log
        cols = list((transformed or rows)[0].keys()) if (transformed or rows) else []
        return {
            'records': json_safe_rows(rows),
            'transformed': json_safe_rows(transformed),
            'columns': cols,
            'total': len(rows),
            'transformLog': transform_log,
        }

    @classmethod
    async def test_load(cls, db: AsyncSession, req: Any) -> dict:
        """把预览样本写入目标,验证装载配置(小批量真实写入)。"""
        ds = await DataSourceDao.get_by_code(db, req.datasource_code)
        if not ds:
            raise ServiceException(message='目标数据源不存在')
        handler = _handler_from_ds(ds)
        if not handler.has(Capability.WRITE):
            raise ServiceException(message=f'{handler.name} 不支持写入')
        if not req.records:
            raise ServiceException(message='没有可写入的样本,请先预览抽取数据')

        fmt = getattr(req, 'format', None) or 'csv'
        to_file = is_file_target(ds.family)

        def _write() -> Any:
            if to_file:  # 对象/文件存储:序列化为整对象写入 key=table
                return handler.write(serialize_records(req.records, fmt), req.table, mode=req.mode or 'append')
            return handler.write(
                req.records,
                req.table,
                mode=req.mode or 'append',
                dataset=req.dataset or 'public',
                pipeline_name=f'etl_test_{req.table}',
            )

        try:
            await run_in_threadpool(_write)
        except Exception as e:
            raise ServiceException(message=f'写入失败:{short_err(e)}') from None
        return {
            'written': len(req.records),
            'table': req.table,
            'dataset': req.dataset or 'public',
            'target': 'file' if to_file else 'table',
        }

    @classmethod
    async def ai_query(cls, db: AsyncSession, req: Any) -> dict:
        """AI 生成原生查询:NL + 源表结构 → 只读查询(提示词构造委托 ezdata.prompts)。"""
        _, prompt = await cls.prep_query(db, req)
        try:
            native = (await _ai_complete(db, prompt)).rstrip(';')
        except ServiceException:
            raise
        except Exception as e:
            raise ServiceException(message=f'AI 生成失败:{short_err(e)}') from None
        return {'native': native}

    @classmethod
    async def prep_query(cls, db: AsyncSession, req: Any) -> tuple[dict, str]:
        """流式/一次性生成共用:解析模型配置 + 构造查询提示词。"""
        ds = await DataSourceDao.get_by_code(db, req.datasource_code)
        if not ds:
            raise ServiceException(message='源数据源不存在')
        handler = _handler_from_ds(ds)
        prompt = await run_in_threadpool(ez_prompts.build_query_prompt, handler, req.object_names, req.question)
        cfg = await _ai_resolve_cfg(db)
        return cfg, prompt

    @classmethod
    async def ai_transform(cls, db: AsyncSession, req: Any) -> dict:
        """AI 生成逐行转换函数:NL + 字段 → transform(row)。"""
        _, prompt = await cls.prep_transform(db, req)
        try:
            code = await _ai_complete(db, prompt)
        except ServiceException:
            raise
        except Exception as e:
            raise ServiceException(message=f'AI 生成失败:{short_err(e)}') from None
        return {'code': code}

    @classmethod
    async def prep_transform(cls, db: AsyncSession, req: Any) -> tuple[dict, str]:
        """流式/一次性生成共用:解析模型配置 + 构造转换提示词(委托 ezdata.prompts)。"""
        prompt = ez_prompts.build_transform_prompt(req.columns, req.question)
        cfg = await _ai_resolve_cfg(db)
        return cfg, prompt

    @classmethod
    async def prep_extract_code(cls, db: AsyncSession, req: Any) -> tuple[dict, str]:
        """AI 生成取数代码(爬虫/任意取数):自然语言 → 产出 result(list[dict])的 Python(提示词委托 ezdata.prompts)。"""
        prompt = ez_prompts.build_extract_code_prompt(getattr(req, 'datasource_codes', None), req.question)
        cfg = await _ai_resolve_cfg(db)
        return cfg, prompt

    @staticmethod
    def _apply_transform(code: str, rows: list[dict]) -> tuple[list[dict], str]:
        """逐行执行 transform(row)->row,返回 (转换后列表, 日志)。

        沙箱开启(SANDBOX_ENABLED)时把「数据行 + 代码」发给独立沙箱容器执行(不传任何凭据),
        日志随响应回传;沙箱未开启时本地 exec 兜底(仅可信/单机调试)。
        """
        from module_data import sandbox_client

        if sandbox_client.enabled():
            res = sandbox_client.transform_rows(code, rows)
            if not res.get('success'):
                raise ServiceException(message=f'转换执行失败:{res.get("error") or "未知错误"}')
            return res.get('transformed') or [], res.get('output') or ''

        # 本地兜底:沙箱未启用
        ns: dict[str, Any] = {}
        exec(compile(code, '<etl-transform>', 'exec'), ns)
        fn = ns.get('transform')
        if not callable(fn):
            raise ServiceException(message='转换代码必须定义 transform(row) 函数')
        out: list[dict] = []
        for r in rows:
            try:
                out.append(fn(dict(r)))
            except Exception as e:
                out.append({'_transform_error': str(e), **r})
        return out, ''


class OpenDataService:
    """公开数据接口(免登录,apikey 校验 + 查询串筛选 + 分页)。"""

    @classmethod
    async def public_query(cls, db: AsyncSession, model_code: str, params: dict) -> dict:
        from sqlalchemy import select

        from common.context import RequestContext
        from ezdata.utils.query import parse_query_params
        from module_apitoken.service.api_token_service import ApiTokenService
        from module_data.entity.do.data_do import DataModel as DataModelDO

        apikey = params.get('apikey') or params.get('api_key')
        tk = await ApiTokenService.validate(db, apikey, 'data_api', model_code)
        # 对外接口无登录上下文:据 token 绑定的租户建立租户上下文,后续模型/数据源查询被租户隔离
        if tk.tenant_id is None:
            raise ServiceException(message='apikey 未绑定租户,禁止访问')
        RequestContext.set_current_tenant_id(tk.tenant_id)

        m = (await db.execute(select(DataModelDO).where(DataModelDO.code == model_code))).scalars().first()
        if not m:
            raise ServiceException(message='数据模型不存在')
        ds = await DataSourceDao.get_by_code(db, m.datasource_code)
        if not ds:
            raise ServiceException(message='数据源不存在')
        handler = _handler_from_ds(ds)
        if not handler.has(Capability.GEN_API):
            raise ServiceException(message=f'{handler.name} 不支持数据接口')

        filters = parse_query_params(params)
        page = int(params.get('page', 1))
        pagesize = min(int(params.get('pagesize', 20)), 200)  # 对外强制上限
        return await run_in_threadpool(handler.search, m.object_name, filters, page, pagesize)


class AnalysisTemplateService:
    """数据分析模板:保存/复用「取数 + 图表配置」。"""

    @classmethod
    async def get_list(cls, db: AsyncSession, model_id: str | None = None) -> list[AnalysisTemplateVo]:
        rows = await AnalysisTemplateDao.get_list(db, model_id)
        return [AnalysisTemplateVo.model_validate(r) for r in rows]

    @classmethod
    async def save(cls, db: AsyncSession, vo: AnalysisTemplateVo, operator: str) -> str:
        if not (vo.name or '').strip():
            raise ServiceException(message='请填写模板名称')
        data = {
            'name': vo.name,
            'model_id': vo.model_id,
            'model_name': vo.model_name,
            'query': vo.query,
            'chart_spec': vo.chart_spec,
            'remark': vo.remark,
        }
        if vo.id:
            data['update_by'] = operator
            await AnalysisTemplateDao.edit(db, vo.id, data)
            tid = vo.id
        else:
            data['id'] = uuid.uuid4().hex
            data['create_by'] = operator
            await AnalysisTemplateDao.add(db, data)
            tid = data['id']
        await db.commit()
        return tid

    @classmethod
    async def save_from_chart(
        cls,
        db: AsyncSession,
        name: str,
        datasource_code: str,
        native: Any,
        chart_spec: Any,
        remark: str,
        operator: str,
    ) -> str:
        """对话 agent 图表存为看板:get-or-create custom_query 模型 → 存模板(取数 native + cfg)。"""
        if not (name or '').strip():
            raise ServiceException(message='请填写看板名称')
        model_id = await DataModelService.ensure_custom_query_model(db, datasource_code, operator)
        m = await DataModelDao.get_by_id(db, model_id)
        vo = AnalysisTemplateVo(
            name=name.strip(),
            model_id=model_id,
            model_name=(m.name if m else ''),
            query={'type': 'native', 'native': native},
            chart_spec=_normalize_chart_cfg(chart_spec) if isinstance(chart_spec, dict) else chart_spec,
            remark=remark or 'AI 对话生成',
        )
        return await cls.save(db, vo, operator)

    @classmethod
    async def save_from_code(
        cls,
        db: AsyncSession,
        name: str,
        datasource_code: str,
        code: str,
        question: str,
        remark: str,
        operator: str,
    ) -> str:
        """代码取数的图表存为看板:LLM 把代码转成 {native, cfg} → get-or-create custom_query 模型 → 存模板。"""
        if not (name or '').strip():
            raise ServiceException(message='请填写看板名称')
        res = await DataQueryService.convert_code_to_board(db, datasource_code, code, question)
        model_id = await DataModelService.ensure_custom_query_model(db, datasource_code, operator)
        m = await DataModelDao.get_by_id(db, model_id)
        vo = AnalysisTemplateVo(
            name=name.strip(),
            model_id=model_id,
            model_name=(m.name if m else ''),
            query={'type': 'native', 'native': res['native']},
            chart_spec=res['cfg'],
            remark=remark or 'AI 对话·代码转看板',
        )
        return await cls.save(db, vo, operator)

    @classmethod
    async def delete(cls, db: AsyncSession, ids: list[str]) -> None:
        await AnalysisTemplateDao.remove(db, [i for i in ids if i])
        await db.commit()
