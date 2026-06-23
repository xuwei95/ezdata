"""AKShare 数据源 handler。"""

from module_data.handlers.akshare_handler.akshare_handler import AKShareHandler as Handler
from module_data.handlers.akshare_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'akshare'
title = 'AKShare 财经数据'
description = 'AKShare(中国财经数据接口,免 key 只读;表=接口函数名,查询参数=函数参数)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
