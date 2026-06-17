"""Amazon Redshift handler:PostgreSQL 协议,复用 SqlConnector。"""

from module_data.handlers.redshift_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class RedshiftHandler(SqlConnector):
    name = 'redshift'
    title = 'Amazon Redshift'
    driver = 'postgresql+psycopg2'      # Redshift 兼容 PG 协议;如需 IAM/专属优化可换 redshift+redshift_connector
    default_port = 5439
    connection_args = connection_args
    connection_args_example = connection_args_example
