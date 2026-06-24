"""CCXT 加密货币交易所 数据源 handler。"""

from module_data.handlers.ccxt_handler.ccxt_handler import CCXTHandler as Handler
from module_data.handlers.ccxt_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'ccxt'
title = 'CCXT 加密货币交易所'
description = 'CCXT(统一接入数百家加密货币交易所;公开行情免 key,表=方法名如 fetch_ticker,symbol 如 BTC/USDT)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
