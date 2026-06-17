"""Rockset 数据源 handler。"""

from module_data.handlers.rockset_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.rockset_handler.rockset_handler import RocksetHandler as Handler

version = '0.0.1'
name = 'rockset'
title = 'Rockset'
description = 'Rockset 数据源(MySQL 协议,SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
