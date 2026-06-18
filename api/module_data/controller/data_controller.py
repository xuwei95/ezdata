from typing import Annotated

from fastapi import Path, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_data.entity.vo.data_vo import (
    AiQueryReq,
    DataModelQuery,
    DataModelVo,
    DataSourceQuery,
    DataSourceVo,
    EtlAiQueryReq,
    EtlAiTransformReq,
    EtlPreviewReq,
    EtlTestLoadReq,
    QueryReq,
    SearchReq,
    TestConnReq,
)
from module_data.service.data_service import (
    DataMetaService,
    DataModelService,
    DataQueryService,
    DataSourceService,
    EtlService,
)
from utils.response_util import ResponseUtil

data_controller = APIRouterPro(prefix='/data', order_num=30, tags=['数据管理'], dependencies=[PreAuthDependency()])


# ---------------- 元信息 ----------------
@data_controller.get('/source/types', summary='可用数据源类型 + 能力')
async def source_types() -> Response:
    return ResponseUtil.success(data=DataMetaService.source_types())


@data_controller.get('/source/schema/{source_type}', summary='连接参数 JSON Schema')
async def source_schema(source_type: Annotated[str, Path()]) -> Response:
    return ResponseUtil.success(data=DataMetaService.connection_schema(source_type))


@data_controller.get('/operators', summary='过滤操作符目录')
async def operators() -> Response:
    return ResponseUtil.success(data=DataMetaService.operators())


# ---------------- 数据源 CRUD ----------------
@data_controller.get('/source/list', summary='数据源分页列表', response_model=PageResponseModel[DataSourceVo])
async def source_list(
    request: Request,
    q: Annotated[DataSourceQuery, Query()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(model_content=await DataSourceService.get_list(db, q, is_page=True))


@data_controller.get('/source/info/{ds_id}', summary='数据源详情(密钥脱敏)')
async def source_info(ds_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DataSourceService.detail(db, ds_id))


@data_controller.post('/source', summary='新增数据源')
async def source_add(
    request: Request, vo: DataSourceVo, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await DataSourceService.add(db, vo, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


@data_controller.put('/source', summary='修改数据源')
async def source_edit(
    request: Request, vo: DataSourceVo, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await DataSourceService.edit(db, vo, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


@data_controller.delete('/source/{ids}', summary='删除数据源')
async def source_delete(ids: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    r = await DataSourceService.delete(db, ids)
    return ResponseUtil.success(msg=r.message)


@data_controller.post('/source/test', summary='测试连接')
async def source_test(req: TestConnReq, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DataSourceService.test_connection(db, req))


@data_controller.get('/source/{ds_id}/tables', summary='列出表/索引/集合')
async def source_tables(ds_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DataSourceService.list_tables(db, ds_id))


@data_controller.get('/source/{ds_id}/columns', summary='字段结构')
async def source_columns(
    ds_id: Annotated[str, Path()], table: Annotated[str, Query()], db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DataSourceService.get_columns(db, ds_id, table))


# ---------------- 数据模型 CRUD ----------------
@data_controller.get('/model/list', summary='数据模型分页列表', response_model=PageResponseModel[DataModelVo])
async def model_list(
    request: Request, q: Annotated[DataModelQuery, Query()], db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(model_content=await DataModelService.get_list(db, q, is_page=True))


@data_controller.get('/model/info/{m_id}', summary='数据模型详情')
async def model_info(m_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DataModelService.detail(db, m_id))


@data_controller.post('/model', summary='新增数据模型')
async def model_add(
    request: Request, vo: DataModelVo, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await DataModelService.add(db, vo, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


@data_controller.put('/model', summary='修改数据模型')
async def model_edit(
    request: Request, vo: DataModelVo, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await DataModelService.edit(db, vo, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


@data_controller.delete('/model/{ids}', summary='删除数据模型')
async def model_delete(ids: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    r = await DataModelService.delete(db, ids)
    return ResponseUtil.success(msg=r.message)


# ---------------- 数据查询 / 接口 ----------------
@data_controller.post('/model/{m_id}/query', summary='数据查询(不分页)')
async def model_query(
    m_id: Annotated[str, Path()], req: QueryReq, db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DataQueryService.query(db, m_id, req))


@data_controller.get('/model/{m_id}/sample-query', summary='原生查询默认示例')
async def model_sample_query(
    m_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DataQueryService.sample_query(db, m_id))


@data_controller.post('/model/{m_id}/ai-query', summary='AI 取数(自然语言→原生查询)')
async def model_ai_query(
    m_id: Annotated[str, Path()], req: AiQueryReq, db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DataQueryService.ai_query(db, m_id, req.question, req.limit or 200))


@data_controller.post('/model/{m_id}/search', summary='数据接口(分页)')
async def model_search(
    m_id: Annotated[str, Path()], req: SearchReq, db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DataQueryService.search(db, m_id, req))


# ---------------- ETL 抽取预览(任务调试)----------------
@data_controller.post('/etl/preview', summary='ETL 抽取预览(原生查询样本+可选转换)')
async def etl_preview(req: EtlPreviewReq, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await EtlService.preview(db, req))


@data_controller.post('/etl/test-load', summary='ETL 测试写入(把预览样本写入目标)')
async def etl_test_load(req: EtlTestLoadReq, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await EtlService.test_load(db, req))


@data_controller.post('/etl/ai-query', summary='ETL AI 生成原生查询')
async def etl_ai_query(req: EtlAiQueryReq, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await EtlService.ai_query(db, req))


@data_controller.post('/etl/ai-transform', summary='ETL AI 生成转换函数')
async def etl_ai_transform(req: EtlAiTransformReq, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await EtlService.ai_transform(db, req))
