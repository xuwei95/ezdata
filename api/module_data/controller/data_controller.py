from typing import Annotated

from fastapi import Path, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_data.entity.vo.data_vo import (
    AiQueryReq,
    AnalysisTemplateVo,
    DashboardVo,
    DataModelQuery,
    DataModelVo,
    DataSourceQuery,
    DataSourceVo,
    EtlAiExtractReq,
    EtlAiQueryReq,
    EtlAiTransformReq,
    EtlPreviewReq,
    EtlTestLoadReq,
    QueryReq,
    SearchReq,
    TestConnReq,
)
from module_data.service.data_service import (
    AnalysisTemplateService,
    DashboardService,
    DataMetaService,
    DataModelService,
    DataQueryService,
    DataSourceService,
    EtlService,
    _ai_stream,
)
from utils.response_util import ResponseUtil

data_controller = APIRouterPro(prefix='/data', order_num=30, tags=['数据管理'], dependencies=[PreAuthDependency()])


# ---------------- 元信息 ----------------
@data_controller.get(
    '/source/types', summary='可用数据源类型 + 能力', dependencies=[UserInterfaceAuthDependency('data:source:list')]
)
async def source_types() -> Response:
    return ResponseUtil.success(data=DataMetaService.source_types())


@data_controller.get(
    '/source/schema/{source_type}',
    summary='连接参数 JSON Schema',
    dependencies=[UserInterfaceAuthDependency('data:source:list')],
)
async def source_schema(source_type: Annotated[str, Path()]) -> Response:
    return ResponseUtil.success(data=DataMetaService.connection_schema(source_type))


@data_controller.get(
    '/source/type-icon/{source_type}',
    summary='数据源类型品牌图标(SVG 文本)',
    dependencies=[UserInterfaceAuthDependency('data:source:list')],
)
async def source_type_icon(source_type: Annotated[str, Path()]) -> Response:
    return ResponseUtil.success(data=DataMetaService.source_type_icon(source_type))


@data_controller.get(
    '/operators', summary='过滤操作符目录', dependencies=[UserInterfaceAuthDependency('data:source:list')]
)
async def operators() -> Response:
    return ResponseUtil.success(data=DataMetaService.operators())


