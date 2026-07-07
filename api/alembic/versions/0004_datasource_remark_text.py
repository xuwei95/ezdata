"""data_source.remark 由 varchar(500) 升为 TEXT(存业务上下文,供取数 AI 读取)

Revision ID: 0004_ds_remark_text
Revises: 0003_task_timeout
Create Date: generated

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0004_ds_remark_text'
down_revision: Union[str, Sequence[str], None] = '0003_task_timeout'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('data_source', 'remark', existing_type=sa.String(length=500),
                    type_=sa.Text(), existing_nullable=True)


def downgrade() -> None:
    op.alter_column('data_source', 'remark', existing_type=sa.Text(),
                    type_=sa.String(length=500), existing_nullable=True)
