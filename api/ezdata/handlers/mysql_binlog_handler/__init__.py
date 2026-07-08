"""MySQL Binlog (CDC) 数据源 handler。"""

from ezdata.handlers.mysql_binlog_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'mysql_binlog'
title = 'MySQL Binlog (CDC)'
family = 'cdc'
capabilities = ('EXTRACT', 'SCHEMA', 'STREAM')
description = 'MySQL binlog 变更捕获(mysql-replication + dlt)'


def load_handler():
    """懒加载:仅在真正需要 handler 类时才导入其重依赖(驱动/ORM)。"""
    from ezdata.handlers.mysql_binlog_handler.mysql_binlog_handler import MySQLBinlogHandler

    return MySQLBinlogHandler


def __getattr__(attr):  # PEP 562:保留 `module.Handler` 旧用法,首次访问才触发重导入
    if attr == 'Handler':
        return load_handler()
    raise AttributeError(attr)


__all__ = [
    'Handler',
    'capabilities',
    'connection_args',
    'connection_args_example',
    'description',
    'family',
    'load_handler',
    'name',
    'title',
    'version',
]
