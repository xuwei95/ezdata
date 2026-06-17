"""ChromaDB 向量数据源 handler。"""

from module_data.handlers.chromadb_handler.chromadb_handler import ChromaDBHandler as Handler
from module_data.handlers.chromadb_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'chromadb'
title = 'ChromaDB'
description = 'ChromaDB 向量库(委托 Agno)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
