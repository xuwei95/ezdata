#!/usr/bin/env python3
"""无状态全注入代码执行沙箱(FastAPI)。

定位:平台所有「运行代码」的**调试态**在此执行(Python / Shell / ETL / 动态);正式态仍由
worker 直跑,不经此服务。沙箱进程 env 为空、不持任何持久凭据,执行所需的一切——代码/命令、
数据源连接(明文)、日志库连接——都随每次 HTTP 请求注入,用完即弃,请求之间互相隔离。
即便进程被攻破,翻不到任何持久凭据;爆炸半径仅限当前请求传入的那批连接信息。

安全边界:容器(独立 fs / 非 root / cap_drop / 资源上限)是主防线;每个执行请求 fork 子进程
(进程隔离 + 可靠墙钟超时 + kill);受限 builtins/import 白名单(复用 runners/sandbox.py)是
纵深防御。开关由调用方的 SANDBOX_ENABLED 控制,关闭时调用方回落本地真实跑,不经此服务。

端点(Authorization: Bearer <SANDBOX_BEARER_KEY>):
- GET  /health
- POST /python/execute   {code, params, logger_config?, timeout}   复用 run_user_code,跑 run(params, logger)
- POST /shell/execute    {command, logger_config?, timeout}        复用 stream_subprocess
- POST /data/execute     {params, datasources, logger_config?, timeout}  ETL 抽取->转换->装载(数据源注入)
- POST /transform        {code, rows, timeout}                     逐行 transform(row)(兼容现有 ETL 预览)

日志 logger_config = {type:'db'|'es'|'file', task_uuid, ...连接参数}:
- db:{db_url}        沙箱按注入连接串直写 task_log 表
- es:{hosts,index,user,password}  沙箱直写 ES 索引
- file/缺省:沙箱只收集日志行随响应回传(由调用方写盘)
所有类型都会把日志行收进响应 logs 字段,便于前端即时展示。

启动:uvicorn sandbox_app:app --host 0.0.0.0 --port 8003
"""

from __future__ import annotations

import contextlib
import io
import json
import multiprocessing as mp
import os
import platform
import queue
import sys
import traceback
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

PORT = int(os.environ.get('SANDBOX_PORT', '8003'))
BEARER_KEY = os.environ.get('SANDBOX_BEARER_KEY', 'change-me')
# 子进程内存上限(字节);0=不限。仅 Unix 生效。
MEM_LIMIT = int(os.environ.get('SANDBOX_MEM_LIMIT_BYTES', str(512 * 1024 * 1024)))

IS_WINDOWS = platform.system() == 'Windows'
_HAS_FORK = hasattr(os, 'fork')

# 预加载重模块到主进程:fork 子进程继承已加载模块,避免子进程「首次 import」时
# 撞上 fork-from-thread 继承的 import 锁而死锁(纯计算不 import 重模块故无此问题)。
for _m in ('pandas', 'numpy'):
    try:
        __import__(_m)
    except Exception:  # noqa: BLE001 未装则跳过
        pass


# ---------------------------------------------------------------------------
# 沙箱内日志:总是收集(随响应回传),db/es 额外按注入连接参数直写任务日志库
# ---------------------------------------------------------------------------
class _InjectedDbLogWriter:
    """用注入的同步连接串直写 task_log 表(沙箱无 env,连接信息随请求传入)。"""

    def __init__(self, db_url: str) -> None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        self._engine = create_engine(db_url, pool_pre_ping=True)
        self._session = sessionmaker(bind=self._engine)
        self._buffer: list[dict[str, Any]] = []

    def write(self, task_uuid: str, level: str, message: str, log_time: datetime) -> None:
        self._buffer.append({'task_uuid': task_uuid, 'level': level, 'content': message, 'create_time': log_time})
        if len(self._buffer) >= 50:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        rows, self._buffer = self._buffer, []
        from module_task_schedule.entity.do.task_do import TaskLog

        session = self._session()
        try:
            session.bulk_insert_mappings(TaskLog, rows)
            session.commit()
        except Exception:  # noqa: BLE001 日志写库失败不影响执行
            session.rollback()
        finally:
            session.close()

    def close(self) -> None:
        self.flush()


