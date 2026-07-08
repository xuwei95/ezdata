"""通用 REST/HTTP API handler。

把任意返回 JSON 的接口当数据源:用 requests 取数,支持 bearer/api_key/basic 鉴权与
page/offset/cursor 分页;返回 list[dict],接入 ETL(extract)/数据服务/AI 取数。

native 查询(statement)形态(与其它 api 族一致,AI 出 {func,params} 可直接用):
- str:命名接口名 或 直接 path(如 "/users" 或完整 URL)
- dict:{path|func|endpoint, method, params, data_selector, pagination}
"""

from __future__ import annotations

import json
from typing import Any

from ezdata.handlers.base import Capability, Column, Connector, ConnectResult
from ezdata.handlers.rest_api_handler.connection_args import connection_args, connection_args_example

# 响应里盛放记录列表的常见包裹键(无 data_selector 时自动探测)
_LIST_KEYS = ('data', 'results', 'items', 'records', 'list', 'rows', 'content')


def _get_path(obj: Any, path: str) -> Any:
    """按 'a.b.c' 取嵌套值,取不到返回 None。"""
    cur = obj
    for part in (path or '').split('.'):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _dig_list(body: Any, selector: str) -> list:
    """从响应里取出记录列表:指定 data_selector 则按路径取;否则自动探测根列表/常见包裹键。"""
    if selector:
        v = _get_path(body, selector)
        return v if isinstance(v, list) else ([] if v is None else [v])
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        for k in _LIST_KEYS:
            if isinstance(body.get(k), list):
                return body[k]
        return [body]  # 单对象
    return []


class RestApiHandler(Connector):
    name = 'rest_api'
    title = 'REST API'
    family = 'api'
    capabilities = Capability.READ | Capability.EXTRACT | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    # ---------- 元信息 ----------
    def _endpoints(self) -> dict:
        eps = self.connection_data.get('endpoints') or {}
        return eps if isinstance(eps, dict) else {}

    def test_connection(self) -> ConnectResult:
        base = self.arg('base_url')
        if not base:
            return ConnectResult(False, '缺少 base_url')
        return ConnectResult(True, f'REST API: {base}')

    def list_tables(self) -> list[str]:
        return list(self._endpoints().keys())

    def table_labels(self) -> dict[str, str]:
        return {k: (v.get('desc') or v.get('path') or '') for k, v in self._endpoints().items() if isinstance(v, dict)}

    def get_columns(self, table: str) -> list[Column]:
        """取一条样本推断字段(联网慢但准)。"""
        try:
            rows = self.query(table, None, 1)
            if rows and isinstance(rows[0], dict):
                return [Column(name=str(k), type=type(v).__name__) for k, v in rows[0].items()]
        except Exception as e:
            return [Column(name='(取样失败)', type='', comment=str(e)[:120])]
        return []

    def describe(self, table: str) -> str:
        ep = self._endpoints().get(table)
        return json.dumps(ep, ensure_ascii=False) if ep else ''

    def sample_query(self, table: str, limit: int = 100) -> dict:
        ep = self._endpoints().get(table) or {}
        return {'path': ep.get('path') or (f'/{table}' if table else '/'), 'params': ep.get('params') or {}}

    # ---------- 请求构造 ----------
    def _headers(self) -> dict:
        h = dict(self.connection_data.get('default_headers') or {})
        auth = (self.arg('auth_type') or 'none').lower()
        token = self.arg('token')
        if auth == 'bearer' and token:
            prefix = self.arg('api_key_prefix', default='Bearer ')
            h['Authorization'] = (prefix if prefix is not None else 'Bearer ') + token
        elif auth == 'api_key' and token:
            hdr = self.arg('api_key_header', default='Authorization') or 'Authorization'
            h[hdr] = (self.arg('api_key_prefix', default='') or '') + token
        return h

    def _auth_tuple(self) -> Any:
        if (self.arg('auth_type') or '').lower() == 'basic':
            return (self.arg('username') or '', self.arg('password') or '')
        return None

    def _resolve_spec(self, statement: Any) -> dict:
        """把 statement 解析为请求规格 dict(path/method/params/data_selector/pagination)。"""
        if isinstance(statement, dict):
            name = statement.get('func') or statement.get('endpoint')
            spec = dict(self._endpoints().get(name) or {}) if name else {}
            for k in ('path', 'method', 'params', 'data_selector', 'pagination'):
                if statement.get(k) is not None:
                    spec[k] = statement[k]
            if not spec.get('path'):
                spec['path'] = statement.get('path') or (f'/{name}' if name else '/')
            return spec
        s = str(statement or '')
        spec = dict(self._endpoints().get(s) or {})  # 命名接口
        if not spec:
            spec['path'] = s if s.startswith(('/', 'http')) else f'/{s}'
        return spec

    # ---------- 读路径 ----------
    def query(self, statement: Any, params: dict | None = None, limit: int | None = None) -> list[dict]:
        import requests

        spec = self._resolve_spec(statement)
        path = spec.get('path') or '/'
        method = (spec.get('method') or 'GET').upper()
        req_params = dict(spec.get('params') or {})
        req_params.update(params or {})
        selector = spec.get('data_selector') or spec.get('data') or ''
        pag = spec.get('pagination') or {}
        base = (self.arg('base_url') or '').rstrip('/')
        url = path if str(path).startswith('http') else base + '/' + str(path).lstrip('/')
        headers = self._headers()
        auth = self._auth_tuple()
        timeout = int(self.arg('timeout', default=30) or 30)

        ptype = (pag.get('type') or 'none').lower()
        max_pages = int(pag.get('max_pages') or (1 if ptype == 'none' else 50))
        size = int(pag.get('size') or 100)
        page = int(pag.get('start_page') or 1)
        cursor: Any = None
        out: list[dict] = []
        for _ in range(max_pages):
            q = dict(req_params)
            if ptype == 'page':
                q[pag.get('page_param') or 'page'] = page
                if pag.get('size_param'):
                    q[pag['size_param']] = size
            elif ptype == 'offset':
                q[pag.get('offset_param') or 'offset'] = len(out)
                if pag.get('limit_param'):
                    q[pag['limit_param']] = size
            elif ptype == 'cursor' and cursor is not None:
                q[pag.get('cursor_param') or 'cursor'] = cursor
            resp = requests.request(
                method,
                url,
                params=q if method == 'GET' else None,
                json=q if method != 'GET' else None,
                headers=headers,
                auth=auth,
                timeout=timeout,
            )
            resp.raise_for_status()
            body = resp.json()
            rows = _dig_list(body, selector)
            out.extend(r for r in rows if isinstance(r, dict))
            if limit is not None and len(out) >= int(limit):
                break
            if ptype == 'none' or not rows:
                break
            if ptype == 'cursor':
                cursor = _get_path(body, pag.get('cursor_path') or 'next_cursor')
                if not cursor:
                    break
            else:
                page += 1
                if len(rows) < size:  # 不足一页 → 结束
                    break
        return out[: int(limit)] if limit is not None else out

    # ---------- 抽取(ETL 批量装载)----------
    def extract(self, table: str, **kwargs: Any) -> Any:
        import dlt

        handler = self
        stmt = kwargs.get('statement') or table
        call_params = kwargs.get('params') or {}

        @dlt.resource(name=str(table or 'rest'), write_disposition='append')
        def _rows() -> Any:
            yield from handler.query(stmt, call_params)

        return _rows
