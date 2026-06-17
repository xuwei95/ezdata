"""Apache Impala 数据源 handler。"""

from module_data.handlers.impala_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.impala_handler.impala_handler import ImpalaHandler as Handler

version = '0.0.1'
name = 'impala'
title = 'Apache Impala'
description = 'Apache Impala 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
