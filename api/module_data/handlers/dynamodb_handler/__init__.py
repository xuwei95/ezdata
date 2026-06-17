"""Amazon DynamoDB 数据源 handler。"""

from module_data.handlers.dynamodb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.dynamodb_handler.dynamodb_handler import DynamoDBHandler as Handler

version = '0.0.1'
name = 'dynamodb'
title = 'Amazon DynamoDB'
description = 'DynamoDB(boto3 PartiQL/scan + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
