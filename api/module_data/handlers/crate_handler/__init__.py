"""CrateDB 数据源 handler。"""

from module_data.handlers.crate_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.crate_handler.crate_handler import CrateHandler as Handler

version = '0.0.1'
name = 'crate'
title = 'CrateDB'
description = 'CrateDB 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
