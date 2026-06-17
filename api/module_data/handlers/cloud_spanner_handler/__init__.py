"""Google Cloud Spanner 数据源 handler。"""

from module_data.handlers.cloud_spanner_handler.cloud_spanner_handler import CloudSpannerHandler as Handler
from module_data.handlers.cloud_spanner_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'cloud_spanner'
title = 'Google Cloud Spanner'
description = 'Google Cloud Spanner 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
