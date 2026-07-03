"""QuestDB handler:PostgreSQL 协议。"""

from ezdata.handlers.questdb_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class QuestDBHandler(SqlConnector):
    name = 'questdb'
    title = 'QuestDB'
    driver = 'postgresql+psycopg2'
    default_port = 8812
    connection_args = connection_args
    connection_args_example = connection_args_example
