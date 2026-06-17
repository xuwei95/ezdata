"""MatrixOne 数据源 handler。"""

from module_data.handlers.matrixone_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.matrixone_handler.matrixone_handler import MatrixOneHandler as Handler

version = '0.0.1'
name = 'matrixone'
title = 'MatrixOne'
description = 'MatrixOne 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
