"""Apache Cassandra 数据源 handler。"""

from module_data.handlers.cassandra_handler.cassandra_handler import CassandraHandler as Handler
from module_data.handlers.cassandra_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'cassandra'
title = 'Apache Cassandra'
description = 'Cassandra(CQL,cassandra-driver + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
