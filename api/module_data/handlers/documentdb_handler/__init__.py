"""Amazon DocumentDB 数据源 handler。"""

from module_data.handlers.documentdb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.documentdb_handler.documentdb_handler import DocumentDBHandler as Handler

version = '0.0.1'
name = 'documentdb'
title = 'Amazon DocumentDB'
description = 'DocumentDB(MongoDB 兼容,pymongo + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
