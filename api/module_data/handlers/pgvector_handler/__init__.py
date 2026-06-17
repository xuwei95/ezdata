"""pgvector 数据源 handler。"""

from module_data.handlers.pgvector_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.pgvector_handler.pgvector_handler import PgVectorHandler as Handler

version = '0.0.1'
name = 'pgvector'
title = 'pgvector (PostgreSQL)'
description = 'pgvector 数据源(PostgreSQL + dlt;向量检索后续加)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
