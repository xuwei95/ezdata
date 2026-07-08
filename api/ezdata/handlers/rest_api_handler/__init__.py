"""通用 REST/HTTP API 数据源 handler。"""

from ezdata.handlers.rest_api_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'rest_api'
title = 'REST API'
family = 'api'
capabilities = ('READ', 'EXTRACT', 'SCHEMA')
description = '通用 REST/HTTP API:配置 base_url + 鉴权,取任意 JSON 接口数据(支持分页),接 ETL/数据服务/AI 取数。'


def load_handler():
    """懒加载:仅在真正需要 handler 类时才导入其重依赖(驱动/ORM)。"""
    from ezdata.handlers.rest_api_handler.rest_api_handler import RestApiHandler

    return RestApiHandler


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
