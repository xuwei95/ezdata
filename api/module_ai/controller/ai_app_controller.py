from datetime import datetime
from typing import Annotated

from fastapi import Path, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic_validation_decorator import ValidateFields
from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_ai.entity.do.ai_app_do import AiApp
from module_ai.entity.vo.ai_app_vo import (
    AiAppModel,
    AiAppPageQueryModel,
    AppDebugReq,
    DeleteAiAppModel,
    PromptGenerateReq,
)
from module_ai.service.ai_app_service import AiAppService
from utils.log_util import logger
from utils.response_util import ResponseUtil

ai_app_controller = APIRouterPro(
    prefix='/ai/app', order_num=21, tags=['AI管理-应用管理'], dependencies=[PreAuthDependency()]
)


@ai_app_controller.get(
    '/list', summary='获取AI应用分页列表', response_model=PageResponseModel[AiAppModel],
    dependencies=[UserInterfaceAuthDependency('ai:app:list')],
)
async def get_ai_app_list(
    request: Request,
    ai_app_page_query: Annotated[AiAppPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(AiApp)],
) -> Response:
    result = await AiAppService.get_ai_app_list_services(query_db, ai_app_page_query, data_scope_sql, is_page=True)
    return ResponseUtil.success(model_content=result)


@ai_app_controller.get(
    '/all', summary='获取AI应用不分页列表(供对话选择)', response_model=DataResponseModel,
)
async def get_ai_app_all(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(AiApp)],
) -> Response:
    result = await AiAppService.get_ai_app_list_services(query_db, AiAppPageQueryModel(), data_scope_sql, is_page=False)
    return ResponseUtil.success(data=result)


@ai_app_controller.post(
    '/prompt/generate', summary='AI 生成系统提示词', response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('ai:app:query')],
)
async def generate_prompt(
    request: Request,
    req: PromptGenerateReq,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    prompt = await AiAppService.generate_prompt_services(query_db, req.requirement, req.model_id or 0)
    return ResponseUtil.success(data={'prompt': prompt})


@ai_app_controller.post(
    '/debug', summary='应用调试对话(用草稿配置,免保存)', response_class=StreamingResponse,
    dependencies=[UserInterfaceAuthDependency('ai:app:query')],
)
async def debug_chat(
    request: Request,
    req: AppDebugReq,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    from module_ai.entity.vo.ai_chat_vo import AiChatRequestModel  # noqa: PLC0415
    from module_ai.service.ai_chat_service import AiChatService  # noqa: PLC0415

    user_id = current_user.user.user_id if current_user and current_user.user else 1
    chat_req = AiChatRequestModel(modelId=0, message=req.message, sessionId=req.session_id)
    stream = AiChatService.chat_services(query_db, chat_req, user_id, app_config_override=req.config or {})
    return StreamingResponse(content=stream, media_type='text/event-stream')


@ai_app_controller.post(
    '', summary='新增AI应用', response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('ai:app:add')],
)
@ValidateFields(validate_model='add_ai_app')
@Log(title='AI应用管理', business_type=BusinessType.INSERT)
async def add_ai_app(
    request: Request,
    add_ai_app: AiAppModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_ai_app.user_id = current_user.user.user_id
    add_ai_app.dept_id = current_user.user.dept_id
    add_ai_app.create_by = current_user.user.user_name
    add_ai_app.create_time = datetime.now()
    add_ai_app.update_by = current_user.user.user_name
    add_ai_app.update_time = datetime.now()
    result = await AiAppService.add_ai_app_services(query_db, add_ai_app)
    return ResponseUtil.success(data=result.result, msg=result.message)


@ai_app_controller.put(
    '', summary='编辑AI应用', response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('ai:app:edit')],
)
@ValidateFields(validate_model='edit_ai_app')
@Log(title='AI应用管理', business_type=BusinessType.UPDATE)
async def edit_ai_app(
    request: Request,
    edit_ai_app: AiAppModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_ai_app.update_by = current_user.user.user_name
    edit_ai_app.update_time = datetime.now()
    result = await AiAppService.edit_ai_app_services(query_db, edit_ai_app)
    return ResponseUtil.success(msg=result.message)


@ai_app_controller.delete(
    '/{app_ids}', summary='删除AI应用', response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('ai:app:remove')],
)
@Log(title='AI应用管理', business_type=BusinessType.DELETE)
async def delete_ai_app(
    request: Request,
    app_ids: Annotated[str, Path(description='需要删除的应用ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AiAppService.delete_ai_app_services(query_db, DeleteAiAppModel(appIds=app_ids))
    return ResponseUtil.success(msg=result.message)


@ai_app_controller.get(
    '/{app_id}', summary='获取AI应用详情', response_model=DataResponseModel[AiAppModel],
    dependencies=[UserInterfaceAuthDependency('ai:app:query')],
)
async def get_ai_app_detail(
    request: Request,
    app_id: Annotated[int, Path(description='应用ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AiAppService.ai_app_detail_services(query_db, app_id)
    return ResponseUtil.success(data=result)
