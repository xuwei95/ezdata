"""MariaDB 数据源 handler。"""

from module_data.handlers.mariadb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.mariadb_handler.mariadb_handler import MariaDBHandler as Handler

version = '0.0.1'
name = 'mariadb'
title = 'MariaDB'
description = 'MariaDB 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
