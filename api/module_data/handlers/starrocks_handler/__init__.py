"""StarRocks 数据源 handler。"""

from module_data.handlers.starrocks_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.starrocks_handler.starrocks_handler import StarRocksHandler as Handler

version = '0.0.1'
name = 'starrocks'
title = 'StarRocks'
description = 'StarRocks 数据源(MySQL 协议,SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
