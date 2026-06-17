"""ScyllaDB 数据源 handler。"""

from module_data.handlers.scylla_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.scylla_handler.scylla_handler import ScyllaHandler as Handler

version = '0.0.1'
name = 'scylla'
title = 'ScyllaDB'
description = 'ScyllaDB(CQL,scylla-driver + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
