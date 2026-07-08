import uuid
from datetime import datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from common.annotation.cache_annotation import ApiCache, ApiCacheEvict
from common.annotation.log_annotation import Log
from common.annotation.rate_limit_annotation import ApiRateLimit, ApiRateLimitPreset
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency
from common.constant import ApiGroup, ApiNamespace
from common.context import RequestContext, tenant_bypass
from common.enums import BusinessType, RedisInitKeyConfig
from common.router import APIRouterPro
from common.vo import CrudResponseModel, DataResponseModel, DynamicResponseModel, ResponseBaseModel
from config.env import AppConfig, GithubSsoConfig, JwtConfig
from exceptions.exception import ServiceException
from module_admin.dao.user_tenant_dao import UserTenantDao
from module_admin.entity.vo.login_vo import LoginToken, RouterModel, Token, UserLogin, UserRegister
from module_admin.entity.vo.user_vo import CurrentUserModel, EditUserModel, SwitchTenantModel, TenantOptionModel
from module_admin.service.login_service import CustomOAuth2PasswordRequestForm, LoginService, oauth2_scheme
from module_admin.service.oauth_service import GithubOauthService, gen_state
from module_admin.service.user_service import UserService
from utils.log_util import logger
from utils.response_util import ResponseUtil

login_controller = APIRouterPro(order_num=1, tags=['登录模块'])


@login_controller.post(
    '/login',
    summary='登录接口',
    description='用于用户登录',
    response_model=DynamicResponseModel[LoginToken] | Token,
)
@ApiRateLimit(namespace=ApiNamespace.LOGIN, preset=ApiRateLimitPreset.ANON_AUTH_LOGIN)
@ApiCacheEvict(namespaces=ApiGroup.LOGIN_SUCCESS_MUTATION)
@Log(title='用户登录', business_type=BusinessType.OTHER, log_type='login')
async def login(
    request: Request,
    form_data: Annotated[CustomOAuth2PasswordRequestForm, Depends()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    captcha_enabled = (
        await request.app.state.redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.account.captchaEnabled') == 'true'
    )
    user = UserLogin(
        userName=form_data.username,
        password=form_data.password,
        code=form_data.code,
        uuid=form_data.uuid,
        loginInfo=form_data.login_info,
        captchaEnabled=captcha_enabled,
    )
    result = await LoginService.authenticate_user(request, query_db, user)
    access_token_expires = timedelta(minutes=JwtConfig.jwt_expire_minutes)
    session_id = str(uuid.uuid4())
    # 多租户:登录默认激活租户(成员表 is_default;无则 None,由 get_current_user 兜底解析)
    with tenant_bypass():
        active_tenant_id = await UserTenantDao.get_default_tenant(query_db, result[0].user_id)
    access_token = await LoginService.create_access_token(
        data={
            'user_id': str(result[0].user_id),
            'user_name': result[0].user_name,
            'dept_name': result[1].dept_name if result[1] else None,
            'session_id': session_id,
            'login_info': user.login_info,
            'tenant_id': active_tenant_id,
        },
        expires_delta=access_token_expires,
    )
    if AppConfig.app_same_time_login:
        await request.app.state.redis.set(
            f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}',
            access_token,
            ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes),
        )
    else:
        # 此方法可实现同一账号同一时间只能登录一次
        await request.app.state.redis.set(
            f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{result[0].user_id}',
            access_token,
            ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes),
        )
    # 登录回写(更新登录时间)发生在租户上下文建立之前(登录态尚未鉴权),且会级联读取该用户的
    # 岗位/角色等多租户表;在租户默认拒绝下需显式放行(此为登录引导,操作的就是当前认证用户自身)。
    with tenant_bypass():
        await UserService.edit_user_services(
            query_db, EditUserModel(userId=result[0].user_id, loginDate=datetime.now(), type='status')
        )
    logger.info('登录成功')
    # 判断请求是否来自于api文档，如果是返回指定格式的结果，用于修复api文档认证成功后token显示undefined的bug
    request_from_swagger = request.headers.get('referer').endswith('docs') if request.headers.get('referer') else False
    request_from_redoc = request.headers.get('referer').endswith('redoc') if request.headers.get('referer') else False
    if request_from_swagger or request_from_redoc:
        return {'access_token': access_token, 'token_type': 'Bearer'}
    return ResponseUtil.success(msg='登录成功', dict_content={'token': access_token})


