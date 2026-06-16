from urllib.parse import quote_plus

from sqlalchemy import BigInteger, Engine, create_engine, event
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker, with_loader_criteria

from config.env import DataBaseConfig


def build_async_sqlalchemy_database_url() -> str:
    """
    构建异步 SQLAlchemy 数据库连接 URL

    :return: 异步 SQLAlchemy 数据库连接 URL
    """
    if DataBaseConfig.db_type == 'postgresql':
        return (
            f'postgresql+asyncpg://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
            f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
        )
    return (
        f'mysql+asyncmy://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
        f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    )


ASYNC_SQLALCHEMY_DATABASE_URL = build_async_sqlalchemy_database_url()


def build_sync_sqlalchemy_database_url() -> str:
    """
    构建同步 SQLAlchemy 数据库连接 URL

    :return: 同步 SQLAlchemy 数据库连接 URL
    """
    if DataBaseConfig.db_type == 'postgresql':
        return (
            f'postgresql+psycopg2://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
            f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
        )
    return (
        f'mysql+pymysql://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
        f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    )


SYNC_SQLALCHEMY_DATABASE_URL = build_sync_sqlalchemy_database_url()


def create_async_db_engine(echo: bool | None = None) -> AsyncEngine:
    """
    创建异步 SQLAlchemy Engine

    :param echo: 可选，是否输出 SQLAlchemy SQL 日志
    :return: 异步 SQLAlchemy Engine
    """
    return create_async_engine(
        ASYNC_SQLALCHEMY_DATABASE_URL,
        echo=DataBaseConfig.db_echo if echo is None else echo,
        max_overflow=DataBaseConfig.db_max_overflow,
        pool_size=DataBaseConfig.db_pool_size,
        pool_recycle=DataBaseConfig.db_pool_recycle,
        pool_timeout=DataBaseConfig.db_pool_timeout,
    )


def create_sync_db_engine(echo: bool | None = None) -> Engine:
    """
    创建同步 SQLAlchemy Engine

    :param echo: 可选，是否输出 SQLAlchemy SQL 日志
    :return: 同步 SQLAlchemy Engine
    """
    return create_engine(
        SYNC_SQLALCHEMY_DATABASE_URL,
        echo=DataBaseConfig.db_echo if echo is None else echo,
        max_overflow=DataBaseConfig.db_max_overflow,
        pool_size=DataBaseConfig.db_pool_size,
        pool_recycle=DataBaseConfig.db_pool_recycle,
        pool_timeout=DataBaseConfig.db_pool_timeout,
        pool_pre_ping=True,  # 连接前探活，避免 Celery worker(solo)空闲后命中失效连接而卡住
    )


def create_async_session_local(engine: AsyncEngine) -> async_sessionmaker:
    """
    创建异步 Session 工厂

    :param engine: 异步 SQLAlchemy Engine
    :return: 异步 Session 工厂
    """
    return async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_sync_session_local(engine: Engine) -> sessionmaker:
    """
    创建同步 Session 工厂

    :param engine: 同步 SQLAlchemy Engine
    :return: 同步 Session 工厂
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


async_engine = create_async_db_engine()
AsyncSessionLocal = create_async_session_local(async_engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class TenantMixin:
    """
    多租户隔离 Mixin。

    继承此类的 ORM 模型会：
    - 拥有 tenant_id 列(值 = 顶级部门ID)
    - 查询时被全局事件自动注入 `tenant_id == 当前租户` 过滤(见下方 do_orm_execute)
    - 新增时被自动盖上当前租户的 tenant_id(见下方 before_flush)
    """

    tenant_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True, comment='租户ID(顶级部门)')


# ---------------------------------------------------------------------------
# 多租户全局过滤 / 写入盖章
#
# 监听 SQLAlchemy 基类 Session 的事件，异步(AsyncSession 底层复用同步 Session)与
# 同步(Celery)会话都会生效。上下文中存在租户ID且未 bypass 时：
#   - 所有针对 TenantMixin 子类的 ORM SELECT 自动追加 tenant_id 过滤
#   - flush 前给新增的 TenantMixin 实例自动填充 tenant_id
# 上下文未设置租户(系统/匿名/启动加载)或显式 bypass(超管/Worker引导)时不过滤。
# ---------------------------------------------------------------------------
@event.listens_for(Session, 'do_orm_execute')
def _tenant_filter_orm_execute(orm_execute_state) -> None:  # noqa: ANN001
    # 仅处理顶层 ORM SELECT；跳过列刷新与关系懒加载(由 include_aliases 覆盖关联)
    if not (
        orm_execute_state.is_select
        and not orm_execute_state.is_column_load
        and not orm_execute_state.is_relationship_load
    ):
        return
    from common.context import RequestContext

    tenant_id = RequestContext.get_effective_tenant_id()
    if tenant_id is None:
        return
    orm_execute_state.statement = orm_execute_state.statement.options(
        with_loader_criteria(
            TenantMixin,
            lambda cls: cls.tenant_id == tenant_id,
            include_aliases=True,
        )
    )


@event.listens_for(Session, 'before_flush')
def _tenant_stamp_before_flush(session: Session, flush_context, instances) -> None:  # noqa: ANN001
    from common.context import RequestContext

    tenant_id = RequestContext.get_effective_tenant_id()
    if tenant_id is None:
        return
    for obj in session.new:
        if isinstance(obj, TenantMixin) and getattr(obj, 'tenant_id', None) is None:
            obj.tenant_id = tenant_id
