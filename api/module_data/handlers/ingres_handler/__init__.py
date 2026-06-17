"""Actian Ingres 数据源 handler。"""

from module_data.handlers.ingres_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.ingres_handler.ingres_handler import IngresHandler as Handler

version = '0.0.1'
name = 'ingres'
title = 'Actian Ingres'
description = 'Actian Ingres 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
