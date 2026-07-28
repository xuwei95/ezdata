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
    from common.context import RequestContext

    RequestContext.mark_request_scope()
    async with AsyncSessionLocal() as current_db:
        yield current_db


async def init_create_table() -> None:
    """
    应用启动时初始化数据库连接

    :return:
    """
    logger.info('🔎 初始化数据库连接...')
    import asyncio

    from fastapi.concurrency import run_in_threadpool
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, OperationalError

    from config.migrate import run_auto_migrate

    # DB 就绪重试:整体 compose 启动时,MySQL 的 healthcheck 可能在 TCP 尚未接受连接前就转绿
    # (mysqladmin ping 走 socket;首次 initdb 期还有个 --skip-networking 的临时服务器),导致后端首连被拒。
    # 这里带退避重试等 DB 真正就绪,使后端不依赖 compose 的 depends_on/healthcheck/restart 兜底也能稳起。
    last_err: Exception | None = None
    for attempt in range(1, 31):  # 最多 ~60s(每次 2s)
        try:
            async with async_engine.connect() as conn:
                await conn.execute(text('SELECT 1'))
            break
        except (OperationalError, DBAPIError, OSError) as e:
            last_err = e
            logger.warning(f'⏳ DB 未就绪(第 {attempt}/30 次),2s 后重试: {str(e).splitlines()[0][:120]}')
            await asyncio.sleep(2)
    else:
        logger.error(f'❌ DB 连接重试 30 次仍失败: {last_err}')
        raise last_err  # type: ignore[misc]

    # 可选:启动时自动 alembic 迁移(AUTO_MIGRATE=true 才执行,默认关);先于 create_all 跑,先改表结构再建缺失表。
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
