"""Amazon Athena 数据源 handler。"""

from module_data.handlers.athena_handler.athena_handler import AthenaHandler as Handler
from module_data.handlers.athena_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'athena'
title = 'Amazon Athena'
description = 'Amazon Athena 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
