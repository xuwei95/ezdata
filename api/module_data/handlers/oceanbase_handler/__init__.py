"""OceanBase 数据源 handler。"""

from module_data.handlers.oceanbase_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.oceanbase_handler.oceanbase_handler import OceanBaseHandler as Handler

version = '0.0.1'
name = 'oceanbase'
title = 'OceanBase'
description = 'OceanBase 数据源(MySQL 协议,SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
