"""通用 REST/HTTP API 数据源 handler。"""

from module_data.handlers.rest_api_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.rest_api_handler.rest_api_handler import RestApiHandler as Handler

version = '0.0.1'
name = 'rest_api'
title = 'REST API'
description = '通用 REST/HTTP API:配置 base_url + 鉴权,取任意 JSON 接口数据(支持分页),接 ETL/数据服务/AI 取数。'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
