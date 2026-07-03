"""Snowflake handler:SqlConnector + snowflake-sqlalchemy,自定义 URL(account/warehouse/role)。"""

from urllib.parse import quote_plus, urlencode

from ezdata.handlers.snowflake_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class SnowflakeHandler(SqlConnector):
    name = 'snowflake'
    title = 'Snowflake'
    driver = 'snowflake'
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        user = quote_plus(str(self.arg('user', 'username', default='')))
        pwd = quote_plus(str(self.arg('password', default='')))
        account = self.arg('account')
        database = self.arg('database', default='')
        schema = self.arg('schema', default='')
        path = f'{database}/{schema}' if schema else database
        params = {k: v for k, v in {
            'warehouse': self.arg('warehouse'), 'role': self.arg('role'),
        }.items() if v}
        qs = f'?{urlencode(params)}' if params else ''
        return f'snowflake://{user}:{pwd}@{account}/{path}{qs}'
