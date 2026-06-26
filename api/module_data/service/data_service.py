import json
import uuid
from datetime import datetime
from typing import Any

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_data.dao.data_dao import DataModelDao, DataSourceDao
from module_data.entity.do.data_do import DataModel, DataSource
from module_data.entity.vo.data_vo import (
    DataModelQuery,
    DataModelVo,
    DataSourceQuery,
    DataSourceVo,
    QueryReq,
    SearchReq,
    TestConnReq,
)
from module_data.etl_util import assert_readonly_sql, is_file_target, serialize_records, short_err, stream_statement
from module_data.handlers import Capability, connection_schema, create_handler, get_handler_cls, list_source_types
from module_data.query import OPERATORS
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


async def _ai_resolve_cfg(db: AsyncSession) -> dict:
    """解析系统内 AI 模型配置:优先库内启用模型,无则回退环境变量兜底模型(LLM_*)。"""
    from sqlalchemy import select  # noqa: PLC0415

    from config.env import AiConfig  # noqa: PLC0415
    from module_ai.entity.do.ai_model_do import AiModels  # noqa: PLC0415

    mc = (await db.execute(
        select(AiModels).where(AiModels.status == '0').order_by(AiModels.model_sort))).scalars().first()
    if mc:  # 库内启用模型(api_key 为 AES 密文)
        return dict(provider=mc.provider, model_code=mc.model_code, model_name=mc.model_name,
                    api_key=CryptoUtil.decrypt(mc.api_key) if mc.api_key else None,
                    base_url=mc.base_url, max_tokens=mc.max_tokens or 1024)
    if AiConfig.enabled:  # 环境变量兜底模型(api_key 明文)
        return dict(provider=AiConfig.provider, model_code=AiConfig.llm_model, model_name=None,
                    api_key=AiConfig.llm_api_key, base_url=AiConfig.llm_url or None,
                    max_tokens=AiConfig.llm_max_tokens or 1024)
    raise ServiceException(
        message='未配置可用 AI 模型:请在「AI 模型管理」启用一个,或在环境变量配置兜底模型(LLM_TYPE/LLM_MODEL/LLM_API_KEY[/LLM_URL])')


def _strip_fence(text: str) -> str:
    """去掉 markdown ```lang ... ``` 代码围栏。"""
    t = (text or '').strip()
    if t.startswith('```'):
        t = t.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
    return t


async def _ai_complete(db: AsyncSession, prompt: str) -> str:
    """一次性补全并返回文本(自动去围栏)。"""
    from utils.ai_util import AiUtil  # noqa: PLC0415

    cfg = await _ai_resolve_cfg(db)

    def _run() -> str:
        from agno.agent import Agent  # noqa: PLC0415

        out = Agent(model=AiUtil.get_model_from_factory(**cfg)).run(prompt)
        return _strip_fence(getattr(out, 'content', None) or str(out))

    return await run_in_threadpool(_run)


def _ai_stream(cfg: dict, prompt: str):
    """同步生成器:流式产出文本增量,供 StreamingResponse 使用(围栏由前端采用时再去除)。"""
    from agno.agent import Agent  # noqa: PLC0415

    from utils.ai_util import AiUtil  # noqa: PLC0415
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
    except Exception as e:  # noqa: BLE001 把错误也流式回去,前端可见
        yield f'\n[生成出错] {short_err(e)}'


class DataMetaService:
    """静态元信息:源类型 / 连接 schema / 操作符。"""

    @staticmethod
    def source_types() -> list[dict]:
        # 转 camelCase,对齐前端/接口约定(source_type -> sourceType)
        return [
            {'sourceType': t['source_type'], 'title': t['title'],
             'family': t['family'], 'capabilities': t['capabilities']}
            for t in list_source_types()
        ]

    @staticmethod
    def connection_schema(source_type: str) -> dict:
        return connection_schema(source_type)

    @staticmethod
    def operators() -> list[dict]:
        return OPERATORS


