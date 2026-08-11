"""seed 文件管理菜单(sys_menu:文件管理页 + 8 个操作权限按钮)

Revision ID: 0011_file_menu
Revises: 0010_file_maintenance_jobs
Create Date: generated
"""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision: str = '0011_file_menu'
down_revision: str | Sequence[str] | None = '0010_file_maintenance_jobs'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (menu_id, name, parent_id, order_num, path, component, menu_type, perms, icon)
_MENUS = [
    (2500, '文件管理', 1, 6, 'file', 'system/file/index', 'C', 'system:file:list', 'documentation'),
    (2501, '文件查询', 2500, 1, '', '', 'F', 'system:file:query', '#'),
    (2502, '文件下载', 2500, 2, '', '', 'F', 'system:file:download', '#'),
    (2503, '文件删除', 2500, 3, '', '', 'F', 'system:file:delete', '#'),
    (2504, '文件恢复', 2500, 4, '', '', 'F', 'system:file:restore', '#'),
    (2505, '访问控制', 2500, 5, '', '', 'F', 'system:file:acl', '#'),
    (2506, '文件转移', 2500, 6, '', '', 'F', 'system:file:transfer', '#'),
    (2507, '保留策略', 2500, 7, '', '', 'F', 'system:file:retention-policy', '#'),
    (2508, '存储对账', 2500, 8, '', '', 'F', 'system:file:reconcile', '#'),
]


def upgrade() -> None:
    bind = op.get_bind()
    now = datetime.now()
    for mid, name, pid, onum, path, comp, mtype, perms, icon in _MENUS:
        if bind.execute(sa.text('SELECT 1 FROM sys_menu WHERE menu_id=:i'), {'i': mid}).first():
            continue
        bind.execute(
            sa.text(
                'INSERT INTO sys_menu (menu_id,menu_name,parent_id,order_num,path,component,query,route_name,'
                'is_frame,is_cache,menu_type,visible,status,perms,icon,create_by,create_time,remark) '
                'VALUES (:mid,:name,:pid,:onum,:path,:comp,:q,:rn,:iff,:ic,:mtype,:vis,:st,:perms,:icon,:cb,:ct,:rk)'
            ),
            {
                'mid': mid, 'name': name, 'pid': pid, 'onum': onum, 'path': path, 'comp': comp, 'q': '', 'rn': '',
                'iff': 1, 'ic': 0, 'mtype': mtype, 'vis': '0', 'st': '0', 'perms': perms, 'icon': icon,
                'cb': 'admin', 'ct': now, 'rk': '文件管理',
            },
        )


def downgrade() -> None:
    op.get_bind().execute(sa.text('DELETE FROM sys_menu WHERE menu_id BETWEEN 2500 AND 2508'))
