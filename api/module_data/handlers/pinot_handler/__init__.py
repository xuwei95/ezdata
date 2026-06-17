"""Apache Pinot 数据源 handler。"""

from module_data.handlers.pinot_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.pinot_handler.pinot_handler import PinotHandler as Handler

version = '0.0.1'
name = 'pinot'
title = 'Apache Pinot'
description = 'Apache Pinot 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
