from datetime import datetime
from typing import Annotated

from fastapi import Path, Query, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_alert.entity.vo.alert_vo import (
    AlertStrategyModel,
    AlertStrategyPageQueryModel,
    DeleteAlertStrategyModel,
)
from module_alert.service.alert_service import AlertStrategyService
from utils.log_util import logger
from utils.response_util import ResponseUtil

alert_strategy_controller = APIRouterPro(
    prefix='/alert/strategy', order_num=15, tags=['告警中心-告警策略'], dependencies=[PreAuthDependency()]
)


@alert_strategy_controller.get(
    '/list',
    summary='获取告警策略分页列表',
    response_model=PageResponseModel[AlertStrategyModel],
    dependencies=[UserInterfaceAuthDependency('alert:strategy:list')],
)
async def get_strategy_list(
    request: Request,
    page_query: Annotated[AlertStrategyPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AlertStrategyService.get_strategy_list_services(query_db, page_query, is_page=True)
    return ResponseUtil.success(model_content=result)


@alert_strategy_controller.get(
    '/all',
    summary='获取启用的告警策略(不分页,供任务绑定选择)',
    response_model=DataResponseModel[AlertStrategyModel],
)
async def get_strategy_all(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AlertStrategyService.get_strategy_list_services(
        query_db, AlertStrategyPageQueryModel(status=1), is_page=False
    )
    return ResponseUtil.success(data=result)


@alert_strategy_controller.post(
    '',
    summary='新增告警策略',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('alert:strategy:add')],
)
@ValidateFields(validate_model='add_strategy')
@Log(title='告警策略', business_type=BusinessType.INSERT)
async def add_strategy(
    request: Request,
    add_strategy: AlertStrategyModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_strategy.create_by = current_user.user.user_name
    add_strategy.create_time = datetime.now()
    add_strategy.update_by = current_user.user.user_name
    add_strategy.update_time = datetime.now()
    result = await AlertStrategyService.add_strategy_services(query_db, add_strategy)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@alert_strategy_controller.put(
    '',
    summary='编辑告警策略',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('alert:strategy:edit')],
)
@ValidateFields(validate_model='edit_strategy')
@Log(title='告警策略', business_type=BusinessType.UPDATE)
async def edit_strategy(
    request: Request,
    edit_strategy: AlertStrategyModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_strategy.update_by = current_user.user.user_name
    edit_strategy.update_time = datetime.now()
    result = await AlertStrategyService.edit_strategy_services(query_db, edit_strategy)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@alert_strategy_controller.delete(
    '/{strategy_ids}',
    summary='删除告警策略',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('alert:strategy:remove')],
)
@Log(title='告警策略', business_type=BusinessType.DELETE)
async def delete_strategy(
    request: Request,
    strategy_ids: Annotated[str, Path(description='需要删除的策略ID(逗号分隔)')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AlertStrategyService.delete_strategy_services(
        query_db, DeleteAlertStrategyModel(strategyIds=strategy_ids)
    )
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@alert_strategy_controller.get(
    '/{strategy_id}',
    summary='获取告警策略详情',
    response_model=DataResponseModel[AlertStrategyModel],
    dependencies=[UserInterfaceAuthDependency('alert:strategy:query')],
)
async def get_strategy_detail(
    request: Request,
    strategy_id: Annotated[int, Path(description='策略ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AlertStrategyService.strategy_detail_services(query_db, strategy_id)
    return ResponseUtil.success(data=result)
