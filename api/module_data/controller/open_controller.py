from typing import Annotated

from fastapi import Path, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.router import APIRouterPro
from module_data.service.data_service import OpenDataService
from utils.response_util import ResponseUtil

# 无 PreAuthDependency = 公开接口(用 apikey 校验,不需登录)
open_controller = APIRouterPro(prefix='/open', order_num=98, tags=['公开数据接口'])


@open_controller.get('/data/{model_code}', summary='公开数据接口(apikey + op[field]=value 筛选 + 分页)')
async def open_data(
    model_code: Annotated[str, Path()],
    request: Request,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 形如 /open/data/demo_ord?apikey=sk_xxx&eq[status]=PAID&gt[amount]=100&page=1&pagesize=20
    params = dict(request.query_params)
    return ResponseUtil.success(data=await OpenDataService.public_query(db, model_code, params))
