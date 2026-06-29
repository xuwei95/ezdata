import re
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Literal

from exceptions.exception import LoginException
from module_admin.entity.vo.user_vo import CurrentUserModel

# 定义上下文变量
# 存储当前请求的编译后的排除路由模式列表
current_exclude_patterns: ContextVar[
    list[dict[str, str | list[Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']] | re.Pattern]] | None
] = ContextVar('current_exclude_patterns', default=None)
# 存储当前用户信息
current_user: ContextVar[CurrentUserModel | None] = ContextVar('current_user', default=None)
# 多租户：当前请求/执行的租户ID(=顶级部门ID)。为 None 表示未设置(系统/匿名上下文，不过滤)
current_tenant_id: ContextVar[int | None] = ContextVar('current_tenant_id', default=None)
# 多租户：是否绕过租户过滤(超管/平台/Worker 引导加载用)。True 时不注入租户条件
current_tenant_bypass: ContextVar[bool] = ContextVar('current_tenant_bypass', default=False)
# 是否处于 HTTP 请求作用域(由 get_db 依赖标记)。仅在请求作用域内对“空租户”默认拒绝;
# 后台(Celery/APScheduler 用独立同步会话,不经 get_db)保持宽松,允许按主键引导加载任务后再设租户。
current_in_request: ContextVar[bool] = ContextVar('current_in_request', default=False)


class RequestContext:
    """
    请求上下文管理类，用于设置和清理上下文变量
    """

    @staticmethod
    def set_current_exclude_patterns(
        exclude_patterns: list[
            dict[str, str | list[Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']] | re.Pattern]
        ],
    ) -> Token:
        """
        设置当前请求的编译后的排除路由模式列表

        :param exclude_patterns: 编译后的排除路由模式列表
        :return: 上下文变量令牌，用于重置
        """
        return current_exclude_patterns.set(exclude_patterns)

    @staticmethod
    def get_current_exclude_patterns() -> list[
        dict[str, str | list[Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']] | re.Pattern]
    ]:
        """
        获取当前请求的编译后的排除路由模式列表

        :return: 编译后的排除路由模式列表
        """
        _exclude_patterns = current_exclude_patterns.get()
        if _exclude_patterns is None:
            _exclude_patterns = []
        return _exclude_patterns

    @staticmethod
    def set_current_user(user: CurrentUserModel) -> Token:
        """
        设置当前用户信息

        :param user: 用户信息
        :return: 上下文变量令牌，用于重置
        """
        return current_user.set(user)

    @staticmethod
    def get_current_user() -> CurrentUserModel:
        """
        获取当前用户信息

        :return: 用户信息
        """
        _current_user = current_user.get()
        if _current_user is None:
            raise LoginException(data='', message='当前用户信息为空，请检查是否已登录')
        return _current_user

    @staticmethod
    def set_current_tenant_id(tenant_id: int | None) -> Token:
        """设置当前租户ID(=顶级部门ID)"""
        return current_tenant_id.set(tenant_id)

    @staticmethod
    def get_current_tenant_id() -> int | None:
        """获取当前租户ID(可能为 None)"""
        return current_tenant_id.get()

    @staticmethod
    def get_effective_tenant_id() -> int | None:
        """获取生效的租户ID：bypass 开启或未设置时返回 None(表示不注入租户过滤)"""
        if current_tenant_bypass.get():
            return None
        return current_tenant_id.get()

    @staticmethod
    def is_tenant_bypassed() -> bool:
        """是否处于租户绕过(超管/系统/bootstrap)上下文。用于区分'放行'与'未设置'。"""
        return current_tenant_bypass.get()

    @staticmethod
    def mark_request_scope() -> None:
        """标记当前处于 HTTP 请求作用域(由 get_db 依赖调用)。"""
        current_in_request.set(True)

    @staticmethod
    def is_request_scope() -> bool:
        """是否处于 HTTP 请求作用域(决定空租户是默认拒绝还是宽松放行)。"""
        return current_in_request.get()

    @staticmethod
    def reset_current_tenant_id(token: Token) -> None:
        """重置当前租户ID"""
        current_tenant_id.reset(token)

    @staticmethod
    def set_current_tenant_bypass(flag: bool) -> Token:
        """设置是否绕过租户过滤(平台超管整请求生效)"""
        return current_tenant_bypass.set(flag)

    @staticmethod
    def reset_current_exclude_patterns(token: Token) -> None:
        """
        重置当前请求的编译后的排除路由模式列表

        :param token: 设置编译后的排除路由模式列表时返回的令牌
        """
        current_exclude_patterns.reset(token)

    @staticmethod
    def reset_current_user(token: Token) -> None:
        """
        重置当前用户信息

        :param token: 设置用户信息时返回的令牌
        """
        current_user.reset(token)

    @staticmethod
    def clear_all() -> None:
        """
        清除所有上下文变量
        """
        current_exclude_patterns.set(None)
        current_user.set(None)
        current_tenant_id.set(None)
        current_tenant_bypass.set(False)
        current_in_request.set(False)


@contextmanager
def tenant_bypass():
    """临时绕过租户过滤(超管/平台/Worker 引导加载等系统级查询使用)。

    用法：
        with tenant_bypass():
            ... 在此作用域内的 ORM 查询不会被注入租户条件 ...
    """
    token = current_tenant_bypass.set(True)
    try:
        yield
    finally:
        current_tenant_bypass.reset(token)


@contextmanager
def tenant_system():
    """系统/启动期(无登录用户、无租户)合法的全局访问放行。

    语义同 tenant_bypass,但用于标注'这是系统级而非用户级'的调用点(启动初始化、
    引导加载等),与租户默认拒绝(空租户 → 拒绝)配套:凡确需在无租户上下文下访问
    多租户表的系统路径,显式用本管理器放行。
    """
    with tenant_bypass():
        yield
