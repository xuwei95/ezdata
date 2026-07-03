"""Oracle handler:SqlConnector(oracledb 驱动),支持 dsn / service_name / sid。"""

from urllib.parse import quote_plus

from ezdata.handlers.oracle_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class OracleHandler(SqlConnector):
    name = 'oracle'
    title = 'Oracle'
    driver = 'oracle+oracledb'
    default_port = 1521
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        user = self.arg('user', 'username', default='')
        pwd = quote_plus(str(self.arg('password', default='')))
        dsn = self.arg('dsn')
        if dsn:                                              # 直接给 DSN
            return f'oracle+oracledb://{user}:{pwd}@{dsn}'
        host = self.arg('host', default='127.0.0.1')
        port = self.arg('port', default=self.default_port)
        service_name = self.arg('service_name')
        if service_name:
            return f'oracle+oracledb://{user}:{pwd}@{host}:{port}/?service_name={service_name}'
        sid = self.arg('sid', default='')
        return f'oracle+oracledb://{user}:{pwd}@{host}:{port}/{sid}'