def _make_log_writer(cfg: dict) -> Any | None:
    """按 logger_config 建直写 writer;file/缺省返回 None(仅收集回传)。"""
    typ = (cfg or {}).get('type')
    try:
        if typ == 'es' and cfg.get('hosts'):
            from module_task_schedule.task_logger import EsTaskLogWriter

            return EsTaskLogWriter(
                hosts=cfg['hosts'], index=cfg.get('index', 'task_logs'),
                user=cfg.get('user', ''), password=cfg.get('password', ''),
            )
        if typ == 'db' and cfg.get('db_url'):
            return _InjectedDbLogWriter(cfg['db_url'])
    except Exception:  # noqa: BLE001 直写后端初始化失败 → 降级为仅收集回传
        return None
    return None


class _SandboxLogger:
    """签名兼容 TaskLogger 的轻量 logger:收集日志行 + 可选直写后端。"""

    def __init__(self, writer: Any | None, task_uuid: str) -> None:
        self._writer = writer
        self._task_uuid = task_uuid
        self.lines: list[dict[str, str]] = []

    def _log(self, level: str, message: Any, exc: bool = False) -> None:
        text = str(message)
        if exc:
            text = f'{text}\n{traceback.format_exc()}'
        self.lines.append({'level': level, 'message': text})
        if self._writer is not None:
            try:
                self._writer.write(self._task_uuid, level, text, datetime.now())
            except Exception:  # noqa: BLE001
                pass

    def debug(self, message: Any) -> None:
        self._log('DEBUG', message)

    def info(self, message: Any) -> None:
        self._log('INFO', message)

    def warning(self, message: Any) -> None:
        self._log('WARNING', message)

    def error(self, message: Any) -> None:
        self._log('ERROR', message)

    def exception(self, message: Any) -> None:
        self._log('ERROR', message, exc=True)

    def flush(self) -> None:
        if self._writer is not None:
            with contextlib.suppress(Exception):
                self._writer.flush()

    def close(self) -> None:
        if self._writer is not None:
            with contextlib.suppress(Exception):
                self._writer.close()


def _jsonable(v: Any) -> Any:
    """规整执行结果:不可 JSON 序列化的对象转字符串,避免响应序列化失败。"""
    try:
        json.dumps(v)
        return v
    except (TypeError, ValueError):
        return str(v)


# ---------------------------------------------------------------------------
# 执行分发(在子进程内运行)
# ---------------------------------------------------------------------------
def _build_runner(payload: dict, logger: Any) -> Any:
    """按任务描述构造 runner —— 与 executor/dag_orchestrator 创建 runner 的逻辑一致。

    沙箱即「远程 executor」:复用平台所有 runner;数据源连接由 resolved_datasources 注入
    (ETL),其余 runner 忽略该键。
    """
    from module_task_schedule.runners.base import get_runner

    params = payload.get('params') or {}
    ctx = {'sandbox': True, 'resolved_datasources': payload.get('datasources') or {}}
    if int(payload.get('runner_type') or 1) == 2:
        from module_task_schedule.runners.dynamic_runner import DynamicRunner

        ctx['runner_code'] = payload.get('runner_code') or ''
        return DynamicRunner(params, logger, context=ctx)
    runner_cls = get_runner(payload.get('template_code') or '')
    if runner_cls is None:
        raise ValueError(f'未注册的任务类型: {payload.get("template_code")}')
    return runner_cls(params, logger, context=ctx)


def _dispatch(kind: str, payload: dict) -> dict:
    """执行任务,返回 {success, result, output, logs, error}。在子进程内调用。"""
    if kind == 'transform':
        return _run_transform(payload.get('code') or '', payload.get('rows') or [])
    if kind in ('pyrun', 'pydata'):
        return _run_pycode(kind, payload)

    logger = _SandboxLogger(_make_log_writer(payload.get('logger_config') or {}),
                            (payload.get('logger_config') or {}).get('task_uuid') or 'sandbox')
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stdout):
            result = _build_runner(payload, logger).run()
        out = stdout.getvalue()
        if out.strip():  # 用户 print 输出也进日志流(写库),便于调试弹窗查看
            logger.info(f'[stdout] {out.rstrip()}')
        logger.info(f'[执行成功] 返回值: {_jsonable(result)}')
        logger.close()
        return {'success': True, 'result': _jsonable(result), 'output': out,
                'logs': logger.lines, 'error': None}
    except Exception as e:  # noqa: BLE001 业务执行错误回报给调用方
        out = stdout.getvalue()
        if out.strip():
            logger.info(f'[stdout] {out.rstrip()}')
        logger.error(f'[执行失败] {type(e).__name__}: {e}')
        logger.close()
        return {'success': False, 'error': f'{type(e).__name__}: {e}', 'output': out,
                'logs': logger.lines, 'result': None}


