"""Amazon Redshift 数据源 handler。"""

from module_data.handlers.redshift_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.redshift_handler.redshift_handler import RedshiftHandler as Handler

version = '0.0.1'
name = 'redshift'
title = 'Amazon Redshift'
description = 'Amazon Redshift 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
