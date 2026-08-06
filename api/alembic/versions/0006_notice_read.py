"""新增 sys_notice_read 公告已读记录表(顶部通知/已读功能后端)

Revision ID: 0006_notice_read
Revises: 0005_board_params_share
Create Date: generated

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0006_notice_read'
down_revision: str | Sequence[str] | None = '0005_board_params_share'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = 'sys_notice_read'


def upgrade() -> None:
    # 幂等:表已存在(如 create_all 先建或从含该表的 sql 建库)则跳过
    bind = op.get_bind()
    if _TABLE in sa.inspect(bind).get_table_names():
        return
    op.create_table(
        _TABLE,
        sa.Column(
            'read_id',
            sa.BigInteger().with_variant(sa.Integer, 'sqlite'),
            autoincrement=True,
            nullable=False,
            comment='已读主键',
        ),
        sa.Column('notice_id', sa.Integer(), nullable=False, comment='公告ID'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='用户ID'),
        sa.Column('read_time', sa.DateTime(), nullable=False, comment='阅读时间'),
        sa.PrimaryKeyConstraint('read_id'),
        sa.UniqueConstraint('user_id', 'notice_id', name='uk_user_notice'),
        comment='公告已读记录表',
    )


def downgrade() -> None:
    op.drop_table(_TABLE)