class DataSourceService:
    """数据源服务。"""

    @classmethod
    async def get_list(cls, db: AsyncSession, q: DataSourceQuery, is_page: bool = False) -> Any:
        result = await DataSourceDao.get_list(db, q, is_page)
        for row in (result.rows if is_page else result):
            row['secrets'] = None  # 列表不回密文
        return result

    @classmethod
    async def detail(cls, db: AsyncSession, ds_id: str) -> DataSourceVo:
        ds = await DataSourceDao.get_by_id(db, ds_id)
        if not ds:
            raise ServiceException(message='数据源不存在')
        # 不读 DO 的密文 secrets,手动构造 + 脱敏
        vo = DataSourceVo(
            id=ds.id, name=ds.name, code=ds.code, source_type=ds.source_type, family=ds.family,
            config=ds.config, status=ds.status, last_test_at=ds.last_test_at, remark=ds.remark,
            create_by=ds.create_by, create_time=ds.create_time, update_by=ds.update_by, update_time=ds.update_time,
        )
        secret_fields = get_handler_cls(ds.source_type).secret_fields() if ds.source_type else []
        vo.secrets = dict.fromkeys(secret_fields, MASK) if secret_fields else None
        return vo

    @classmethod
    async def add(cls, db: AsyncSession, vo: DataSourceVo, operator: str) -> CrudResponseModel:
        try:
            obj = {
                'id': uuid.uuid4().hex,
                'name': vo.name, 'code': vo.code or uuid.uuid4().hex[:8],
                'source_type': vo.source_type,
                'family': get_handler_cls(vo.source_type).family if vo.source_type else None,
                'config': vo.config or {},
                'secrets': CryptoUtil.encrypt(json.dumps(vo.secrets)) if vo.secrets else None,
                'status': 'untested', 'remark': vo.remark,
                'create_by': operator, 'create_time': datetime.now(),
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
            await DataSourceDao.edit(db, req.id, {
                'status': 'ok' if result.success else 'failed', 'last_test_at': datetime.now()})
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
        return DataModelVo.model_validate(m)

    @classmethod
    async def add(cls, db: AsyncSession, vo: DataModelVo, operator: str) -> CrudResponseModel:
        try:
            obj = vo.model_dump(exclude={'id', 'create_time', 'update_time', 'create_by', 'update_by'})
            obj.update(id=uuid.uuid4().hex, code=vo.code or uuid.uuid4().hex[:8],
                       create_by=operator, create_time=datetime.now())
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
        return {'records': records, 'total': len(records)}

    @classmethod
    async def sample_query(cls, db: AsyncSession, m_id: str) -> dict:
        """该模型的原生查询默认示例(前端预填,limit=100)。"""
        m, handler = await cls._load(db, m_id)
        return {'native': handler.sample_query(m.object_name or '', 100)}

    @classmethod
    async def _kb_context(cls, db: AsyncSession, m: Any, question: str) -> str:
        """取数前从该数据源的专属知识库召回业务知识(表义务/字段口径/QA),注入 prompt。无则空。"""
        try:
            from common.context import RequestContext  # noqa: PLC0415
            from module_rag.agent_tools import search_knowledge_base  # noqa: PLC0415
            ds = await DataSourceDao.get_by_code(db, m.datasource_code)
            if not ds:
                return ''
            tenant = RequestContext.get_effective_tenant_id()
            txt = await run_in_threadpool(search_knowledge_base, question,
                                          source_id=ds.id, tenant_id=tenant, top_k=5)
            return '' if (not txt or txt.startswith(('未找到', '未检索', '未指定'))) else txt
        except Exception:  # noqa: BLE001 KB 不影响取数主流程
            return ''

    @classmethod
    async def ai_query(cls, db: AsyncSession, m_id: str, question: str, limit: int = 200) -> dict:
        """AI 取数:NL + 表结构(+专属知识库)→ 生成只读原生查询 → 执行。复用 ai_models 配置 + Agno。"""
        m, handler = await cls._load(db, m_id)
        cols = '\n'.join(f"- {f['name']} ({f.get('type', '')})" for f in (m.fields or []))
        kb = await cls._kb_context(db, m, question)
        kb_block = f'参考该数据源的业务知识(理解字段口径/表义务,可据此选字段写条件):\n{kb}\n\n' if kb else ''
        prompt = (
            kb_block +
            f'你是 {handler.name} 数据库的 SQL 专家。表名:`{m.object_name}`,字段:\n{cols}\n\n'
            f'请根据下面的自然语言需求,写一条**只读 SELECT** 查询(单条语句、不要注释、不要 markdown 代码块、'
            f'不要修改数据)。只输出 SQL 本身:\n需求:{question}'
        )
        sql = (await _ai_complete(db, prompt)).rstrip(';')
        if not sql.lower().lstrip().startswith('select'):
            raise ServiceException(message=f'AI 生成的不是只读查询,已拦截:{sql[:100]}')
        records = await run_in_threadpool(handler.query, sql, None, limit)
        return {'query': sql, 'records': records, 'total': len(records)}

    @classmethod
    async def prep_ai_query(cls, db: AsyncSession, m_id: str, question: str) -> tuple[dict, str]:
        """流式 AI 取数:解析模型配置 + 按源类型构造提示词(SQL 出 SELECT;ES 出 DSL JSON)。"""
        m, handler = await cls._load(db, m_id)
        cols = '\n'.join(f"- {f['name']} ({f.get('type', '')})" for f in (m.fields or []))
        if getattr(handler, 'family', '') == 'search' or handler.name == 'elasticsearch':
            fmt = (f'返回 Elasticsearch 查询 DSL 的 JSON,形如 '
                   f'{{"index":"{m.object_name}","body":{{"query":{{...}},"size":50}}}};只输出 JSON,不要解释、不要 markdown 围栏。')
        else:
            fmt = '写一条**只读 SELECT** 查询(单条语句、不要注释、不要 markdown 围栏);只输出 SQL 本身。'
        kb = await cls._kb_context(db, m, question)
        kb_block = f'参考该数据源的业务知识(理解字段口径/表义务):\n{kb}\n\n' if kb else ''
        prompt = (
            kb_block +
            f'你是 {handler.name} 数据查询专家。表/索引:`{m.object_name}`,字段:\n{cols}\n\n'
            f'请根据下面的自然语言需求,{fmt}\n需求:{question}'
        )
        cfg = await _ai_resolve_cfg(db)
        return cfg, prompt

    @classmethod
    async def search(cls, db: AsyncSession, m_id: str, req: SearchReq) -> dict:
        """数据接口(分页)。"""
        m, handler = await cls._load(db, m_id)
        if not handler.has(Capability.GEN_API):
            raise ServiceException(message=f'{handler.name} 不支持分页接口')
        cls._check_fields(m, req.filters)
        return await run_in_threadpool(handler.search, m.object_name, req.filters, req.page, req.pagesize)


class EtlService:
    """ETL 调试:原生查询抽取预览 / 测试写入 / AI 生成查询与转换。"""

    @classmethod
    async def preview(cls, db: AsyncSession, req: Any) -> dict:
        """批量源按原生查询取样本;流式源抽 1 条事件。均支持逐行转换。"""
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
        except Exception as e:  # noqa: BLE001 抽取报错截断后回给前端
            raise ServiceException(message=f'抽取失败:{short_err(e)}') from None

        transformed = None
        transform_log = ''
        if (req.transform_code or '').strip():
            transformed, transform_log = await run_in_threadpool(cls._apply_transform, req.transform_code, rows)
        cols = list((transformed or rows)[0].keys()) if (transformed or rows) else []
        return {'records': rows, 'transformed': transformed, 'columns': cols,
                'total': len(rows), 'transformLog': transform_log}

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
            return handler.write(req.records, req.table, mode=req.mode or 'append',
                                 dataset=req.dataset or 'public', pipeline_name=f'etl_test_{req.table}')

        try:
            await run_in_threadpool(_write)
        except Exception as e:  # noqa: BLE001 写入报错截断后回给前端
            raise ServiceException(message=f'写入失败:{short_err(e)}') from None
        return {'written': len(req.records), 'table': req.table,
                'dataset': req.dataset or 'public', 'target': 'file' if to_file else 'table'}

    # 不指定主表时,最多喂给 AI 的表数(保护 token,大库会截断并提示)
    SCHEMA_TABLE_CAP = 40

    @classmethod
    async def ai_query(cls, db: AsyncSession, req: Any) -> dict:
        """AI 生成原生查询:NL + 源表结构 → 只读查询。

        - 选了若干表:只喂这些表的结构(支持连表 join);
        - 不选表:喂全库表结构,大库截断到 SCHEMA_TABLE_CAP 张并提示。
        """
        _, prompt = await cls.prep_query(db, req)
        try:
            native = (await _ai_complete(db, prompt)).rstrip(';')
        except ServiceException:
            raise
        except Exception as e:  # noqa: BLE001 模型调用报错截断
            raise ServiceException(message=f'AI 生成失败:{short_err(e)}') from None
        return {'native': native}

    @classmethod
    async def prep_query(cls, db: AsyncSession, req: Any) -> tuple[dict, str]:
        """流式/一次性生成共用:解析模型配置 + 构造查询提示词。"""
        ds = await DataSourceDao.get_by_code(db, req.datasource_code)
        if not ds:
            raise ServiceException(message='源数据源不存在')
        handler = _handler_from_ds(ds)
        prompt = await run_in_threadpool(cls._query_prompt, handler, req.object_names, req.question)
        cfg = await _ai_resolve_cfg(db)
        return cfg, prompt

    # native 为 SQL 文本的源族(出 SELECT);其余非 api 源统一走"原生查询"(各用各自查询语法)
    _SQL_FAMILIES = {'rdbms', 'timeseries'}

    @classmethod
    def _query_prompt(cls, handler: Any, object_names: list[str] | None, question: str) -> str:
        family = getattr(handler, 'family', '')
        # api 族(akshare/ccxt 等):原生查询是"接口函数调用",出 {func, params} JSON
        if family == 'api':
            return cls._api_query_prompt(handler, object_names, question)
        # SQL 文本族(mysql/pg/tdengine…):出只读 SELECT
        if family in cls._SQL_FAMILIES:
            schema_ctx = cls._schema_context(handler, object_names)
            return (
                f'你是 {handler.name} 数据库的查询专家。{schema_ctx}'
                f'请根据下面的自然语言需求,写一条**只读**抽取查询(可按需连表 join;单条语句、不要注释、不要 markdown 代码块)。'
                f'只输出查询本身:\n需求:{question}'
            )
        # 其余非 SQL 源(ES/Mongo/图/KV/向量…):统一"原生查询",让模型用该源自身的查询语法/DSL
        return cls._native_query_prompt(handler, object_names, question)

    @classmethod
    def _api_query_prompt(cls, handler: Any, object_names: list[str] | None, question: str) -> str:
        """api 族(akshare/ccxt)取数提示词:其"查询"是调用一个数据接口函数,需输出 {func, params} JSON。"""
        labels = handler.table_labels() if hasattr(handler, 'table_labels') else {}
        names = [n for n in (object_names or []) if n]
        if not names:  # 没选函数:给出白名单里前若干个候选,让模型自行挑选
            try:
                names = [t for t in handler.list_tables()][: cls.SCHEMA_TABLE_CAP]
            except Exception:  # noqa: BLE001
                names = list(labels.keys())[: cls.SCHEMA_TABLE_CAP]
        blocks: list[str] = []
        for t in names:
            desc = labels.get(t, '')
            doc = ''
            if hasattr(handler, 'describe'):
                try:
                    doc = (handler.describe(t) or '').strip()
                except Exception:  # noqa: BLE001
                    doc = ''
            block = f'- {t}' + (f':{desc}' if desc else '')
            if doc:
                block += '\n' + '\n'.join('    ' + ln for ln in doc.splitlines()[:30])
            blocks.append(block)
        funcs = '\n'.join(blocks) or '(无可用接口信息)'
        return (
            f'你是 {handler.name} 接口数据源的取数专家。该数据源的"原生查询"**不是 SQL**,'
            f'而是调用一个数据接口函数(函数名 + 参数)。\n'
            f'可用接口函数及其参数说明:\n{funcs}\n\n'
            f'请根据下面的需求,选最合适的函数并填好参数。**只输出一行 JSON 对象**'
            f'(不要 SQL、不要注释、不要 markdown 代码块):\n'
            f'{{"func": "函数名", "params": {{"参数名": "值"}}}}\n'
            f'无参数时 params 写 {{}}。参数取值参考上面的函数说明。\n需求:{question}'
        )

    @classmethod
    def _native_query_prompt(cls, handler: Any, object_names: list[str] | None, question: str) -> str:
        """非 SQL/非 api 源(ES/Mongo/图/KV 等)的统一"原生查询"提示词。

        不为每种源写一套:只声明数据源类型 + 字段 + 该源原生查询的样例结构(handler.sample_query 自描述),
        让模型用该源自身的查询语法/DSL 编写——模型本就知道各系统的查询语言,明确要求即可。
        """
        schema_ctx = cls._schema_context(handler, object_names)
        names = [n for n in (object_names or []) if n]
        example = ''
        if names and hasattr(handler, 'sample_query'):
            try:
                sq = handler.sample_query(names[0], 50)
                example = f'该数据源原生查询的结构形如(请在此基础上按需求改写):\n{json.dumps(sq, ensure_ascii=False)}\n'
            except Exception:  # noqa: BLE001
                example = ''
        return (
            f'你是 {handler.name} 数据查询专家。{schema_ctx}'
            f'该数据源的"原生查询"**不是 SQL**,请用 {handler.name} 自身的查询语法/DSL 编写。\n'
            f'{example}'
            f'请根据下面的需求写一条**只读**查询,**只输出查询本身**'
            f'(按该源语法,通常是 JSON/DSL;不要 SQL、不要注释、不要 markdown 代码块):\n需求:{question}'
        )

    @classmethod
    def _schema_context(cls, handler: Any, object_names: list[str] | None) -> str:
        """构造喂给 AI 的表结构上下文(同步,放线程池调用)。"""
        if not handler.has(Capability.SCHEMA):
            return ''
        names = [n for n in (object_names or []) if n]
        if names:  # 选了表:只喂这些表(1 张或多张,支持连表)
            parts = cls._tables_schema(handler, names)
            if not parts:
                return ''
            label = '相关表结构(可连表查询):' if len(parts) > 1 else '主表字段:'
            return f'{label}\n' + '\n'.join(parts) + '\n\n'
        # 没选表:喂全库结构(滤掉 dlt 内部表),大库截断
        try:
            tables = [t for t in handler.list_tables() if not t.startswith('_dlt')]
        except Exception:  # noqa: BLE001
            return ''
        shown = tables[: cls.SCHEMA_TABLE_CAP]
        parts = cls._tables_schema(handler, shown)
        if not parts:
            return ''
        note = (f'(全库共 {len(tables)} 张表,仅列出前 {len(shown)} 张;'
                f'如需其它表请在主表里指定)\n') if len(tables) > len(shown) else ''
        return '可用表结构(可连表查询):\n' + note + '\n'.join(parts) + '\n\n'

    @staticmethod
    def _tables_schema(handler: Any, tables: list[str]) -> list[str]:
        """逐表 introspect,返回 ['表 `t`: col type, ...', ...],取不到的表跳过。"""
        parts = []
        for t in tables:
            try:
                cols = handler.get_columns(t)
                parts.append(f'表 `{t}`: ' + ', '.join(f'{c.name} {c.type}' for c in cols))
            except Exception:  # noqa: BLE001
                continue
        return parts

    @classmethod
    async def ai_transform(cls, db: AsyncSession, req: Any) -> dict:
        """AI 生成逐行转换函数:NL + 字段 → transform(row)。"""
        _, prompt = await cls.prep_transform(db, req)
        try:
            code = await _ai_complete(db, prompt)
        except ServiceException:
            raise
        except Exception as e:  # noqa: BLE001 模型调用报错截断
            raise ServiceException(message=f'AI 生成失败:{short_err(e)}') from None
        return {'code': code}

    @classmethod
    async def prep_transform(cls, db: AsyncSession, req: Any) -> tuple[dict, str]:
        """流式/一次性生成共用:解析模型配置 + 构造转换提示词。"""
        cols = ('可用字段:' + ', '.join(req.columns) + '\n\n') if req.columns else ''
        prompt = (
            f'你是 Python 数据处理专家。{cols}'
            f'请根据需求写一个函数 `def transform(row):`,入参 row 是一条记录(dict),返回处理后的 dict。'
            f'只输出函数代码本身(不要注释外的解释、不要 markdown 代码块):\n需求:{req.question}'
        )
        cfg = await _ai_resolve_cfg(db)
        return cfg, prompt

    @staticmethod
    def _apply_transform(code: str, rows: list[dict]) -> tuple[list[dict], str]:
        """逐行执行 transform(row)->row,返回 (转换后列表, 日志)。

        沙箱开启(SANDBOX_ENABLED)时把「数据行 + 代码」发给独立沙箱容器执行(不传任何凭据),
        日志随响应回传;沙箱未开启时本地 exec 兜底(仅可信/单机调试)。
        """
        from module_data import sandbox_client  # noqa: PLC0415

        if sandbox_client.enabled():
            res = sandbox_client.transform_rows(code, rows)
            if not res.get('success'):
                raise ServiceException(message=f'转换执行失败:{res.get("error") or "未知错误"}')
            return res.get('transformed') or [], res.get('output') or ''

        # 本地兜底:沙箱未启用
        ns: dict[str, Any] = {}
        exec(compile(code, '<etl-transform>', 'exec'), ns)  # noqa: S102 内部调试用途(沙箱未启用时)
        fn = ns.get('transform')
        if not callable(fn):
            raise ServiceException(message='转换代码必须定义 transform(row) 函数')
        out: list[dict] = []
        for r in rows:
            try:
                out.append(fn(dict(r)))
            except Exception as e:  # noqa: BLE001 预览容错:逐行报告
                out.append({'_transform_error': str(e), **r})
        return out, ''


class OpenDataService:
    """公开数据接口(免登录,apikey 校验 + 查询串筛选 + 分页)。"""

    @classmethod
    async def public_query(cls, db: AsyncSession, model_code: str, params: dict) -> dict:
        from sqlalchemy import select  # noqa: PLC0415

        from module_apitoken.service.api_token_service import ApiTokenService  # noqa: PLC0415
        from module_data.entity.do.data_do import DataModel as DataModelDO  # noqa: PLC0415
        from module_data.query import parse_query_params  # noqa: PLC0415

        apikey = params.get('apikey') or params.get('api_key')
        await ApiTokenService.validate(db, apikey, 'data_api', model_code)

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
