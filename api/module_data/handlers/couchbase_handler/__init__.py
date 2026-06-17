"""Couchbase 数据源 handler。"""

from module_data.handlers.couchbase_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.couchbase_handler.couchbase_handler import CouchbaseHandler as Handler

version = '0.0.1'
name = 'couchbase'
title = 'Couchbase'
description = 'Couchbase(N1QL,couchbase SDK + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
