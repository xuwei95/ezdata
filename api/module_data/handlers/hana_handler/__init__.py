"""SAP HANA 数据源 handler。"""

from module_data.handlers.hana_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.hana_handler.hana_handler import HanaHandler as Handler

version = '0.0.1'
name = 'hana'
title = 'SAP HANA'
description = 'SAP HANA 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
