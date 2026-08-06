"""新增 sys_notice_user 公告收件人表(定向投递;无行=广播)

Revision ID: 0007_notice_user
Revises: 0006_notice_read
Create Date: generated

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0007_notice_user'
down_revision: str | Sequence[str] | None = '0006_notice_read'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = 'sys_notice_user'


def upgrade() -> None:
    # 幂等:表已存在(如 create_all 已建)则跳过
    bind = op.get_bind()
    if _TABLE in sa.inspect(bind).get_table_names():
        return
    op.create_table(
        _TABLE,
        sa.Column(
            'id',
            sa.BigInteger().with_variant(sa.Integer, 'sqlite'),
            autoincrement=True,
            nullable=False,
            comment='主键',
        ),
        sa.Column('notice_id', sa.Integer(), nullable=False, comment='公告ID'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='收件人用户ID'),
        sa.Column('create_time', sa.DateTime(), nullable=False, comment='投递时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('notice_id', 'user_id', name='uk_notice_user'),
        comment='公告收件人表',
    )


def downgrade() -> None:
    op.drop_table(_TABLE)
