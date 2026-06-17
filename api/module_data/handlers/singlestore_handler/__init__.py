"""SingleStore 数据源 handler。"""

from module_data.handlers.singlestore_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.singlestore_handler.singlestore_handler import SingleStoreHandler as Handler

version = '0.0.1'
name = 'singlestore'
title = 'SingleStore'
description = 'SingleStore 数据源(MySQL 协议,SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
