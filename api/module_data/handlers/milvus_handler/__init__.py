"""Milvus 向量数据源 handler。"""

from module_data.handlers.milvus_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.milvus_handler.milvus_handler import MilvusHandler as Handler

version = '0.0.1'
name = 'milvus'
title = 'Milvus'
description = 'Milvus 向量库(委托 Agno)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
