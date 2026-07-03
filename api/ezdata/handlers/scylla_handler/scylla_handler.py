"""ScyllaDB handler:Cassandra 兼容(CQL),继承 CassandraHandler。"""

from ezdata.handlers.cassandra_handler.cassandra_handler import CassandraHandler
from ezdata.handlers.scylla_handler.connection_args import connection_args, connection_args_example


class ScyllaHandler(CassandraHandler):
    name = 'scylla'
    title = 'ScyllaDB'
    connection_args = connection_args
    connection_args_example = connection_args_example
