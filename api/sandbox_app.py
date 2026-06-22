#!/usr/bin/env python3
"""代码执行沙箱服务(调试层专用)。

定位:只对「worker 已抽取好的数据行」跑「转换/分析代码」,**永远拿不到任何连接凭据**。
安全边界靠容器(独立 internal 网络 + 非 root + 只读 fs + cap_drop + seccomp + 资源限制),
本服务内的 AST 校验 / 受限 builtins / 超时只是纵深防御,不作主防线。

刻意只用标准库、**不 import 任何业务代码**(config/连接器/crypto 一概不碰),
所以即便代码逃逸,这个进程里也没有数据库/密钥可偷。

端点(Authorization: Bearer <SANDBOX_BEARER_KEY>):
- GET  /health             健康检查
- POST /transform          {code, rows, timeout?} 逐行 transform(row)->row,返回 {success, transformed, output, error}

启动:python sandbox_app.py   (端口取 SANDBOX_PORT,默认 8003)
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import signal
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get('SANDBOX_PORT', '8003'))
BEARER_KEY = os.environ.get('SANDBOX_BEARER_KEY', 'change-me')
MAX_BODY = 64 * 1024 * 1024  # 64MB 请求体上限

# 允许 import 的模块(转换/分析够用;重依赖如 pandas/numpy 由镜像提供)
ALLOWED_MODULES = {
    'math', 'datetime', 'json', 'random', 're', 'decimal', 'itertools', 'collections',
    'statistics', 'string', 'uuid', 'hashlib', 'base64', 'textwrap', 'functools', 'operator',
    'pandas', 'numpy',
}
# 受限 builtins:剔除可直接逃逸/触达系统的项
_BLOCKED_BUILTINS = {
    'open', 'eval', 'exec', 'compile', 'input', 'breakpoint', 'exit', 'quit', 'help',
    'memoryview', 'globals', 'vars', 'locals', 'dir', 'getattr', 'setattr', 'delattr',
    '__import__',
}
# AST 禁止访问的 dunder 属性(挡 ().__class__.__bases__... 这类经典逃逸)
_BLOCKED_ATTRS = {
    '__class__', '__bases__', '__mro__', '__subclasses__', '__globals__', '__code__',
    '__builtins__', '__dict__', '__getattribute__', '__base__', '__subclasshook__', '__loader__',
}


def _build_safe_builtins() -> dict:
    import builtins as _b
    safe = {n: getattr(_b, n) for n in dir(_b) if not n.startswith('_') and n not in _BLOCKED_BUILTINS}

    def _guarded_import(name, *a, **k):
        top = name.split('.')[0]
        if top not in ALLOWED_MODULES:
            raise ImportError(f'sandbox 禁止导入: {name}')
        return _b.__import__(name, *a, **k)

    safe['__import__'] = _guarded_import
    return safe


def validate(code: str) -> str | None:
    """AST 校验。返回 None=通过,否则返回拒绝原因。"""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f'语法错误: {e}'
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split('.')[0] not in ALLOWED_MODULES:
                    return f"不允许导入 '{a.name}'"
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] not in ALLOWED_MODULES:
                return f"不允许从 '{node.module}' 导入"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {'eval', 'exec', 'compile', '__import__', 'open', 'getattr', 'setattr'}:
                return f"不允许调用 '{node.func.id}'"
        elif isinstance(node, ast.Attribute) and node.attr in _BLOCKED_ATTRS:
            return f"不允许访问属性 '{node.attr}'"
    return None


class _Timeout(Exception):
    pass


@contextlib.contextmanager
def _time_limit(seconds: int):
    """SIGALRM 墙钟超时(单线程 HTTPServer 主线程可用;非 Unix 跳过)。"""
    if not hasattr(signal, 'SIGALRM') or seconds <= 0:
        yield
        return

    def _handler(signum, frame):  # noqa: ANN001
        raise _Timeout(f'执行超时(> {seconds}s)')

    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def run_transform(code: str, rows: list, timeout: int) -> dict:
    """编译 transform(row),逐行执行;单行异常不中断(回报错)。stdout 作为 output 回传。"""
    reason = validate(code)
    if reason:
        return {'success': False, 'error': f'代码校验未通过: {reason}', 'transformed': None, 'output': ''}

    safe_globals = {'__builtins__': _build_safe_builtins()}
    stdout = io.StringIO()
    try:
        with _time_limit(timeout), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stdout):
            compiled = compile(code, '<sandbox-transform>', 'exec')
            exec(compiled, safe_globals)  # noqa: S102 受控:受限 builtins + 容器边界
            fn = safe_globals.get('transform')
            if not callable(fn):
                return {'success': False, 'error': '代码必须定义 transform(row) 函数',
                        'transformed': None, 'output': stdout.getvalue()}
            out = []
            for r in rows:
                try:
                    out.append(fn(dict(r)))
                except Exception as e:  # noqa: BLE001 逐行容错
                    out.append({'_transform_error': str(e), **(r if isinstance(r, dict) else {})})
        return {'success': True, 'transformed': out, 'output': stdout.getvalue(), 'error': None}
    except _Timeout as e:
        return {'success': False, 'error': str(e), 'transformed': None, 'output': stdout.getvalue()}
    except Exception as e:  # noqa: BLE001
        return {'success': False, 'error': f'{type(e).__name__}: {e}', 'transformed': None,
                'output': stdout.getvalue()}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth_ok(self) -> bool:
        h = self.headers.get('Authorization', '')
        return h.startswith('Bearer ') and h[7:] == BEARER_KEY

    def log_message(self, *a):  # noqa: ANN002 静音默认访问日志
        return

    def do_GET(self) -> None:
        if self.path == '/health':
            self._send(200, {'status': 'ok'})
        else:
            self._send(404, {'error': 'not found'})

    def do_POST(self) -> None:
        if self.path != '/transform':
            self._send(404, {'error': 'not found'})
            return
        if not self._auth_ok():
            self._send(401, {'error': 'unauthorized'})
            return
        try:
            length = int(self.headers.get('Content-Length') or 0)
            if length <= 0 or length > MAX_BODY:
                self._send(400, {'error': 'invalid body size'})
                return
            payload = json.loads(self.rfile.read(length))
        except Exception as e:  # noqa: BLE001
            self._send(400, {'error': f'bad request: {e}'})
            return
        code = payload.get('code') or ''
        rows = payload.get('rows') or []
        timeout = int(payload.get('timeout') or 60)
        if not code.strip():
            self._send(400, {'error': 'code 为空'})
            return
        if not isinstance(rows, list):
            self._send(400, {'error': 'rows 必须是数组'})
            return
        self._send(200, run_transform(code, rows, timeout))


def main() -> None:
    # 单线程 HTTPServer:请求串行,主线程可用 SIGALRM 做墙钟超时(调试场景够用)
    server = HTTPServer(('0.0.0.0', PORT), Handler)  # noqa: S104 容器内,靠 internal 网络隔离
    print(f'[sandbox] listening on :{PORT} (allowed modules: {sorted(ALLOWED_MODULES)})', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
