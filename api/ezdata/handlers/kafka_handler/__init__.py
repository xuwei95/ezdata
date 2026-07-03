"""Apache Kafka 数据源 handler。"""

from ezdata.handlers.kafka_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'kafka'
title = 'Apache Kafka'
family = 'stream'
capabilities = ('WRITE', 'EXTRACT', 'SCHEMA', 'STREAM')
description = 'Kafka 流式消息(kafka-python + dlt)'


def load_handler():
    """懒加载:仅在真正需要 handler 类时才导入其重依赖(驱动/ORM)。"""
    from ezdata.handlers.kafka_handler.kafka_handler import KafkaHandler
    return KafkaHandler


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
