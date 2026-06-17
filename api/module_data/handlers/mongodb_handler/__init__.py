"""MongoDB 数据源 handler。"""

from module_data.handlers.mongodb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.mongodb_handler.mongodb_handler import MongoDBHandler as Handler

version = '0.0.1'
name = 'mongodb'
title = 'MongoDB'
description = 'MongoDB 数据源(原生 pymongo + dlt resource)'

__all__ = [
           'Handler',
           'connection_args',
           'connection_args_example',
           'description',
           'name',
           'title',
           'version',
]
