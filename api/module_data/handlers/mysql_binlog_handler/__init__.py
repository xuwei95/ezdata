"""MySQL Binlog (CDC) 数据源 handler。"""

from module_data.handlers.mysql_binlog_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.mysql_binlog_handler.mysql_binlog_handler import MySQLBinlogHandler as Handler

version = '0.0.1'
name = 'mysql_binlog'
title = 'MySQL Binlog (CDC)'
description = 'MySQL binlog 变更捕获(mysql-replication + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
