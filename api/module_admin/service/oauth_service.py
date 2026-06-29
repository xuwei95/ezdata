"""GitHub SSO 服务:OAuth 交换、拉取 GitHub 资料、解析/自动建号绑定平台用户。"""
import secrets
import uuid
from datetime import datetime
from types import SimpleNamespace
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.context import tenant_bypass
from config.env import GithubSsoConfig
from exceptions.exception import ServiceException
from module_admin.dao.role_dao import RoleDao
from module_admin.dao.user_dao import UserDao
from module_admin.entity.do.user_oauth_do import SysUserOauth
from module_admin.entity.vo.role_vo import RoleModel
from module_admin.entity.vo.user_vo import AddUserModel, UserModel
from module_admin.service.user_service import UserService
from utils.log_util import logger
from utils.pwd_util import PwdUtil

GITHUB_AUTHORIZE = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN = 'https://github.com/login/oauth/access_token'
GITHUB_API = 'https://api.github.com'


class GithubOauthService:
    """GitHub OAuth 流程与用户落地。"""

    @staticmethod
    def authorize_url(state: str) -> str:
        """构造 GitHub 授权跳转地址。"""
        params = {
            'client_id': GithubSsoConfig.github_client_id,
            'redirect_uri': GithubSsoConfig.github_redirect_uri,
            'scope': 'read:user user:email',
            'state': state,
            'allow_signup': 'false',
        }
        return f'{GITHUB_AUTHORIZE}?{urlencode(params)}'

    @classmethod
    async def fetch_profile(cls, code: str) -> dict:
        """用授权码换 access_token,并拉取 GitHub 用户资料(含主邮箱、可选组织校验)。"""
        async with httpx.AsyncClient(timeout=15) as client:
            tok_resp = await client.post(
                GITHUB_TOKEN,
                headers={'Accept': 'application/json'},
                data={
                    'client_id': GithubSsoConfig.github_client_id,
                    'client_secret': GithubSsoConfig.github_client_secret,
                    'code': code,
                    'redirect_uri': GithubSsoConfig.github_redirect_uri,
                },
            )
            tok = tok_resp.json()
            access_token = tok.get('access_token')
            if not access_token:
                raise ServiceException(message=f'GitHub 授权失败: {tok.get("error_description") or tok.get("error") or "无 access_token"}')

            auth_headers = {'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'}
            user = (await client.get(f'{GITHUB_API}/user', headers=auth_headers)).json()
            if not user.get('id'):
                raise ServiceException(message='获取 GitHub 用户信息失败')

            email = user.get('email')
            if not email:
                emails = (await client.get(f'{GITHUB_API}/user/emails', headers=auth_headers)).json()
                if isinstance(emails, list):
                    primary = next((e for e in emails if e.get('primary') and e.get('verified')), None)
                    email = (primary or (emails[0] if emails else {})).get('email')

            # 可选:限定 GitHub 组织成员
            allowed_org = (GithubSsoConfig.github_allowed_org or '').strip()
            if allowed_org:
                orgs = (await client.get(f'{GITHUB_API}/user/orgs', headers=auth_headers)).json()
                org_logins = {o.get('login') for o in orgs} if isinstance(orgs, list) else set()
                if allowed_org not in org_logins:
                    raise ServiceException(message=f'仅允许 GitHub 组织「{allowed_org}」成员登录')

        return {
            'open_id': str(user['id']),
            'login': user.get('login') or f'gh{user["id"]}',
            'name': user.get('name') or user.get('login'),
            'email': email,
            'avatar': user.get('avatar_url'),
        }

    @classmethod
    async def resolve_or_provision(cls, db: AsyncSession, profile: dict) -> SimpleNamespace:
        """据 GitHub 资料解析平台用户:已绑定→取;邮箱命中→绑;否则自动建号(可关)。

        全程跨租户(无登录上下文)操作,显式 tenant_bypass。
        返回标量快照(user_id/user_name/tenant_id),避免提交后惰性加载(MissingGreenlet)。
        """
        from module_admin.entity.do.user_do import SysUser  # noqa: PLC0415

        with tenant_bypass():
            uid: int | None = None
            tenant_id: int | None = None
            # 1) 已绑定
            binding = (
                await db.execute(
                    select(SysUserOauth).where(
                        SysUserOauth.provider == 'github', SysUserOauth.open_id == profile['open_id']
                    )
                )
            ).scalars().first()
            if binding:
                row = (
                    await db.execute(
                        select(SysUser.user_id, SysUser.tenant_id).where(SysUser.user_id == binding.user_id)
                    )
                ).first()
                if row:
                    uid, tenant_id = row.user_id, row.tenant_id
                else:
                    # 绑定悬空(用户被删):清理后走建号
                    await db.delete(binding)
                    await db.flush()

            # 2) 邮箱匹配既有用户 → 建绑定
            if uid is None and profile.get('email'):
                existing = await UserDao.get_user_by_info(db, UserModel(email=profile['email']))
                if existing:
                    uid, tenant_id = existing.user_id, existing.tenant_id
                    await cls._create_binding(db, uid, tenant_id, profile)

            # 3) 自动建号
            if uid is None:
                if not GithubSsoConfig.github_sso_auto_create:
                    raise ServiceException(message='该 GitHub 账号未绑定平台用户,且未开启自动建号')
                uid, tenant_id = await cls._provision_user(db, profile)
                await cls._create_binding(db, uid, tenant_id, profile)

            await db.commit()
            # 提交后惰性属性会失效,改取标量快照返回
            snap = (
                await db.execute(
                    select(SysUser.user_id, SysUser.user_name, SysUser.tenant_id).where(SysUser.user_id == uid)
                )
            ).first()
            return SimpleNamespace(user_id=snap.user_id, user_name=snap.user_name, tenant_id=snap.tenant_id)

    @classmethod
    async def _provision_user(cls, db: AsyncSession, profile: dict) -> tuple[int, int | None]:
        """按默认角色/部门新建用户(决定租户),返回 (user_id, tenant_id)。"""
        from module_admin.entity.do.user_do import SysUser  # noqa: PLC0415

        # 生成唯一登录名
        base = 'gh_' + (profile['login'] or profile['open_id'])
        user_name = base
        if await UserDao.get_user_by_name(db, user_name):
            user_name = f'{base}_{profile["open_id"]}'

        # 默认角色 roleKey → role_id
        role_ids: list[int] = []
        role_key = (GithubSsoConfig.github_sso_default_role_key or '').strip()
        if role_key:
            role = await RoleDao.get_role_by_info(db, RoleModel(role_key=role_key))
            if role:
                role_ids = [role.role_id]

        add_user = AddUserModel(
            userName=user_name,
            nickName=profile.get('name') or user_name,
            email=profile.get('email'),
            password=PwdUtil.get_password_hash(secrets.token_urlsafe(24)),  # 随机占位,SSO 用户走第三方登录
            deptId=GithubSsoConfig.github_sso_default_dept_id or None,
            avatar=profile.get('avatar') or '',
            status='0',
            sex='2',
            pwdUpdateDate=datetime.now(),
            roleIds=role_ids,
        )
        result = await UserService.add_user_services(db, add_user)
        if not result.is_success:
            raise ServiceException(message=f'SSO 自动建号失败: {result.message}')
        # add_user_services 内部已 commit;此处为新查询,属性已加载,可安全取标量
        row = (
            await db.execute(select(SysUser.user_id, SysUser.tenant_id).where(SysUser.user_name == user_name))
        ).first()
        if not row:
            raise ServiceException(message='SSO 自动建号后未能读取用户')
        logger.info(f'GitHub SSO 自动建号: {user_name} (tenant={row.tenant_id})')
        return row.user_id, row.tenant_id

    @staticmethod
    async def _create_binding(db: AsyncSession, user_id: int, tenant_id: int | None, profile: dict) -> None:
        """写入第三方身份绑定记录。"""
        db.add(
            SysUserOauth(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                provider='github',
                open_id=profile['open_id'],
                login_name=profile.get('login'),
                avatar=profile.get('avatar'),
                create_time=datetime.now(),
            )
        )
        await db.flush()


def gen_state() -> str:
    """生成 OAuth state(CSRF)。"""
    return secrets.token_urlsafe(24)
