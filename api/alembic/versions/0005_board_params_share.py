"""data_analysis_template 增加 params / refresh_interval / share_token 列(看板参数化+自动刷新+匿名分享)

Revision ID: 0005_board_params_share
Revises: 0004_ds_remark_text
Create Date: generated

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0005_board_params_share'
down_revision: str | Sequence[str] | None = '0004_ds_remark_text'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = 'data_analysis_template'


def upgrade() -> None:
    # 幂等:列已存在(如从含该列的 ezdata.sql 建库)则跳过
    bind = op.get_bind()
    cols = [c['name'] for c in sa.inspect(bind).get_columns(_TABLE)]
    if 'params' not in cols:
        op.add_column(_TABLE, sa.Column('params', sa.JSON(), nullable=True, comment='看板变量定义+当前值'))
    if 'refresh_interval' not in cols:
        op.add_column(
            _TABLE,
            sa.Column('refresh_interval', sa.Integer(), nullable=True, server_default='0', comment='自动刷新间隔(秒,0=不刷新)'),
        )
    if 'share_token' not in cols:
        op.add_column(_TABLE, sa.Column('share_token', sa.String(length=64), nullable=True, comment='匿名分享令牌'))
        op.create_index('ix_data_analysis_template_share_token', _TABLE, ['share_token'])


def downgrade() -> None:
    op.drop_index('ix_data_analysis_template_share_token', table_name=_TABLE)
    op.drop_column(_TABLE, 'share_token')
    op.drop_column(_TABLE, 'refresh_interval')
    op.drop_column(_TABLE, 'params')
