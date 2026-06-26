from typing import Annotated

from fastapi import Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_ai.service.ai_metrics_service import AiMetricsService
from utils.response_util import ResponseUtil

ai_metrics_controller = APIRouterPro(
    prefix='/ai/metrics', order_num=25, tags=['AI管理-用量可观测'], dependencies=[PreAuthDependency()]
)


@ai_metrics_controller.get(
    '/overview', summary='AI 用量总览(token/时延/模型/用户)',
    dependencies=[UserInterfaceAuthDependency('ai:metrics:list')],
)
async def metrics_overview(
    request: Request,
    db: Annotated[AsyncSession, DBSessionDependency()],
    days: Annotated[int, Query()] = 7,
) -> Response:
    return ResponseUtil.success(data=await AiMetricsService.overview(db, days))
