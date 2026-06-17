"""Oracle 数据源 handler。"""

from module_data.handlers.oracle_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.oracle_handler.oracle_handler import OracleHandler as Handler

version = '0.0.1'
name = 'oracle'
title = 'Oracle'
description = 'Oracle 数据源(SQLAlchemy + dlt)'

__all__ = [
           'Handler',
           'connection_args',
           'connection_args_example',
           'description',
           'name',
           'title',
           'version',
]
