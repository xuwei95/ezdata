"""OpenGauss 数据源 handler。"""

from module_data.handlers.opengauss_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.opengauss_handler.opengauss_handler import OpenGaussHandler as Handler

version = '0.0.1'
name = 'opengauss'
title = 'OpenGauss'
description = 'OpenGauss 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
