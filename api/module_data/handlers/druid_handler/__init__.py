"""Apache Druid 数据源 handler。"""

from module_data.handlers.druid_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.druid_handler.druid_handler import DruidHandler as Handler

version = '0.0.1'
name = 'druid'
title = 'Apache Druid'
description = 'Apache Druid 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
