"""LanceDB 向量数据源 handler。"""

from module_data.handlers.lancedb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.lancedb_handler.lancedb_handler import LanceDBHandler as Handler

version = '0.0.1'
name = 'lancedb'
title = 'LanceDB'
description = 'LanceDB 向量库(委托 Agno)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
