from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_dashboard.service.dashboard_service import DashboardService
from utils.response_util import ResponseUtil

dashboard_controller = APIRouterPro(
    prefix='/dashboard', order_num=5, tags=['控制台'], dependencies=[PreAuthDependency()]
)


@dashboard_controller.get('/overview', summary='控制台概览(各模块计数/分布/任务趋势)')
async def overview(request: Request, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DashboardService.overview(db))
