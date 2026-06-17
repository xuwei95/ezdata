"""Redis 数据源 handler。"""

from module_data.handlers.redis_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.redis_handler.redis_handler import RedisHandler as Handler

version = '0.0.1'
name = 'redis'
title = 'Redis'
description = 'Redis(redis-py,KV/hash/list/set/zset + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
