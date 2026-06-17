"""Apache Kafka 数据源 handler。"""

from module_data.handlers.kafka_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.kafka_handler.kafka_handler import KafkaHandler as Handler

version = '0.0.1'
name = 'kafka'
title = 'Apache Kafka'
description = 'Kafka 流式消息(kafka-python + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
