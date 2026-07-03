"""Google Cloud SQL handler:按 db_engine 选 mysql/postgres/mssql 驱动。"""

from urllib.parse import quote_plus

from ezdata.handlers.cloud_sql_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector

_DRIVERS = {
    'mysql': ('mysql+pymysql', 3306),
    'postgres': ('postgresql+psycopg2', 5432),
    'postgresql': ('postgresql+psycopg2', 5432),
    'mssql': ('mssql+pymssql', 1433),
    'sqlserver': ('mssql+pymssql', 1433),
}


class CloudSQLHandler(SqlConnector):
    name = 'cloud_sql'
    title = 'Google Cloud SQL'
    driver = 'mysql+pymysql'
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        engine = str(self.arg('db_engine', default='mysql')).lower()
        driver, default_port = _DRIVERS.get(engine, ('mysql+pymysql', 3306))
        host = self.arg('host', default='127.0.0.1')
        port = self.arg('port', default=default_port)
        user = self.arg('user', 'username', default='')
        pwd = quote_plus(str(self.arg('password', default='')))
        database = self.arg('database', default='')
        return f'{driver}://{user}:{pwd}@{host}:{port}/{database}'
