"""Google BigQuery 数据源 handler。"""

from module_data.handlers.bigquery_handler.bigquery_handler import BigQueryHandler as Handler
from module_data.handlers.bigquery_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'bigquery'
title = 'Google BigQuery'
description = 'Google BigQuery 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
