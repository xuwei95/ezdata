"""PlanetScale 数据源 handler。"""

from module_data.handlers.planetscale_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.planetscale_handler.planetscale_handler import PlanetScaleHandler as Handler

version = '0.0.1'
name = 'planetscale'
title = 'PlanetScale'
description = 'PlanetScale 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
