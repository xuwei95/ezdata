"""IBM Informix 数据源 handler。"""

from module_data.handlers.informix_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.informix_handler.informix_handler import InformixHandler as Handler

version = '0.0.1'
name = 'informix'
title = 'IBM Informix'
description = 'IBM Informix 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
