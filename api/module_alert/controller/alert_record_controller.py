from typing import Annotated

from fastapi import Path, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import PageResponseModel, ResponseBaseModel
from module_alert.entity.vo.alert_vo import (
    AlertRecordModel,
    AlertRecordPageQueryModel,
    DeleteAlertRecordModel,
    EditAlertStatusModel,
)
from module_alert.service.alert_service import AlertRecordService
from utils.log_util import logger
from utils.response_util import ResponseUtil

alert_record_controller = APIRouterPro(
    prefix='/alert/record', order_num=16, tags=['告警中心-告警记录'], dependencies=[PreAuthDependency()]
)


@alert_record_controller.get(
    '/list',
    summary='获取告警记录分页列表',
    response_model=PageResponseModel[AlertRecordModel],
    dependencies=[UserInterfaceAuthDependency('alert:record:list')],
)
async def get_record_list(
    request: Request,
    page_query: Annotated[AlertRecordPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AlertRecordService.get_record_list_services(query_db, page_query, is_page=True)
    return ResponseUtil.success(model_content=result)


@alert_record_controller.put(
    '/changeStatus',
    summary='标记告警处理状态',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('alert:record:edit')],
)
@Log(title='告警记录', business_type=BusinessType.UPDATE)
async def change_record_status(
    request: Request,
    edit_status: EditAlertStatusModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AlertRecordService.edit_record_status_services(query_db, edit_status)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@alert_record_controller.delete(
    '/{alert_ids}',
    summary='删除告警记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('alert:record:remove')],
)
@Log(title='告警记录', business_type=BusinessType.DELETE)
async def delete_record(
    request: Request,
    alert_ids: Annotated[str, Path(description='需要删除的告警ID(逗号分隔)')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await AlertRecordService.delete_record_services(query_db, DeleteAlertRecordModel(alertIds=alert_ids))
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)
