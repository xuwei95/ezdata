"""OpenSearch 数据源 handler。"""

from module_data.handlers.opensearch_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.opensearch_handler.opensearch_handler import OpenSearchHandler as Handler

version = '0.0.1'
name = 'opensearch'
title = 'OpenSearch'
description = 'OpenSearch(ES 兼容,原生 client + dlt resource)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
