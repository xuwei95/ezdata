"""Apache Doris 数据源 handler。"""

from module_data.handlers.apache_doris_handler.apache_doris_handler import ApacheDorisHandler as Handler
from module_data.handlers.apache_doris_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'doris'
title = 'Apache Doris'
description = 'Apache Doris 数据源(MySQL 协议,SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