@login_controller.get(
    '/getInfo',
    summary='获取用户信息接口',
    description='用于获取当前登录用户的信息',
    response_model=DynamicResponseModel[CurrentUserModel],
)
@ApiCache(namespace=ApiNamespace.LOGIN_USER_INFO)
async def get_login_user_info(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 多租户:附当前激活租户 + 可切换租户列表(admin 见全部顶级部门,普通用户见其成员)
    is_admin = bool(current_user.user and current_user.user.admin)
    if is_admin:
        depts = await UserTenantDao.list_top_depts(query_db)
        current_user.tenant_list = [TenantOptionModel(tenantId=d[0], tenantName=d[1], isDefault=False) for d in depts]
        current_user.current_tenant_id = None
    else:
        memberships = await UserTenantDao.list_by_user(query_db, current_user.user.user_id)
        default_map = {m.tenant_id: m.is_default for m in memberships}
        depts = await UserTenantDao.list_top_depts(query_db, list(default_map.keys()))
        current_user.tenant_list = [
            TenantOptionModel(tenantId=d[0], tenantName=d[1], isDefault=bool(default_map.get(d[0]))) for d in depts
        ]
        current_user.current_tenant_id = RequestContext.get_current_tenant_id()
    logger.info('获取成功')

    return ResponseUtil.success(model_content=current_user)


@login_controller.get(
    '/getRouters',
    summary='获取用户路由接口',
    description='用于获取当前登录用户的路由信息',
    response_model=DataResponseModel[list[RouterModel]],
)
@ApiCache(namespace=ApiNamespace.LOGIN_USER_ROUTERS)
async def get_login_user_routers(
    request: Request,
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    logger.info('获取成功')
    user_routers = await LoginService.get_current_user_routers(current_user.user.user_id, query_db)

    return ResponseUtil.success(data=user_routers)


@login_controller.post(
    '/register',
    summary='注册接口',
    description='用于用户注册',
    response_model=DataResponseModel[CrudResponseModel],
)
@ApiRateLimit(namespace=ApiNamespace.REGISTER, preset=ApiRateLimitPreset.ANON_AUTH_REGISTER)
@ApiCacheEvict(namespaces=ApiGroup.USER_ENTITY_MUTATION)
async def register_user(
    request: Request,
    user_register: UserRegister,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    user_register_result = await LoginService.register_user_services(request, query_db, user_register)
    logger.info(user_register_result.message)

    return ResponseUtil.success(data=user_register_result, msg=user_register_result.message)


# @login_controller.post("/getSmsCode", response_model=SmsCode)
# async def get_sms_code(request: Request, user: ResetUserModel, query_db: AsyncSession = DBSessionDependency()):
#     try:
#         sms_result = await LoginService.get_sms_code_services(request, query_db, user)
#         if sms_result.is_success:
#             logger.info('获取成功')
#             return ResponseUtil.success(data=sms_result)
#         else:
#             logger.warning(sms_result.message)
#             return ResponseUtil.failure(msg=sms_result.message)
#     except Exception as e:
#         logger.exception(e)
#         return ResponseUtil.error(msg=str(e))
#
#
# @login_controller.post("/forgetPwd", response_model=CrudResponseModel)
# async def forget_user_pwd(request: Request, forget_user: ResetUserModel, query_db: AsyncSession = DBSessionDependency()):
#     try:
#         forget_user_result = await LoginService.forget_user_services(request, query_db, forget_user)
#         if forget_user_result.is_success:
#             logger.info(forget_user_result.message)
#             return ResponseUtil.success(data=forget_user_result, msg=forget_user_result.message)
#         else:
#             logger.warning(forget_user_result.message)
#             return ResponseUtil.failure(msg=forget_user_result.message)
#     except Exception as e:
#         logger.exception(e)
#         return ResponseUtil.error(msg=str(e))


@login_controller.post(
    '/logout',
    summary='退出登录接口',
    description='用于用户退出登录',
    response_model=ResponseBaseModel,
)
@ApiCacheEvict(namespaces=ApiGroup.LOGOUT_MUTATION)
async def logout(request: Request, token: Annotated[str | None, Depends(oauth2_scheme)]) -> Response:
    payload = jwt.decode(
        token, JwtConfig.jwt_secret_key, algorithms=[JwtConfig.jwt_algorithm], options={'verify_exp': False}
    )
    if AppConfig.app_same_time_login:
        token_id: str = payload.get('session_id')
    else:
        token_id: str = payload.get('user_id')
    await LoginService.logout_services(request, token_id)
    logger.info('退出成功')

    return ResponseUtil.success(msg='退出成功')


@login_controller.post(
    '/switchTenant',
    summary='切换当前激活租户',
    description='校验成员资格后重签 token(激活租户随之改变)',
    response_model=ResponseBaseModel,
)
@ApiCacheEvict(namespaces=ApiGroup.LOGIN_SUCCESS_MUTATION)
async def switch_tenant(
    request: Request,
    req: SwitchTenantModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """切换激活租户:校验当前用户是目标租户成员(超管放行任意顶级部门)→ 重签 token。"""
    user_id = current_user.user.user_id
    is_admin = bool(current_user.user and current_user.user.admin)
    with tenant_bypass():
        if is_admin:
            top_ids = {d[0] for d in await UserTenantDao.list_top_depts(query_db)}
            allowed = req.tenant_id in top_ids
        else:
            allowed = await UserTenantDao.is_member(query_db, user_id, req.tenant_id)
    if not allowed:
        return ResponseUtil.forbidden(msg='无权切换到该租户')

    session_id = str(uuid.uuid4())
    access_token = await LoginService.create_access_token(
        data={
            'user_id': str(user_id),
            'user_name': current_user.user.user_name,
            'dept_name': None,
            'session_id': session_id,
            'login_info': 'switch-tenant',
            'tenant_id': req.tenant_id,
        },
        expires_delta=timedelta(minutes=JwtConfig.jwt_expire_minutes),
    )
    redis = request.app.state.redis
    key_suffix = session_id if AppConfig.app_same_time_login else str(user_id)
    await redis.set(
        f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{key_suffix}',
        access_token,
        ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes),
    )
    logger.info(f'用户 {user_id} 切换激活租户 -> {req.tenant_id}')
    return ResponseUtil.success(msg='切换成功', dict_content={'token': access_token})


async def _issue_token_for_user(request: Request, user) -> str:
    """为已解析的用户签发 JWT 并写入 Redis 会话(复用账密登录的会话机制)。"""
    session_id = str(uuid.uuid4())
    access_token = await LoginService.create_access_token(
        data={
            'user_id': str(user.user_id),
            'user_name': user.user_name,
            'dept_name': None,
            'session_id': session_id,
            'login_info': 'GitHub SSO',
            # SSO 用户新建即有一条 home 租户成员,直接作激活租户;get_current_user 会再校验
            'tenant_id': getattr(user, 'tenant_id', None),
        },
        expires_delta=timedelta(minutes=JwtConfig.jwt_expire_minutes),
    )
    redis = request.app.state.redis
    key_suffix = session_id if AppConfig.app_same_time_login else str(user.user_id)
    await redis.set(
        f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{key_suffix}',
        access_token,
        ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes),
    )
    return access_token


@login_controller.get('/oauth/github/authorize', summary='GitHub 授权跳转')
async def github_authorize(request: Request) -> Response:
    """生成 state(防 CSRF)并 302 跳转到 GitHub 授权页。"""
    if not GithubSsoConfig.github_sso_enabled:
        return ResponseUtil.failure(msg='GitHub 登录未启用')
    state = gen_state()
    await request.app.state.redis.set(f'oauth:github:state:{state}', '1', ex=600)
    return RedirectResponse(GithubOauthService.authorize_url(state))


@login_controller.get('/oauth/github/callback', summary='GitHub 回调')
async def github_callback(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    code: str = '',
    state: str = '',
) -> Response:
    """校验 state → 换取资料 → 解析/建号 → 签发 token → 回跳前端(带 token 或 error)。"""
    frontend = GithubSsoConfig.github_sso_frontend_url
    sep = '&' if '?' in frontend else '?'
    try:
        if not GithubSsoConfig.github_sso_enabled:
            raise ServiceException(message='GitHub 登录未启用')
        if not code or not state:
            raise ServiceException(message='缺少 code 或 state')
        state_key = f'oauth:github:state:{state}'
        if not await request.app.state.redis.get(state_key):
            raise ServiceException(message='state 无效或已过期')
        await request.app.state.redis.delete(state_key)

        profile = await GithubOauthService.fetch_profile(code)
        user = await GithubOauthService.resolve_or_provision(query_db, profile)
        token = await _issue_token_for_user(request, user)
        logger.info(f'GitHub SSO 登录成功: user_id={user.user_id}')
        return RedirectResponse(f'{frontend}{sep}token={token}')
    except Exception as e:
        from urllib.parse import quote

        msg = getattr(e, 'message', None) or str(e)
        logger.warning(f'GitHub SSO 失败: {msg}')
        return RedirectResponse(f'{frontend}{sep}error={quote(msg)}')
