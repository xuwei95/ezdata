"""task 增加 timeout 列(任务超时秒:0=全局默认/-1=不限/>0=自定义)

Revision ID: 0003_task_timeout
Revises: 0002_seed_system
Create Date: generated

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0003_task_timeout'
down_revision: Union[str, Sequence[str], None] = '0002_seed_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'task',
        sa.Column('timeout', sa.Integer(), nullable=True, server_default='0',
                  comment='任务超时(秒):0=用全局默认,-1=不限(流式/超长),>0=自定义'),
    )


def downgrade() -> None:
    op.drop_column('task', 'timeout')
