"""task 增加 timeout 列(任务超时秒:0=全局默认/-1=不限/>0=自定义)

Revision ID: 0003_task_timeout
Revises: 0002_seed_system
Create Date: generated

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0003_task_timeout'
down_revision: str | Sequence[str] | None = '0002_seed_system'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 幂等:列已存在(如从含该列的 ezdata.sql 建库)则跳过,便于 stamp 基线后重跑
    bind = op.get_bind()
    cols = [c['name'] for c in sa.inspect(bind).get_columns('task')]
    if 'timeout' not in cols:
        op.add_column(
            'task',
            sa.Column(
                'timeout',
                sa.Integer(),
                nullable=True,
                server_default='0',
                comment='任务超时(秒):0=用全局默认,-1=不限(流式/超长),>0=自定义',
            ),
        )


def downgrade() -> None:
    op.drop_column('task', 'timeout')
