"""轻量 HTTP 服务:标准库 http.server 暴露 JSON API + 托管单页 UI(零额外依赖)。

路由:
  GET  /                       -> static/index.html
  GET  /api/source_types       -> 数据源类型 + 能力
  GET  /api/schema?type=       -> 连接参数 schema
  GET  /api/icon?type=         -> 数据源品牌图标 SVG
  GET  /api/deps?type=         -> 依赖诊断 {requirements,missing,ready}
  POST /api/deps/install       {source_type,upgrade}  # pip 装缺失驱动
  POST /api/deps/install/stream {source_type}  # SSE:流式 pip 输出(log/done)
  GET  /api/connections        -> 连接目录
  POST /api/connections        {name,source_type,config,secrets}
  POST /api/connections/update {name,...}
  POST /api/connections/delete {name}
  POST /api/test               {name} | {source_type,config,secrets}
  GET  /api/tables?name=
  GET  /api/columns?name=&table=       -> 表字段结构 [{name,type,nullable,comment}]
  GET  /api/sample?name=&table=        -> 该表原生查询预填示例 {native}
  POST /api/query              {name,statement,limit}
  POST /api/export             {rows,filename}  # 结果行导出 xlsx(下载)
  POST /api/ask                {name,question,tables,limit}  # AI 取数:NL→查询→执行
  POST /api/ask/stream         {name,question,tables,limit}  # SSE:meta/token/statement/result(生成并执行)
  POST /api/gen/stream         {name,question,tables}        # SSE:meta/token/statement(仅生成,不执行)
  GET  /api/llm                -> LLM 就绪状态
"""

import json
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# 允许直接 `python ezdata/interface/web/server.py` 运行:作为脚本时(无包上下文),
# 把 api/ 目录(含 ezdata 包)加入 sys.path,后续 `import ezdata` 才能解析。
if __package__ in (None, ''):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # web -> interface -> ezdata -> api

from ezdata.errors import EzDataError

_STATIC = Path(__file__).parent / 'static'


