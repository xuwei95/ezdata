"""Weaviate 向量数据源 handler。"""

from module_data.handlers.weaviate_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.weaviate_handler.weaviate_handler import WeaviateHandler as Handler

version = '0.0.1'
name = 'weaviate'
title = 'Weaviate'
description = 'Weaviate 向量库(委托 Agno)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
