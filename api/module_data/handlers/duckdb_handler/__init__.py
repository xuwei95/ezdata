"""DuckDB 数据源 handler。"""

from module_data.handlers.duckdb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.duckdb_handler.duckdb_handler import DuckDBHandler as Handler

version = '0.0.1'
name = 'duckdb'
title = 'DuckDB'
description = 'DuckDB 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
