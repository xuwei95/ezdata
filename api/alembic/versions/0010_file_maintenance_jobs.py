"""seed 文件管理后台维护定时任务(sys_job:保留提醒/回收站清理/存储对账)

Revision ID: 0010_file_maintenance_jobs
Revises: 0009_file_management
Create Date: generated

默认 status='1'(暂停),需要时在「定时任务」页启用。invoke_target 指向 module_task_schedule.file_jobs。
"""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision: str = '0010_file_maintenance_jobs'
down_revision: str | Sequence[str] | None = '0009_file_management'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_JOBS = [
    ('文件-保留期限提醒扫描', 'module_task_schedule.file_jobs.scan_retention_reminders', '0 0 2 * * ?'),
    ('文件-回收站清理', 'module_task_schedule.file_jobs.purge_recycle_bin', '0 0 3 * * ?'),
    ('文件-存储对账', 'module_task_schedule.file_jobs.reconcile_file_storage', '0 0 4 ? * 1'),
]


def upgrade() -> None:
    bind = op.get_bind()
    now = datetime.now()
    for name, target, cron in _JOBS:
        exists = bind.execute(
            sa.text('SELECT 1 FROM sys_job WHERE invoke_target = :t LIMIT 1'), {'t': target}
        ).first()
        if exists:
            continue
        bind.execute(
            sa.text(
                'INSERT INTO sys_job (job_name, job_group, job_executor, invoke_target, cron_expression, '
                'misfire_policy, concurrent, status, create_by, create_time, remark, tenant_id) '
                'VALUES (:n, :g, :e, :t, :c, :m, :cc, :s, :cb, :ct, :r, :tid)'
            ),
            {
                'n': name, 'g': 'default', 'e': 'default', 't': target, 'c': cron,
                'm': '3', 'cc': '1', 's': '1', 'cb': 'admin', 'ct': now, 'r': '文件管理维护(默认暂停)', 'tid': 100,
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    for _name, target, _cron in _JOBS:
        bind.execute(sa.text('DELETE FROM sys_job WHERE invoke_target = :t'), {'t': target})
