"""CCXT 加密货币交易所 数据源 handler。"""

from ezdata.handlers.ccxt_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'ccxt'
title = 'CCXT 加密货币交易所'
family = 'api'
capabilities = ('READ', 'EXTRACT', 'SCHEMA')
description = 'CCXT(统一接入数百家加密货币交易所;公开行情免 key,表=方法名如 fetch_ticker,symbol 如 BTC/USDT)'


def load_handler():
    """懒加载:仅在真正需要 handler 类时才导入其重依赖(驱动/ORM)。"""
    from ezdata.handlers.ccxt_handler.ccxt_handler import CCXTHandler

    return CCXTHandler


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
