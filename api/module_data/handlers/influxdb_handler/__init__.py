"""InfluxDB 数据源 handler。"""

from module_data.handlers.influxdb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.influxdb_handler.influxdb_handler import InfluxDBHandler as Handler

version = '0.0.1'
name = 'influxdb'
title = 'InfluxDB'
description = 'InfluxDB 3.x(influxdb3-python,SQL + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
