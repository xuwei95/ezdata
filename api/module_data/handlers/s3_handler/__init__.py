"""S3 / 对象存储 数据源 handler。"""

from module_data.handlers.s3_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.s3_handler.s3_handler import S3Handler as Handler

version = '0.0.1'
name = 's3'
title = 'S3 / 对象存储'
description = 'S3/MinIO/OSS 对象存储(boto3 + dlt filesystem)'

__all__ = [
           'Handler',
           'connection_args',
           'connection_args_example',
           'description',
           'name',
           'title',
           'version',
]
