"""Elasticsearch 数据源 handler。"""

from module_data.handlers.elasticsearch_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.elasticsearch_handler.elasticsearch_handler import ElasticsearchHandler as Handler

version = '0.0.1'
name = 'elasticsearch'
title = 'Elasticsearch'
description = 'Elasticsearch 数据源(原生 client + dlt resource)'

__all__ = [
           'Handler',
           'connection_args',
           'connection_args_example',
           'description',
           'name',
           'title',
           'version',
]
