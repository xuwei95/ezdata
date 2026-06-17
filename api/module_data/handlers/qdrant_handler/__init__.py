"""Qdrant 向量数据源 handler。"""

from module_data.handlers.qdrant_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.qdrant_handler.qdrant_handler import QdrantHandler as Handler

version = '0.0.1'
name = 'qdrant'
title = 'Qdrant'
description = 'Qdrant 向量库(委托 Agno)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
