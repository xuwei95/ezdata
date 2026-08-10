"""新增 data_access_log 数据访问审计表(谁在何时查了哪个源/表)

Revision ID: 0008_data_access_log
Revises: 0007_notice_user
Create Date: generated

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0008_data_access_log'
down_revision: str | Sequence[str] | None = '0007_notice_user'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = 'data_access_log'


def upgrade() -> None:
    # 幂等:表已存在(如 create_all 已建)则跳过
    bind = op.get_bind()
    if _TABLE in sa.inspect(bind).get_table_names():
        return
    op.create_table(
        _TABLE,
        sa.Column(
            'access_id',
            sa.BigInteger().with_variant(sa.Integer, 'sqlite'),
            autoincrement=True,
            nullable=False,
            comment='主键',
        ),
        sa.Column('tenant_id', sa.BigInteger(), nullable=True, comment='租户ID'),
        sa.Column('user_id', sa.BigInteger(), nullable=True, comment='访问用户ID'),
        sa.Column('user_name', sa.String(length=64), nullable=True, comment='访问用户名'),
        sa.Column('datasource_code', sa.String(length=200), nullable=True, comment='数据源编码'),
        sa.Column('source_type', sa.String(length=50), nullable=True, comment='数据源类型'),
        sa.Column('model_id', sa.String(length=36), nullable=True, comment='数据模型ID(如有)'),
        sa.Column('object_name', sa.String(length=255), nullable=True, comment='目标表/索引/集合'),
        sa.Column('access_type', sa.String(length=20), nullable=True, comment='query/search/aggregate/preview/api'),
        sa.Column('statement', sa.Text(), nullable=True, comment='原始查询语句/DSL/参数'),
        sa.Column('filters', sa.JSON(), nullable=True, comment='结构化过滤条件'),
        sa.Column('result_rows', sa.Integer(), nullable=True, comment='返回行数'),
        sa.Column('exec_ms', sa.Integer(), nullable=True, comment='执行耗时(ms)'),
        sa.Column('success', sa.SmallInteger(), server_default='1', nullable=True, comment='1成功0失败'),
        sa.Column('error_msg', sa.Text(), nullable=True, comment='失败原因'),
        sa.Column('trace_id', sa.String(length=64), nullable=True, comment='链路追踪ID'),
        sa.Column('request_path', sa.String(length=255), nullable=True, comment='HTTP 路径'),
        sa.Column('source', sa.String(length=20), server_default='web', nullable=True, comment='web/api/agent/task'),
        sa.Column('access_time', sa.DateTime(), nullable=True, comment='访问时间'),
        sa.PrimaryKeyConstraint('access_id'),
        comment='数据访问审计日志',
    )
    op.create_index('ix_data_access_log_tenant_id', _TABLE, ['tenant_id'])
    op.create_index('ix_data_access_log_user_name', _TABLE, ['user_name'])
    op.create_index('ix_data_access_log_datasource_code', _TABLE, ['datasource_code'])
    op.create_index('ix_data_access_log_object_name', _TABLE, ['object_name'])
    op.create_index('ix_data_access_log_trace_id', _TABLE, ['trace_id'])
    op.create_index('ix_data_access_log_access_time', _TABLE, ['access_time'])


def downgrade() -> None:
    op.drop_table(_TABLE)
