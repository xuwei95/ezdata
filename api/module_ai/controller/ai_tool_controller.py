from datetime import datetime
from typing import Annotated

from fastapi import Path, Query, Request, Response
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
from module_ai.entity.do.ai_tool_do import AiTool
from module_ai.entity.vo.ai_tool_vo import (
    AiToolModel,
    AiToolPageQueryModel,
    DeleteAiToolModel,
    TestToolReq,
)
from module_ai.service.ai_tool_service import AiToolService
from utils.log_util import logger
from utils.response_util import ResponseUtil

ai_tool_controller = APIRouterPro(
    prefix='/ai/tool', order_num=20, tags=['AI管理-工具管理'], dependencies=[PreAuthDependency()]
)


@ai_tool_controller.get(
    '/list',
    summary='获取AI工具分页列表接口',
    response_model=PageResponseModel[AiToolModel],
    dependencies=[UserInterfaceAuthDependency('ai:tool:list')],
)
async def get_ai_tool_list(
    request: Request,
    ai_tool_page_query: Annotated[AiToolPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(AiTool)],
) -> Response:
    result = await AiToolService.get_ai_tool_list_services(query_db, ai_tool_page_query, data_scope_sql, is_page=True)
    logger.info('获取成功')
    return ResponseUtil.success(model_content=result)


@ai_tool_controller.post(
    '',
    summary='新增AI工具接口',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('ai:tool:add')],
)
@ValidateFields(validate_model='add_ai_tool')
@Log(title='AI工具管理', business_type=BusinessType.INSERT)
async def add_ai_tool(
    request: Request,
    add_ai_tool: AiToolModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_ai_tool.user_id = current_user.user.user_id
    add_ai_tool.dept_id = current_user.user.dept_id
    add_ai_tool.create_by = current_user.user.user_name
    add_ai_tool.create_time = datetime.now()
    add_ai_tool.update_by = current_user.user.user_name
    add_ai_tool.update_time = datetime.now()
    result = await AiToolService.add_ai_tool_services(query_db, add_ai_tool)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@ai_tool_controller.put(
    '',
    summary='编辑AI工具接口',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('ai:tool:edit')],
)
@ValidateFields(validate_model='edit_ai_tool')
@Log(title='AI工具管理', business_type=BusinessType.UPDATE)
async def edit_ai_tool(
    request: Request,
    edit_ai_tool: AiToolModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_ai_tool.update_by = current_user.user.user_name
    edit_ai_tool.update_time = datetime.now()
    result = await AiToolService.edit_ai_tool_services(query_db, edit_ai_tool)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@ai_tool_controller.delete(
    '/{tool_ids}',
    summary='删除AI工具接口',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('ai:tool:remove')],
)
@Log(title='AI工具管理', business_type=BusinessType.DELETE)
async def delete_ai_tool(
    request: Request,
    tool_ids: Annotated[str, Path(description='需要删除的工具ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AiToolService.delete_ai_tool_services(query_db, DeleteAiToolModel(toolIds=tool_ids))
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@ai_tool_controller.post(
    '/test',
    summary='测试MCP工具连接接口',
    description='连接 MCP server 并返回其暴露的工具列表',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('ai:tool:query')],
)
async def test_ai_tool(
    request: Request,
    test_req: TestToolReq,
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await AiToolService.test_mcp_tool_services(test_req.args)
    logger.info(f'测试工具连接成功,发现 {result.get("count")} 个工具')
    return ResponseUtil.success(data=result, msg='连接成功')


@ai_tool_controller.get(
    '/{tool_id}',
    summary='获取AI工具详情接口',
    response_model=DataResponseModel[AiToolModel],
    dependencies=[UserInterfaceAuthDependency('ai:tool:query')],
)
async def get_ai_tool_detail(
    request: Request,
    tool_id: Annotated[int, Path(description='工具ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AiToolService.ai_tool_detail_services(query_db, tool_id)
    logger.info(f'获取tool_id为{tool_id}的信息成功')
    return ResponseUtil.success(data=result)