# 受限 builtins / 校验:仅用于 /transform(逐行 transform(row),不走 run_user_code)
_ALLOWED_MODULES = {
    'math', 'datetime', 'json', 'random', 're', 'decimal', 'itertools', 'collections',
    'statistics', 'string', 'uuid', 'hashlib', 'base64', 'textwrap', 'functools', 'operator',
    'pandas', 'numpy',
}
_BLOCKED_BUILTINS = {
    'open', 'eval', 'exec', 'compile', 'input', 'breakpoint', 'exit', 'quit', 'help',
    'memoryview', 'globals', 'vars', 'locals', 'dir', 'getattr', 'setattr', 'delattr', '__import__',
}


def _safe_builtins() -> dict:
    import builtins as _b

    safe = {n: getattr(_b, n) for n in dir(_b) if not n.startswith('_') and n not in _BLOCKED_BUILTINS}

    def _guarded_import(name, *a, **k):  # noqa: ANN001,ANN002,ANN003
        if name.split('.')[0] not in _ALLOWED_MODULES:
            raise ImportError(f'sandbox 禁止导入: {name}')
        return _b.__import__(name, *a, **k)

    safe['__import__'] = _guarded_import
    return safe


def _run_pycode(kind: str, payload: dict) -> dict:
    """受限 exec 裸脚本(agent 代码工具),返回 {success, stdout, result, error}。

    pyrun:纯计算/数据处理(math/json/pandas/numpy 等,禁 os/网络/文件)。
    pydata:额外注入 handler(用明文连接建),code 中用 handler 取数,如
            result = handler.query("SELECT ...");取 variable_to_return 变量返回。
    """
    code = payload.get('code') or ''
    var = payload.get('variable_to_return')
    if not code.strip():
        return {'success': False, 'error': 'code 为空', 'stdout': '', 'result': None}
    g: dict[str, Any] = {'__builtins__': _safe_builtins()}
    if kind == 'pydata':
        ds = payload.get('datasource') or {}
        try:
            from module_data.handlers import create_handler

            g['handler'] = create_handler(ds.get('source_type'), ds.get('config') or {}, ds.get('secrets') or {})
            g['datasource'] = g['handler']  # 别名
        except Exception as e:  # noqa: BLE001
            return {'success': False, 'error': f'数据源连接失败: {type(e).__name__}: {e}',
                    'stdout': '', 'result': None}
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stdout):
            exec(compile(code, '<sandbox-pycode>', 'exec'), g)  # noqa: S102 受限 builtins + 容器边界
        result = _jsonable(g.get(var)) if var else None
        return {'success': True, 'result': result, 'stdout': stdout.getvalue(), 'error': None}
    except Exception as e:  # noqa: BLE001
        return {'success': False, 'error': f'{type(e).__name__}: {e}', 'stdout': stdout.getvalue(), 'result': None}


def _run_transform(code: str, rows: list) -> dict:
    """逐行执行 transform(row)->row(ETL 预览)。单行异常不中断。"""
    if not code.strip():
        return {'success': False, 'error': 'code 为空', 'transformed': None, 'output': ''}
    stdout = io.StringIO()
    g = {'__builtins__': _safe_builtins()}
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stdout):
            exec(compile(code, '<sandbox-transform>', 'exec'), g)  # noqa: S102 受限 builtins + 容器边界
            fn = g.get('transform')
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
    except Exception as e:  # noqa: BLE001
        return {'success': False, 'error': f'{type(e).__name__}: {e}', 'transformed': None,
                'output': stdout.getvalue()}


# ---------------------------------------------------------------------------
# 子进程执行 + 墙钟超时
# ---------------------------------------------------------------------------
def _subprocess_entry(kind: str, payload: dict, q: Any) -> None:
    """子进程入口:设资源上限 → 执行 → 结果放回队列。"""
    if not IS_WINDOWS:
        try:
            import resource

            if MEM_LIMIT > 0:
                resource.setrlimit(resource.RLIMIT_AS, (MEM_LIMIT, MEM_LIMIT))
        except Exception:  # noqa: BLE001
            pass
    try:
        result = _dispatch(kind, payload)
    except Exception as e:  # noqa: BLE001
        result = {'success': False, 'error': f'{type(e).__name__}: {e}\n{traceback.format_exc()}',
                  'logs': [], 'output': ''}
    try:
        q.put(result)
    except Exception:  # noqa: BLE001 结果不可 pickle 等极端情况
        q.put({'success': False, 'error': '执行结果无法回传(序列化失败)', 'logs': [], 'output': ''})


