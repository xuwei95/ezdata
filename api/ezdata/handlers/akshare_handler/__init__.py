"""AKShare 数据源 handler。"""

from ezdata.handlers.akshare_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'akshare'
title = 'AKShare 财经数据'
family = 'api'
capabilities = ('READ', 'EXTRACT', 'SCHEMA')
description = 'AKShare(中国财经数据接口,免 key 只读;表=接口函数名,查询参数=函数参数)'


def load_handler():
    """懒加载:仅在真正需要 handler 类时才导入其重依赖(驱动/ORM)。"""
    from ezdata.handlers.akshare_handler.akshare_handler import AKShareHandler
    return AKShareHandler


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
