"""TDengine 数据源 handler。"""

from module_data.handlers.tdengine_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.tdengine_handler.tdengine_handler import TDengineHandler as Handler

version = '0.0.1'
name = 'tdengine'
title = 'TDengine'
description = 'TDengine(taospy REST,SQL + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