# ---------------- 数据源 CRUD ----------------
@data_controller.get(
    '/source/list',
    summary='数据源分页列表',
    response_model=PageResponseModel[DataSourceVo],
    dependencies=[UserInterfaceAuthDependency('data:source:list')],
)
async def source_list(
    request: Request,
    q: Annotated[DataSourceQuery, Query()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(model_content=await DataSourceService.get_list(db, q, is_page=True))


@data_controller.get(
    '/source/info/{ds_id}',
    summary='数据源详情(密钥脱敏)',
    dependencies=[UserInterfaceAuthDependency('data:source:list')],
)
async def source_info(ds_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DataSourceService.detail(db, ds_id))


@data_controller.post('/source', summary='新增数据源', dependencies=[UserInterfaceAuthDependency('data:source:add')])
async def source_add(
    request: Request,
    vo: DataSourceVo,
    db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await DataSourceService.add(db, vo, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


@data_controller.put('/source', summary='修改数据源', dependencies=[UserInterfaceAuthDependency('data:source:edit')])
async def source_edit(
    request: Request,
    vo: DataSourceVo,
    db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await DataSourceService.edit(db, vo, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


@data_controller.delete(
    '/source/{ids}', summary='删除数据源', dependencies=[UserInterfaceAuthDependency('data:source:remove')]
)
async def source_delete(ids: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    r = await DataSourceService.delete(db, ids)
    return ResponseUtil.success(msg=r.message)


@data_controller.post(
    '/source/test', summary='测试连接', dependencies=[UserInterfaceAuthDependency('data:source:list')]
)
async def source_test(req: TestConnReq, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DataSourceService.test_connection(db, req))


@data_controller.post(
    '/source/{ds_id}/sync-catalog',
    summary='同步该数据源到目录检索索引(异步 worker 任务)',
    dependencies=[UserInterfaceAuthDependency('data:source:edit')],
)
async def source_sync_catalog(
    ds_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]
) -> Response:
    from module_ai.tools.catalog_index import CatalogRetrievalService

    if not CatalogRetrievalService.available():
        return ResponseUtil.failure(msg='未配置 embedding,目录检索索引不可用')
    ds = await DataSourceService.detail(db, ds_id)
    if not ds or not ds.code:
        return ResponseUtil.failure(msg='数据源不存在')
    # 投递到 Celery worker 异步执行(大库 embedding 可能耗时,不阻塞 Web)
    from config.celery_app import celery_app

    r = celery_app.send_task('module_data.sync_catalog_index', args=[ds.code], queue='default')
    return ResponseUtil.success(msg=f'已提交同步任务到 worker(实例 {r.id}),完成后该源的表即可被 AI 按问题检索')


@data_controller.get(
    '/source/{ds_id}/tables', summary='列出表/索引/集合', dependencies=[UserInterfaceAuthDependency('data:source:list')]
)
async def source_tables(ds_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DataSourceService.list_tables(db, ds_id))


@data_controller.get(
    '/source/{ds_id}/columns', summary='字段结构', dependencies=[UserInterfaceAuthDependency('data:source:list')]
)
async def source_columns(
    ds_id: Annotated[str, Path()],
    table: Annotated[str, Query()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DataSourceService.get_columns(db, ds_id, table))


@data_controller.post(
    '/source/{ds_id}/analyze-context/stream',
    summary='AI 解析数据源业务上下文(流式)',
    dependencies=[UserInterfaceAuthDependency('data:source:edit')],
)
async def source_analyze_context_stream(
    ds_id: Annotated[str, Path()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> StreamingResponse:
    """读该数据源的现有描述 + 整体结构,流式生成业务上下文初稿(供前端「应用到描述」复写)。"""
    cfg, prompt = await DataSourceService.prep_analyze_context(db, ds_id)
    return StreamingResponse(
        _ai_stream(cfg, prompt),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


# ---------------- 数据模型 CRUD ----------------
@data_controller.get(
    '/model/list',
    summary='数据模型分页列表',
    response_model=PageResponseModel[DataModelVo],
    dependencies=[UserInterfaceAuthDependency('data:model:list')],
)
async def model_list(
    request: Request,
    q: Annotated[DataModelQuery, Query()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(model_content=await DataModelService.get_list(db, q, is_page=True))


@data_controller.get(
    '/model/info/{m_id}', summary='数据模型详情', dependencies=[UserInterfaceAuthDependency('data:model:list')]
)
async def model_info(m_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DataModelService.detail(db, m_id))


@data_controller.post('/model', summary='新增数据模型', dependencies=[UserInterfaceAuthDependency('data:model:add')])
async def model_add(
    request: Request,
    vo: DataModelVo,
    db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await DataModelService.add(db, vo, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


@data_controller.put('/model', summary='修改数据模型', dependencies=[UserInterfaceAuthDependency('data:model:edit')])
async def model_edit(
    request: Request,
    vo: DataModelVo,
    db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await DataModelService.edit(db, vo, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


@data_controller.delete(
    '/model/{ids}', summary='删除数据模型', dependencies=[UserInterfaceAuthDependency('data:model:remove')]
)
async def model_delete(ids: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    r = await DataModelService.delete(db, ids)
    return ResponseUtil.success(msg=r.message)


@data_controller.post(
    '/model/catalog/rebuild',
    summary='重建数据目录检索索引(Agent 按问题检索表用)',
    dependencies=[UserInterfaceAuthDependency('data:model:edit')],
)
async def model_catalog_rebuild(
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    from fastapi.concurrency import run_in_threadpool

    from module_ai.tools.catalog_index import CatalogRetrievalService

    if not CatalogRetrievalService.available():
        return ResponseUtil.failure(msg='未配置 embedding,检索索引不可用')
    n = await run_in_threadpool(CatalogRetrievalService.rebuild)
    return ResponseUtil.success(msg=f'已重建数据目录索引,共 {n} 张表')


# ---------------- 数据查询 / 接口 ----------------
@data_controller.post(
    '/model/{m_id}/query', summary='数据查询(不分页)', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def model_query(
    m_id: Annotated[str, Path()],
    req: QueryReq,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DataQueryService.query(db, m_id, req))


@data_controller.get(
    '/model/{m_id}/sample-query', summary='原生查询默认示例', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def model_sample_query(
    m_id: Annotated[str, Path()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DataQueryService.sample_query(db, m_id))


@data_controller.post(
    '/model/{m_id}/ai-chart',
    summary='AI 生成图表配置(自然语言 + 数据列 → EchartsBuilder cfg)',
    dependencies=[UserInterfaceAuthDependency('data:query')],
)
async def model_ai_chart(
    m_id: Annotated[str, Path()],
    body: dict,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    cfg = await DataQueryService.ai_chart(db, m_id, body.get('question', ''), body.get('columns') or [])
    return ResponseUtil.success(data={'cfg': cfg})


# ---------------- 数据分析模板(取数 + 图表配置,可复用)----------------
@data_controller.get(
    '/analysis-template/list', summary='分析模板列表', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def analysis_template_list(
    db: Annotated[AsyncSession, DBSessionDependency()],
    model_id: Annotated[str, Query()] = '',
) -> Response:
    return ResponseUtil.success(data=await AnalysisTemplateService.get_list(db, model_id or None))


@data_controller.get(
    '/analysis-template/detail/{tid}', summary='看板/模板详情', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def analysis_template_detail(
    tid: Annotated[str, Path()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await AnalysisTemplateService.get(db, tid))


@data_controller.post(
    '/analysis-template', summary='保存分析模板', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def analysis_template_save(
    vo: AnalysisTemplateVo,
    db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    tid = await AnalysisTemplateService.save(db, vo, current_user.user.user_name)
    return ResponseUtil.success(data={'id': tid}, msg='已保存')


@data_controller.post(
    '/analysis-template/from-chart',
    summary='对话图表存为看板(自动挂 custom_query 模型)',
    dependencies=[UserInterfaceAuthDependency('data:query')],
)
async def analysis_template_from_chart(
    body: dict,
    db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """统一存看板入口:带 code(代码取数的图)→ LLM 转;否则用 native+chartSpec(plot_chart 声明式图)直存。"""
    operator = current_user.user.user_name
    if body.get('code'):
        tid = await AnalysisTemplateService.save_from_code(
            db, body.get('name', ''), body.get('datasourceCode', ''),
            body['code'], body.get('question', ''), body.get('remark', ''), operator,
        )
    else:
        tid = await AnalysisTemplateService.save_from_chart(
            db, body.get('name', ''), body.get('datasourceCode', ''),
            body.get('native'), body.get('chartSpec'), body.get('remark', ''), operator,
        )
    return ResponseUtil.success(data={'id': tid}, msg='已存为看板')


@data_controller.post(
    '/analysis-template/code-to-board/stream',
    summary='代码转看板(流式生成 native + 图表配置)',
    dependencies=[UserInterfaceAuthDependency('data:query')],
)
async def analysis_template_code_to_board_stream(
    body: dict,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> StreamingResponse:
    """流式产出 LLM 把取数代码转成的 {native, cfg} JSON(前端实时打印,再自行预览取数画图、确认存看板)。"""
    cfg, prompt = await DataQueryService.prep_code_to_board(
        db, body.get('datasourceCode', ''), body.get('code', ''), body.get('question', ''), body.get('hint', '')
    )
    return StreamingResponse(
        _ai_stream(cfg, prompt),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@data_controller.post(
    '/analysis-template/preview-native',
    summary='按数据源 + native 只读预览取数(转看板画图/校验用)',
    dependencies=[UserInterfaceAuthDependency('data:query')],
)
async def analysis_template_preview_native(
    body: dict,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    data = await DataQueryService.preview_native(db, body.get('datasourceCode', ''), body.get('native'))
    return ResponseUtil.success(data=data)


@data_controller.post(
    '/analysis-template/{tid}/share', summary='开启/重置看板匿名分享', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def analysis_template_share(
    tid: Annotated[str, Path()],
    db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    token = await AnalysisTemplateService.gen_share(db, tid, current_user.user.user_name)
    return ResponseUtil.success(data={'token': token}, msg='已开启分享')


@data_controller.delete(
    '/analysis-template/{tid}/share', summary='关闭看板匿名分享', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def analysis_template_unshare(
    tid: Annotated[str, Path()],
    db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    await AnalysisTemplateService.revoke_share(db, tid, current_user.user.user_name)
    return ResponseUtil.success(msg='已关闭分享')


@data_controller.delete(
    '/analysis-template/{ids}', summary='删除分析模板', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def analysis_template_delete(
    ids: Annotated[str, Path()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    await AnalysisTemplateService.delete(db, ids.split(','))
    return ResponseUtil.success(msg='已删除')


# ---------------- 多图看板 / 大屏(dash_type=board/screen)----------------
@data_controller.get(
    '/dashboard/list', summary='看板/大屏列表', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def dashboard_list(
    db: Annotated[AsyncSession, DBSessionDependency()],
    dash_type: Annotated[str, Query()] = '',
) -> Response:
    return ResponseUtil.success(data=await DashboardService.get_list(db, dash_type or None))


@data_controller.get(
    '/dashboard/detail/{did}', summary='看板/大屏详情(含画布)', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def dashboard_detail(
    did: Annotated[str, Path()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DashboardService.get(db, did))


@data_controller.post('/dashboard', summary='保存看板/大屏', dependencies=[UserInterfaceAuthDependency('data:query')])
async def dashboard_save(
    vo: DashboardVo,
    db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    did = await DashboardService.save(db, vo, current_user.user.user_name)
    return ResponseUtil.success(data={'id': did}, msg='已保存')


@data_controller.post(
    '/dashboard/{did}/share', summary='开启/重置看板匿名分享', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def dashboard_share(
    did: Annotated[str, Path()],
    db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    token = await DashboardService.gen_share(db, did, current_user.user.user_name)
    return ResponseUtil.success(data={'token': token}, msg='已开启分享')


@data_controller.delete(
    '/dashboard/{did}/share', summary='关闭看板匿名分享', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def dashboard_unshare(
    did: Annotated[str, Path()],
    db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    await DashboardService.revoke_share(db, did, current_user.user.user_name)
    return ResponseUtil.success(msg='已关闭分享')


@data_controller.delete(
    '/dashboard/{ids}', summary='删除看板/大屏', dependencies=[UserInterfaceAuthDependency('data:query')]
)
async def dashboard_delete(
    ids: Annotated[str, Path()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    await DashboardService.delete(db, ids.split(','))
    return ResponseUtil.success(msg='已删除')


@data_controller.post(
    '/model/{m_id}/ai-query',
    summary='AI 取数(自然语言→原生查询)',
    dependencies=[UserInterfaceAuthDependency('data:query')],
)
async def model_ai_query(
    m_id: Annotated[str, Path()],
    req: AiQueryReq,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DataQueryService.ai_query(db, m_id, req.question, req.limit or 200))


@data_controller.post(
    '/model/{m_id}/ai-query/stream',
    summary='AI 取数(流式生成查询,前端确认后再执行)',
    dependencies=[UserInterfaceAuthDependency('data:query')],
)
async def model_ai_query_stream(
    m_id: Annotated[str, Path()],
    req: AiQueryReq,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> StreamingResponse:
    cfg, prompt = await DataQueryService.prep_ai_query(db, m_id, req.question)
    # text/event-stream:绕开 gzip 中间件对 text/plain 流式的缓冲(否则整段一次性吐出、非流式);
    # X-Accel-Buffering:no:关掉 nginx 反代缓冲。与 AI 对话/取数代码生成一致。
    return StreamingResponse(
        _ai_stream(cfg, prompt),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@data_controller.post(
    '/model/{m_id}/search', summary='数据接口(分页)', dependencies=[UserInterfaceAuthDependency('data:api')]
)
async def model_search(
    m_id: Annotated[str, Path()],
    req: SearchReq,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DataQueryService.search(db, m_id, req))


# ---------------- ETL 抽取预览(任务调试)----------------
@data_controller.post(
    '/etl/preview',
    summary='ETL 抽取预览(原生查询样本+可选转换)',
    dependencies=[UserInterfaceAuthDependency('data:etl')],
)
async def etl_preview(req: EtlPreviewReq, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await EtlService.preview(db, req))


@data_controller.post(
    '/etl/test-load', summary='ETL 测试写入(把预览样本写入目标)', dependencies=[UserInterfaceAuthDependency('data:etl')]
)
async def etl_test_load(req: EtlTestLoadReq, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await EtlService.test_load(db, req))


@data_controller.post(
    '/etl/ai-query', summary='ETL AI 生成原生查询', dependencies=[UserInterfaceAuthDependency('data:etl')]
)
async def etl_ai_query(req: EtlAiQueryReq, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await EtlService.ai_query(db, req))


@data_controller.post(
    '/etl/ai-transform', summary='ETL AI 生成转换函数', dependencies=[UserInterfaceAuthDependency('data:etl')]
)
async def etl_ai_transform(req: EtlAiTransformReq, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await EtlService.ai_transform(db, req))


@data_controller.post(
    '/etl/ai-query/stream', summary='ETL AI 生成原生查询(流式)', dependencies=[UserInterfaceAuthDependency('data:etl')]
)
async def etl_ai_query_stream(
    req: EtlAiQueryReq, db: Annotated[AsyncSession, DBSessionDependency()]
) -> StreamingResponse:
    cfg, prompt = await EtlService.prep_query(db, req)
    # text/event-stream:绕开 gzip 中间件对 text/plain 流式的缓冲(否则整段一次性吐出、非流式);
    # X-Accel-Buffering:no:关掉 nginx 反代缓冲。与 AI 对话/取数代码生成一致。
    return StreamingResponse(
        _ai_stream(cfg, prompt),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@data_controller.post(
    '/etl/ai-transform/stream',
    summary='ETL AI 生成转换函数(流式)',
    dependencies=[UserInterfaceAuthDependency('data:etl')],
)
async def etl_ai_transform_stream(
    req: EtlAiTransformReq, db: Annotated[AsyncSession, DBSessionDependency()]
) -> StreamingResponse:
    cfg, prompt = await EtlService.prep_transform(db, req)
    # text/event-stream:绕开 gzip 中间件对 text/plain 流式的缓冲(否则整段一次性吐出、非流式);
    # X-Accel-Buffering:no:关掉 nginx 反代缓冲。与 AI 对话/取数代码生成一致。
    return StreamingResponse(
        _ai_stream(cfg, prompt),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@data_controller.post(
    '/etl/ai-extract/stream',
    summary='ETL AI 生成取数代码(流式)',
    dependencies=[UserInterfaceAuthDependency('data:etl')],
)
async def etl_ai_extract_stream(
    req: EtlAiExtractReq, db: Annotated[AsyncSession, DBSessionDependency()]
) -> StreamingResponse:
    cfg, prompt = await EtlService.prep_extract_code(db, req)
    # text/event-stream:gzip 中间件不压缩该类型,避免流式被缓冲(同提示词生成)
    return StreamingResponse(
        _ai_stream(cfg, prompt),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )
