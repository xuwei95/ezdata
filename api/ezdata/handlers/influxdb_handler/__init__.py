"""InfluxDB 数据源 handler。"""

from ezdata.handlers.influxdb_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'influxdb'
title = 'InfluxDB'
family = 'timeseries'
capabilities = ('READ', 'WRITE', 'EXTRACT', 'SCHEMA')
description = 'InfluxDB 3.x(influxdb3-python,SQL + dlt)'


def load_handler():
    """懒加载:仅在真正需要 handler 类时才导入其重依赖(驱动/ORM)。"""
    from ezdata.handlers.influxdb_handler.influxdb_handler import InfluxDBHandler
    return InfluxDBHandler


def __getattr__(attr):  # PEP 562:保留 `module.Handler` 旧用法,首次访问才触发重导入
    if attr == 'Handler':
        return load_handler()
    raise AttributeError(attr)


__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'family',
    'capabilities',
    'load_handler',
    'name',
    'title',
    'version',
]
