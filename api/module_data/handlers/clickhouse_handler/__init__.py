"""ClickHouse 数据源 handler。"""

from module_data.handlers.clickhouse_handler.clickhouse_handler import ClickHouseHandler as Handler
from module_data.handlers.clickhouse_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'clickhouse'
title = 'ClickHouse'
description = 'ClickHouse 数据源(SQLAlchemy + dlt)'

__all__ = [
           'Handler',
           'connection_args',
           'connection_args_example',
           'description',
           'name',
           'title',
           'version',
]