def _execute_with_timeout(kind: str, payload: dict, timeout: int) -> dict:
    """fork 子进程执行,wait(timeout) 超时则 kill。无 fork(Windows 本地)时同进程兜底。"""
    timeout = max(1, int(timeout or 60))
    if not _HAS_FORK:
        return _dispatch(kind, payload)  # 本地兜底:无强制超时

    ctx = mp.get_context('fork')
    q = ctx.Queue()
    p = ctx.Process(target=_subprocess_entry, args=(kind, payload, q), daemon=True)
    p.start()
    try:
        # 子进程自身(如 shell/stream_subprocess)也按 timeout 收尾,外层多给 2s 缓冲再硬杀
        result = q.get(timeout=timeout + 2)
    except queue.Empty:
        result = {'success': False, 'error': f'执行超时(> {timeout}s)', 'logs': [], 'output': ''}
    finally:
        if p.is_alive():
            p.terminate()
            p.join(2)
            if p.is_alive():
                p.kill()
                p.join()
    return result


# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------
app = FastAPI(title='ezdata sandbox', docs_url=None, redoc_url=None, openapi_url=None)


def _auth(authorization: str = Header(default='')) -> None:
    if not (authorization.startswith('Bearer ') and authorization[7:] == BEARER_KEY):
        raise HTTPException(status_code=401, detail='unauthorized')


class TaskReq(BaseModel):
    template_code: str = ''           # 内置:PythonTask / ShellTask / DataIntegrationTask
    runner_type: int = 1              # 1 内置 runner / 2 动态代码
    runner_code: str | None = None    # runner_type=2 时的模板代码
    params: dict = {}
    datasources: dict = {}            # {code: {source_type, config, secrets(明文 dict)}} 仅 ETL 用
    logger_config: dict | None = None
    timeout: int = 300


class TransformReq(BaseModel):
    code: str
    rows: list = []
    timeout: int = 60


class PyRunReq(BaseModel):
    code: str
    variable_to_return: str | None = None
    timeout: int = 60


class PyDataReq(BaseModel):
    code: str
    datasource: dict = {}                 # {source_type, config, secrets(明文 dict)}
    variable_to_return: str | None = 'result'
    timeout: int = 60


@app.get('/health')
async def health() -> dict:
    return {'status': 'ok', 'fork': _HAS_FORK}


@app.post('/task/execute')
async def task_execute(req: TaskReq, authorization: str = Header(default='')) -> dict:
    """通用任务执行:沙箱即远程 executor,按 template_code/runner_type 复用平台 runner。"""
    _auth(authorization)
    payload = {'template_code': req.template_code, 'runner_type': req.runner_type,
               'runner_code': req.runner_code, 'params': req.params, 'datasources': req.datasources,
               'logger_config': req.logger_config, 'timeout': req.timeout}
    return await run_in_threadpool(_execute_with_timeout, 'task', payload, req.timeout)


@app.post('/transform')
async def transform(req: TransformReq, authorization: str = Header(default='')) -> dict:
    _auth(authorization)
    payload = {'code': req.code, 'rows': req.rows}
    return await run_in_threadpool(_execute_with_timeout, 'transform', payload, req.timeout)


@app.post('/python/run')
async def python_run(req: PyRunReq, authorization: str = Header(default='')) -> dict:
    """运行普通 python 代码(纯计算/数据处理),返回 stdout 与指定变量值。"""
    _auth(authorization)
    payload = {'code': req.code, 'variable_to_return': req.variable_to_return}
    return await run_in_threadpool(_execute_with_timeout, 'pyrun', payload, req.timeout)


@app.post('/python/data')
async def python_data(req: PyDataReq, authorization: str = Header(default='')) -> dict:
    """运行数据源取数代码:注入 handler(用明文连接建),code 中用其取数。"""
    _auth(authorization)
    payload = {'code': req.code, 'datasource': req.datasource, 'variable_to_return': req.variable_to_return}
    return await run_in_threadpool(_execute_with_timeout, 'pydata', payload, req.timeout)


def main() -> None:
    import uvicorn

    print(f'[sandbox] FastAPI listening on :{PORT} (fork={_HAS_FORK})', flush=True)
    uvicorn.run(app, host='0.0.0.0', port=PORT, log_level='warning')  # noqa: S104 容器内,靠网络隔离


if __name__ == '__main__':
    main()
