"""Azure Blob Storage 数据源 handler。"""

from module_data.handlers.azure_blob_handler.azure_blob_handler import AzureBlobHandler as Handler
from module_data.handlers.azure_blob_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'azure_blob'
title = 'Azure Blob Storage'
description = 'Azure Blob(fsspec/adlfs + DuckDB + dlt filesystem)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
