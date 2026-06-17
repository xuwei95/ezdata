"""EdgelessDB 数据源 handler。"""

from module_data.handlers.edgelessdb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.edgelessdb_handler.edgelessdb_handler import EdgelessDBHandler as Handler

version = '0.0.1'
name = 'edgelessdb'
title = 'EdgelessDB'
description = 'EdgelessDB 数据源(MySQL 协议,SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
