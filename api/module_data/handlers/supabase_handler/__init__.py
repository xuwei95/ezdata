"""Supabase 数据源 handler。"""

from module_data.handlers.supabase_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.supabase_handler.supabase_handler import SupabaseHandler as Handler

version = '0.0.1'
name = 'supabase'
title = 'Supabase'
description = 'Supabase 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
