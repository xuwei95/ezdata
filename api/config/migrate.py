"""可选:启动时自动执行 alembic 迁移(默认关,`AUTO_MIGRATE=true` 开启)。

背景:本项目库多由 `*.sql` 初始化、**不在 alembic 管控下**(无 alembic_version 表)。直接
`alembic upgrade head` 会从 0001_baseline 重跑建表而报错。故本模块:
  1) 已纳管(有 alembic_version)→ 直接 `upgrade head`;
  2) 未纳管 → 先 `stamp` 到基线(`AUTO_MIGRATE_BASELINE`,默认 `0002_seed_system`,即 ezdata.sql 对应的
     "建表+种子"状态)再 `upgrade head`。配合幂等迁移(add/alter 前查存在性),无论新库/滞后库都安全。
迁移失败只记日志、**不阻断启动**。
"""

import os

from utils.log_util import logger


def _truthy(v: str | None) -> bool:
    return str(v or '').strip().lower() in ('1', 'true', 'yes', 'on')


def run_auto_migrate() -> None:
    """按 AUTO_MIGRATE 开关执行 alembic 迁移(同步阻塞,由调用方 threadpool 包裹)。"""
    if not _truthy(os.getenv('AUTO_MIGRATE')):
        return
    try:
        from alembic import command  # noqa: PLC0415
        from alembic.config import Config  # noqa: PLC0415
        from alembic.runtime.migration import MigrationContext  # noqa: PLC0415
        from sqlalchemy import create_engine  # noqa: PLC0415

        from config.database import SYNC_SQLALCHEMY_DATABASE_URL  # noqa: PLC0415

        eng = create_engine(SYNC_SQLALCHEMY_DATABASE_URL)
        try:
            with eng.connect() as conn:
                current = MigrationContext.configure(conn).get_current_revision()
        finally:
            eng.dispose()

        cfg = Config('alembic.ini')
        if current is None:  # 库未纳入 alembic:先标记到基线,避免从 baseline 重跑
            baseline = (os.getenv('AUTO_MIGRATE_BASELINE') or '0002_seed_system').strip()
            logger.info(f'🔖 AUTO_MIGRATE: 库未纳入 alembic,先 stamp 到 {baseline}')
            command.stamp(cfg, baseline)
        logger.info('⛓️ AUTO_MIGRATE: alembic upgrade head …')
        command.upgrade(cfg, 'head')
        logger.info('✅️ AUTO_MIGRATE: 迁移完成')
    except Exception as e:  # noqa: BLE001
        logger.error(f'❌ AUTO_MIGRATE 迁移失败(不阻断启动,可手动处理): {e}')
