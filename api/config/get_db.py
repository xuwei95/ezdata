from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal, Base, async_engine
from utils.log_util import logger


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    每一个请求处理完毕后会关闭当前连接，不同的请求使用不同的连接

    :return:
    """
    # 标记 HTTP 请求作用域:仅在此作用域内对"空租户"默认拒绝(后台用独立同步会话,不经此处)
    from common.context import RequestContext  # noqa: PLC0415

    RequestContext.mark_request_scope()
    async with AsyncSessionLocal() as current_db:
        yield current_db


async def init_create_table() -> None:
    """
    应用启动时初始化数据库连接

    :return:
    """
    logger.info('🔎 初始化数据库连接...')
    # 可选:启动时自动 alembic 迁移(AUTO_MIGRATE=true 才执行,默认关);先于 create_all 跑,先改表结构再建缺失表。
    from fastapi.concurrency import run_in_threadpool  # noqa: PLC0415

    from config.migrate import run_auto_migrate  # noqa: PLC0415

    await run_in_threadpool(run_auto_migrate)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info('✅️ 数据库连接成功')


async def close_async_engine() -> None:
    """
    应用关闭时释放数据库连接池

    :return:
    """
    await async_engine.dispose()
