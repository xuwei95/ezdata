"""Google Cloud Storage 数据源 handler。"""

from module_data.handlers.gcs_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.gcs_handler.gcs_handler import GCSHandler as Handler

version = '0.0.1'
name = 'gcs'
title = 'Google Cloud Storage'
description = 'GCS(fsspec/gcsfs + DuckDB + dlt filesystem)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
