"""QuestDB 数据源 handler。"""

from module_data.handlers.questdb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.questdb_handler.questdb_handler import QuestDBHandler as Handler

version = '0.0.1'
name = 'questdb'
title = 'QuestDB'
description = 'QuestDB 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
