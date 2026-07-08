"""
BigQuery handler:SqlConnector + sqlalchemy-bigquery。

鉴权特殊:不走 URL 用户名密码,而是 service_account_json 通过 create_engine 的
credentials_info 注入(故覆写 _build_url 与 _engine_kwargs)。
"""

import json
from typing import Any

from ezdata.handlers.bigquery_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class BigQueryHandler(SqlConnector):
    name = 'bigquery'
    title = 'Google BigQuery'
    driver = 'bigquery'
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        project = self.arg('project_id')
        dataset = self.arg('dataset', default='')
        return f'bigquery://{project}/{dataset}' if dataset else f'bigquery://{project}'

    def _engine_kwargs(self) -> dict:
        kw: dict[str, Any] = {}
        sa = self.arg('service_account_json') or self.arg('service_account_keys')
        if isinstance(sa, str) and sa.strip().startswith('{'):
            sa = json.loads(sa)
        if isinstance(sa, dict):
            kw['credentials_info'] = sa
        elif isinstance(sa, str) and sa:
            kw['credentials_path'] = sa  # 给的是 key 文件路径
        return kw
