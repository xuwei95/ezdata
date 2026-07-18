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
from module_ai.entity.do.ai_skill_do import AiSkill
from module_ai.entity.vo.ai_skill_vo import (
    AiSkillModel,
    AiSkillPageQueryModel,
    DeleteAiSkillModel,
)
from module_ai.service.ai_skill_service import AiSkillService
from utils.log_util import logger
from utils.response_util import ResponseUtil

ai_skill_controller = APIRouterPro(
    prefix='/ai/skill', order_num=21, tags=['AI管理-技能管理'], dependencies=[PreAuthDependency()]
)


@ai_skill_controller.get(
    '/list',
    summary='获取AI技能分页列表接口',
    response_model=PageResponseModel[AiSkillModel],
    dependencies=[UserInterfaceAuthDependency('ai:skill:list')],
)
async def get_ai_skill_list(
    request: Request,
    ai_skill_page_query: Annotated[AiSkillPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(AiSkill)],
) -> Response:
    result = await AiSkillService.get_ai_skill_list_services(query_db, ai_skill_page_query, data_scope_sql, is_page=True)
    logger.info('获取成功')
    return ResponseUtil.success(model_content=result)


@ai_skill_controller.post(
    '',
    summary='新增AI技能接口',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('ai:skill:add')],
)
@ValidateFields(validate_model='add_ai_skill')
@Log(title='AI技能管理', business_type=BusinessType.INSERT)
async def add_ai_skill(
    request: Request,
    add_ai_skill: AiSkillModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_ai_skill.user_id = current_user.user.user_id
    add_ai_skill.dept_id = current_user.user.dept_id
    add_ai_skill.create_by = current_user.user.user_name
    add_ai_skill.create_time = datetime.now()
    add_ai_skill.update_by = current_user.user.user_name
    add_ai_skill.update_time = datetime.now()
    result = await AiSkillService.add_ai_skill_services(query_db, add_ai_skill)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@ai_skill_controller.put(
    '',
    summary='编辑AI技能接口',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('ai:skill:edit')],
)
@ValidateFields(validate_model='edit_ai_skill')
@Log(title='AI技能管理', business_type=BusinessType.UPDATE)
async def edit_ai_skill(
    request: Request,
    edit_ai_skill: AiSkillModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_ai_skill.update_by = current_user.user.user_name
    edit_ai_skill.update_time = datetime.now()
    result = await AiSkillService.edit_ai_skill_services(query_db, edit_ai_skill)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@ai_skill_controller.delete(
    '/{skill_ids}',
    summary='删除AI技能接口',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('ai:skill:remove')],
)
@Log(title='AI技能管理', business_type=BusinessType.DELETE)
async def delete_ai_skill(
    request: Request,
    skill_ids: Annotated[str, Path(description='需要删除的技能ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AiSkillService.delete_ai_skill_services(query_db, DeleteAiSkillModel(skillIds=skill_ids))
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@ai_skill_controller.get(
    '/{skill_id}',
    summary='获取AI技能详情接口',
    response_model=DataResponseModel[AiSkillModel],
    dependencies=[UserInterfaceAuthDependency('ai:skill:query')],
)
async def get_ai_skill_detail(
    request: Request,
    skill_id: Annotated[int, Path(description='技能ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AiSkillService.ai_skill_detail_services(query_db, skill_id)
    logger.info(f'获取skill_id为{skill_id}的信息成功')
    return ResponseUtil.success(data=result)
