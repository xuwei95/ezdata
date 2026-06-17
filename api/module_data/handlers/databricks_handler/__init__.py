"""Databricks 数据源 handler。"""

from module_data.handlers.databricks_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.databricks_handler.databricks_handler import DatabricksHandler as Handler

version = '0.0.1'
name = 'databricks'
title = 'Databricks'
description = 'Databricks 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