def make_handler(core):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'ezdata-local/0.1'

        def log_message(self, fmt, *args):  # 静默默认访问日志
            pass

        # ---------- 响应助手 ----------
        def _json(self, obj, status=200):
            body = json.dumps(obj, ensure_ascii=False, default=str).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _err(self, e, status=400):
            if isinstance(e, EzDataError) and hasattr(e, 'to_dict'):
                self._json({'error': str(e), 'detail': e.to_dict()}, status)
            else:
                self._json({'error': f'{type(e).__name__}: {e}'}, status)

        def _sse(self, generator):
            """把 {event,data} 生成器以 SSE 流出;data 一律 JSON 编码为单行。"""
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'close')
            self.send_header('X-Accel-Buffering', 'no')
            self.end_headers()
            try:
                for ev in generator:
                    data = json.dumps(ev.get('data', ''), ensure_ascii=False, default=str)
                    frame = f'event: {ev.get("event", "message")}\ndata: {data}\n\n'
                    self.wfile.write(frame.encode('utf-8'))
                    self.wfile.flush()
            except Exception as e:
                traceback.print_exc()
                err = json.dumps({'error': f'{type(e).__name__}: {e}'}, ensure_ascii=False)
                try:
                    self.wfile.write(f'event: error\ndata: {err}\n\n'.encode())
                    self.wfile.flush()
                except Exception:
                    pass

        def _file(self, path: Path, ctype: str):
            if not path.exists():
                self._json({'error': 'not found'}, 404)
                return
            body = path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')  # 开发期:每次刷新都取最新 UI,避免浏览器缓存旧页
            self.end_headers()
            self.wfile.write(body)

        def _download(self, data: bytes, ctype: str, filename: str):
            """以附件形式下发二进制(导出用)。"""
            from urllib.parse import quote

            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Disposition', f"attachment; filename*=UTF-8''{quote(filename)}")
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self) -> dict:
            length = int(self.headers.get('Content-Length', 0) or 0)
            if not length:
                return {}
            raw = self.rfile.read(length)
            for enc in ('utf-8', 'gbk', 'latin-1'):  # 浏览器发 utf-8;容忍 Windows 终端 gbk
                try:
                    return json.loads(raw.decode(enc) or '{}')
                except UnicodeDecodeError:
                    continue
            return json.loads(raw.decode('utf-8', 'replace') or '{}')

        # ---------- GET ----------
        def do_GET(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path in ('/', '/index.html'):
                    return self._file(_STATIC / 'index.html', 'text/html; charset=utf-8')
                if u.path == '/api/source_types':
                    return self._json(core.list_source_types())
                if u.path == '/api/schema':
                    return self._json(core.connection_schema(q['type']))
                if u.path == '/api/icon':
                    from ezdata import services

                    return self._json({'svg': services.source_type_icon(q['type'])})
                if u.path == '/api/deps':
                    return self._json(core.dependency_status(q['type']))
                if u.path == '/api/connections':
                    return self._json(core.list_connections())
                if u.path == '/api/tables':
                    return self._json(core.list_tables(q['name']))
                if u.path == '/api/columns':
                    return self._json(core.get_columns(q['name'], q['table']))
                if u.path == '/api/sample':
                    return self._json(core.sample_query(q['name'], q['table']))
                if u.path == '/api/llm':
                    return self._json(
                        {
                            'ready': core.llm.ready,
                            'model': core.llm.cfg.get('model'),
                            'base_url': core.llm.cfg.get('base_url'),
                        }
                    )
                self._json({'error': 'not found'}, 404)
            except Exception as e:
                traceback.print_exc()
                self._err(e)

        # ---------- POST ----------
        def do_POST(self):
            u = urlparse(self.path)
            try:
                b = self._body()
                if u.path == '/api/connections':
                    return self._json(
                        core.add_connection(b['name'], b['source_type'], b.get('config'), b.get('secrets'))
                    )
                if u.path == '/api/connections/update':
                    name = b.pop('name')
                    return self._json(core.update_connection(name, **b))
                if u.path == '/api/connections/delete':
                    return self._json({'removed': core.remove_connection(b['name'])})
                if u.path == '/api/test':
                    # name 存在时以原连接为底合并(编辑态:测新 config + 原密钥);纯新建则只用传入值
                    return self._json(
                        core.test_connection(
                            b.get('name'),
                            source_type=b.get('source_type'),
                            config=b.get('config'),
                            secrets=b.get('secrets'),
                        )
                    )
                if u.path == '/api/query':
                    return self._json({'rows': core.query(b['name'], b['statement'], b.get('limit', 200))})
                if u.path == '/api/export':
                    data = core.export_excel(b.get('rows') or [])
                    fn = b.get('filename') or 'export.xlsx'
                    return self._download(data, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', fn)
                if u.path == '/api/ask':
                    return self._json(core.ask(b['name'], b['question'], b.get('tables'), b.get('limit', 200)))
                if u.path == '/api/ask/stream':
                    return self._sse(core.ask_stream(b['name'], b['question'], b.get('tables'), b.get('limit', 200)))
                if u.path == '/api/gen/stream':
                    return self._sse(core.gen_query_stream(b['name'], b['question'], b.get('tables')))
                if u.path == '/api/deps/install':
                    return self._json(core.install_dependencies(b['source_type'], upgrade=b.get('upgrade', False)))
                if u.path == '/api/deps/install/stream':
                    return self._sse(
                        core.install_dependencies_stream(b['source_type'], upgrade=b.get('upgrade', False))
                    )
                self._json({'error': 'not found'}, 404)
            except Exception as e:
                traceback.print_exc()
                self._err(e)

    return Handler


def serve(core, host='127.0.0.1', port=8077):
    httpd = ThreadingHTTPServer((host, port), make_handler(core))
    print(f'ezdata 本地 UI 已启动: http://{host}:{port}')
    print(f'LLM: {"就绪" if core.llm.ready else "未配置"} model={core.llm.cfg.get("model")}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止')
        httpd.shutdown()


if __name__ == '__main__':
    # 直接 `python ezdata/interface/web/server.py [--host --port]` 也能起(等价 python -m ezdata.interface.web)
    from ezdata.interface.web.__main__ import main

    main()
