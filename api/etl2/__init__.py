# -*- coding: utf-8 -*-
"""
ETL2 模块
整合 MindsDB integrations 和自定义 handlers
"""
from .etl_task import EtlTask, etl_task_process
from .registry import (
    HandlerRegistry,
    get_registry,
    get_reader,
    get_writer,
    # 公共注册变量
    CUSTOM_HANDLERS,
    WRITABLE_HANDLERS,
    # 便捷注册函数
    register_handler,
    register_writable,
    unregister_handler,
    list_registered_handlers,
)
from etl2.utils.mindsdb_client import IntegrationsClient

__version__ = '2.0.0'

__all__ = [
    # 核心类和函数
    'EtlTask',
    'etl_task_process',
    'HandlerRegistry',
    'get_registry',
    'get_reader',
    'get_writer',
    'IntegrationsClient',
    # 公共注册变量
    'CUSTOM_HANDLERS',
    'WRITABLE_HANDLERS',
    # 便捷注册函数
    'register_handler',
    'register_writable',
    'unregister_handler',
    'list_registered_handlers',
]
