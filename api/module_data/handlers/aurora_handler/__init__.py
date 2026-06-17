"""Amazon Aurora (MySQL) 数据源 handler。"""

from module_data.handlers.aurora_handler.aurora_handler import AuroraHandler as Handler
from module_data.handlers.aurora_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'aurora'
title = 'Amazon Aurora (MySQL)'
description = 'Amazon Aurora (MySQL) 数据源(MySQL 协议,SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
