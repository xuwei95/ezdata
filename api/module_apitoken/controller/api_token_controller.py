from typing import Annotated

from fastapi import Path, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_apitoken.entity.vo.api_token_vo import ApiTokenQuery, ApiTokenVo
from module_apitoken.service.api_token_service import ApiTokenService
from utils.response_util import ResponseUtil

# 通用 apikey 管理:任意需要 apikey 的业务(数据接口 / agent 对话)共用本组接口
apitoken_controller = APIRouterPro(prefix='/apitoken', order_num=35, tags=['通用API令牌'], dependencies=[PreAuthDependency()])


@apitoken_controller.get('/list', summary='API Token 列表', response_model=PageResponseModel[ApiTokenVo],
                         dependencies=[UserInterfaceAuthDependency('apitoken:list')])
async def token_list(
    request: Request, q: Annotated[ApiTokenQuery, Query()], db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(model_content=await ApiTokenService.get_list(db, q, is_page=True))


@apitoken_controller.post('', summary='生成 API Token', dependencies=[UserInterfaceAuthDependency('apitoken:add')])
async def token_add(
    request: Request, vo: ApiTokenVo, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await ApiTokenService.add(db, vo, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


@apitoken_controller.delete('/{ids}', summary='删除 API Token', dependencies=[UserInterfaceAuthDependency('apitoken:remove')])
async def token_delete(ids: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    r = await ApiTokenService.delete(db, ids)
    return ResponseUtil.success(msg=r.message)
