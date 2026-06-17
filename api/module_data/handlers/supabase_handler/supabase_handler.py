"""Supabase handler:复用 SqlConnector + postgresql+psycopg2。"""

from urllib.parse import quote_plus  # noqa: F401

from module_data.handlers.sql_base import SqlConnector
from module_data.handlers.supabase_handler.connection_args import connection_args, connection_args_example


class SupabaseHandler(SqlConnector):
    name = 'supabase'
    title = 'Supabase'
    driver = 'postgresql+psycopg2'
    default_port = 5432
    connection_args = connection_args
    connection_args_example = connection_args_example
