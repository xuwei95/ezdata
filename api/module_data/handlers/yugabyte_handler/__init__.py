"""YugabyteDB 数据源 handler。"""

from module_data.handlers.yugabyte_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.yugabyte_handler.yugabyte_handler import YugabyteHandler as Handler

version = '0.0.1'
name = 'yugabyte'
title = 'YugabyteDB'
description = 'YugabyteDB 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
