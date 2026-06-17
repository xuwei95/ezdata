"""Pinecone 向量数据源 handler。"""

from module_data.handlers.pinecone_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.pinecone_handler.pinecone_handler import PineconeHandler as Handler

version = '0.0.1'
name = 'pinecone'
title = 'Pinecone'
description = 'Pinecone 向量库(委托 Agno)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
