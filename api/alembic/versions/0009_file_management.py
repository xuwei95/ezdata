"""新增文件管理子系统 8 表(移植自 RuoYi-Vue3-FastAPI v1.10.0,SysFileInfo 加多租户)

Revision ID: 0009_file_management
Revises: 0008_data_access_log
Create Date: generated

表:sys_file_info / sys_file_reference / sys_file_retention_policy / sys_file_retention_notice /
   sys_file_acl / sys_file_access_log / sys_file_reconcile_run / sys_file_reconcile_issue
列/索引/约束以 module_admin/entity/do/file_do.py 的 DO 定义为准,故直接委托 ORM metadata
建表(checkfirst 幂等),避免手工转写 260 行 DDL 与 DO 漂移。
"""

from collections.abc import Sequence

from alembic import op

revision: str = '0009_file_management'
down_revision: str | Sequence[str] | None = '0008_data_access_log'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    'sys_file_info',
    'sys_file_reference',
    'sys_file_retention_policy',
    'sys_file_retention_notice',
    'sys_file_acl',
    'sys_file_access_log',
    'sys_file_reconcile_run',
    'sys_file_reconcile_issue',
)


def _models() -> list:
    from module_admin.entity.do import file_do

    return [
        file_do.SysFileInfo,
        file_do.SysFileReference,
        file_do.SysFileRetentionPolicy,
        file_do.SysFileRetentionNotice,
        file_do.SysFileAcl,
        file_do.SysFileAccessLog,
        file_do.SysFileReconcileRun,
        file_do.SysFileReconcileIssue,
    ]


def upgrade() -> None:
    bind = op.get_bind()
    for model in _models():
        model.__table__.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for model in reversed(_models()):
        model.__table__.drop(bind=bind, checkfirst=True)
