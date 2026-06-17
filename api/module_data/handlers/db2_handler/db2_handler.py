"""IBM Db2 handler:数仓/OLAP 引擎,复用 SqlConnector + db2+ibm_db。"""

from urllib.parse import quote_plus  # noqa: F401

from module_data.handlers.db2_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class Db2Handler(SqlConnector):
    name = 'db2'
    title = 'IBM Db2'
    driver = 'db2+ibm_db'
    default_port = 50000
    connection_args = connection_args
    connection_args_example = connection_args_example
