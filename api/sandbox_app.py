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
    except Exception:
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
        except Exception:
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
                hosts=cfg['hosts'],
                index=cfg.get('index', 'task_logs'),
                user=cfg.get('user', ''),
                password=cfg.get('password', ''),
            )
        if typ == 'db' and cfg.get('db_url'):
            return _InjectedDbLogWriter(cfg['db_url'])
    except Exception:
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
            except Exception:
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
    """规整执行结果:不可 JSON 序列化的对象转字符串,避免响应序列化失败。

    关键:含 date/Decimal/numpy 等的 list[dict] 不能整体 str() 化(否则 list 变成一个大字符串,
    取数预览/agent 会判定"未产出 list[dict]")。用 json_safe **递归保结构、只转无法序列化的叶子**。
    """
    try:
        json.dumps(v)
        return v
    except (TypeError, ValueError):
        try:
            from ezdata.utils.etl_util import json_safe

            return json_safe(v)
        except Exception:
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
    if kind in ('pyrun', 'pydata', 'pyextract'):
        return _run_pycode(kind, payload)

    logger = _SandboxLogger(
        _make_log_writer(payload.get('logger_config') or {}),
        (payload.get('logger_config') or {}).get('task_uuid') or 'sandbox',
    )
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stdout):
            result = _build_runner(payload, logger).run()
        out = stdout.getvalue()
        if out.strip():  # 用户 print 输出也进日志流(写库),便于调试弹窗查看
            logger.info(f'[stdout] {out.rstrip()}')
        logger.info(f'[执行成功] 返回值: {_jsonable(result)}')
        logger.close()
        return {'success': True, 'result': _jsonable(result), 'output': out, 'logs': logger.lines, 'error': None}
    except Exception as e:
        out = stdout.getvalue()
        if out.strip():
            logger.info(f'[stdout] {out.rstrip()}')
        logger.error(f'[执行失败] {type(e).__name__}: {e}')
        logger.close()
        return {
            'success': False,
            'error': f'{type(e).__name__}: {e}',
            'output': out,
            'logs': logger.lines,
            'result': None,
        }


# 受限 builtins:门住所有沙箱代码(/python/run、/python/data、/transform)的 import。
# 仅校验顶层模块名;被放行模块自身的内部 import(如 akshare→requests/socket)走真实 import 不受此限。
# 网络类(akshare/requests)的出网由 egress 代理(SANDBOX_EGRESS_ALLOW 域名白名单)兜底,而非此处。
# 注:run_datasource_query 走 akshare 数据源时,handler.query 在普通作用域 import,无需在此放行。
_ALLOWED_MODULES = {
    'math',
    'datetime',
    'time',
    'json',
    'random',
    're',
    'decimal',
    'itertools',
    'collections',
    'statistics',
    'string',
    'uuid',
    'hashlib',
    'base64',
    'textwrap',
    'functools',
    'operator',
    'pandas',
    'numpy',
    'pyecharts',
    'akshare',
    'requests',
    'ccxt',  # 联网取数:出网受 egress 代理域名白名单约束
    'bs4',
    'lxml',
    'urllib',  # 代码取数/爬虫:HTML 解析 + URL 处理(网络仍受 egress 约束)
}
_BLOCKED_BUILTINS = {
    'open',
    'eval',
    'exec',
    'compile',
    'input',
    'breakpoint',
    'exit',
    'quit',
    'help',
    'memoryview',
    'globals',
    'vars',
    'locals',
    'dir',
    'getattr',
    'setattr',
    'delattr',
    '__import__',
}


def _safe_builtins() -> dict:
    import builtins as _b

    safe = {n: getattr(_b, n) for n in dir(_b) if not n.startswith('_') and n not in _BLOCKED_BUILTINS}

    def _guarded_import(name, *a, **k):
        if name.split('.')[0] not in _ALLOWED_MODULES:
            raise ImportError(f'sandbox 禁止导入: {name}')
        return _b.__import__(name, *a, **k)

    safe['__import__'] = _guarded_import
    return safe


def _is_dataframe(v: Any) -> bool:
    try:
        import pandas as pd

        return isinstance(v, pd.DataFrame)
    except Exception:
        return False


def _df_to_list(df: Any) -> list:
    """DataFrame → records list:datetime 列转字符串,数值列 NaN→0,其余 NaN→''。"""
    import pandas as pd

    for col in df.select_dtypes(include=['datetime', 'datetimetz']).columns:
        df[col] = df[col].astype(str)
    for col in df.columns:
        df[col] = df[col].fillna(0) if pd.api.types.is_numeric_dtype(df[col]) else df[col].fillna('')
    return df.to_dict(orient='records')


def _normalize_result(v: Any) -> Any:
    """规整执行结果,对齐 {type, value} 约定。

    - 裸 DataFrame          → {'type':'dataframe', 'value': records}
    - {'type','value'} dict → value 若是 DataFrame 转 records,否则 _jsonable
    - 其他(str/list/dict/数字) → _jsonable 原样
    """
    if _is_dataframe(v):
        return {'type': 'dataframe', 'value': _df_to_list(v)}
    if isinstance(v, dict) and 'type' in v and 'value' in v:
        val = v['value']
        return {'type': v['type'], 'value': _df_to_list(val) if _is_dataframe(val) else _jsonable(val)}
    return _jsonable(v)


class _StopPreview(Exception):
    """预览时 emit 收集够样本后抛出,提前中断用户代码抓取(避免全量分页拖慢预览)。"""


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
    # 注入 logger(签名兼容 worker 的 TaskLogger)+ log 别名,使沙箱内代码可用 logger.info/log(...)——
    # 与 worker 的 code-extract 执行环境(注入 logger/log)对齐,避免"预览/agent 走沙箱时 NameError"。
    # 有 logger_config 时直写后端日志(同任务日志流);无则仅收集到 lines 并随响应返回。
    cfg = payload.get('logger_config') or {}
    logger = _SandboxLogger(_make_log_writer(cfg), cfg.get('task_uuid') or 'sandbox')
    # emit(rows):与 worker code-extract 的流式分批一致的调用签名。预览不做真实装载,只收集前几批做样本展示。
    # 关键:攒够 _EMIT_PREVIEW_CAP 行就**抛 _StopPreview 中断用户代码**——否则像全市场分页那样会把 70 页全抓完
    # 才返回(预览卡很久)。预览只需头部样本,拿到就停、立即返回。worker 里的 emit 无此上限,仍抓全量。
    _emit_buf: list[Any] = []
    _EMIT_PREVIEW_CAP = 200

    def _emit(rows: Any) -> int:
        try:
            if hasattr(rows, 'to_dict') and not isinstance(rows, dict):
                rows = rows.to_dict('records')
        except Exception:
            pass
        if isinstance(rows, dict):
            rows = [rows]
        n = 0
        if isinstance(rows, (list, tuple)):
            for r in rows:
                _emit_buf.append(r)
                n += 1
                if len(_emit_buf) >= _EMIT_PREVIEW_CAP:
                    raise _StopPreview  # 样本够了,中断抓取,立即返回预览
        return n

    g: dict[str, Any] = {'__builtins__': _safe_builtins(), 'logger': logger, 'log': logger.info, 'emit': _emit}
    if kind == 'pydata':
        ds = payload.get('datasource') or {}
        try:
            from ezdata.handlers import create_handler

            g['handler'] = create_handler(
                ds.get('source_type'), ds.get('config') or {}, ds.get('secrets') or {}, cache=False
            )  # 沙箱 fork 子进程用完即死,不缓
            g['datasource'] = g['handler']  # 别名
        except Exception as e:
            return {'success': False, 'error': f'数据源连接失败: {type(e).__name__}: {e}', 'stdout': '', 'result': None}
    if kind == 'pyextract':
        # 代码取数:注入 get_handler(code) 从预解密注入的 datasources map 建 handler(仅限注入的源)
        dsmap = payload.get('datasources') or {}
        try:
            from ezdata.handlers import create_handler

            def _get_handler(code: str) -> Any:
                ds = dsmap.get(code)
                if not ds:
                    raise ValueError(f'数据源未授权或未注入: {code}')
                return create_handler(
                    ds.get('source_type'), ds.get('config') or {}, ds.get('secrets') or {}, cache=False
                )

            g['get_handler'] = _get_handler
            if len(dsmap) == 1:
                g['handler'] = _get_handler(next(iter(dsmap)))  # 仅 1 个源时给 handler 别名
        except Exception as e:
            return {'success': False, 'error': f'数据源连接失败: {type(e).__name__}: {e}', 'stdout': '', 'result': None}
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stdout):
            try:
                exec(compile(code, '<sandbox-pycode>', 'exec'), g)
            except _StopPreview:  # emit 攒够样本主动中断:正常结束,用已收集的样本
                pass
        out_val = g.get(var) if var else None
        if out_val is None and _emit_buf:  # 用了 emit 而未设 result:预览取 emit 收集的样本
            out_val = _emit_buf
        # result 是生成器(原生 yield 流式):预览时迭代出前 _EMIT_PREVIEW_CAP 行做样本,避免被 str 化
        if (
            out_val is not None
            and not isinstance(out_val, (list, tuple, dict, str, bytes))
            and not _is_dataframe(out_val)
            and hasattr(out_val, '__iter__')
        ):
            sample: list[Any] = []
            for it in out_val:
                if isinstance(it, dict):
                    sample.append(it)
                elif isinstance(it, (list, tuple)):
                    sample.extend(it)
                if len(sample) >= _EMIT_PREVIEW_CAP:
                    break
            out_val = sample
        result = _normalize_result(out_val) if var else None
        logger.close()
        return {'success': True, 'result': result, 'stdout': stdout.getvalue(), 'logs': logger.lines, 'error': None}
    except Exception as e:
        logger.close()
        return {
            'success': False,
            'error': f'{type(e).__name__}: {e}',
            'stdout': stdout.getvalue(),
            'logs': logger.lines,
            'result': None,
        }


def _run_transform(code: str, rows: list) -> dict:
    """逐行执行 transform(row)->row(ETL 预览)。单行异常不中断。"""
    if not code.strip():
        return {'success': False, 'error': 'code 为空', 'transformed': None, 'output': ''}
    stdout = io.StringIO()
    g = {'__builtins__': _safe_builtins()}
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stdout):
            exec(compile(code, '<sandbox-transform>', 'exec'), g)
            fn = g.get('transform')
            if not callable(fn):
                return {
                    'success': False,
                    'error': '代码必须定义 transform(row) 函数',
                    'transformed': None,
                    'output': stdout.getvalue(),
                }
            out = []
            for r in rows:
                try:
                    out.append(fn(dict(r)))
                except Exception as e:
                    out.append({'_transform_error': str(e), **(r if isinstance(r, dict) else {})})
        return {'success': True, 'transformed': out, 'output': stdout.getvalue(), 'error': None}
    except Exception as e:
        return {'success': False, 'error': f'{type(e).__name__}: {e}', 'transformed': None, 'output': stdout.getvalue()}


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
        except Exception:
            pass
    try:
        result = _dispatch(kind, payload)
    except Exception as e:
        result = {
            'success': False,
            'error': f'{type(e).__name__}: {e}\n{traceback.format_exc()}',
            'logs': [],
            'output': '',
        }
    try:
        q.put(result)
    except Exception:
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
    template_code: str = ''  # 内置:PythonTask / ShellTask / DataIntegrationTask
    runner_type: int = 1  # 1 内置 runner / 2 动态代码
    runner_code: str | None = None  # runner_type=2 时的模板代码
    params: dict = {}
    datasources: dict = {}  # {code: {source_type, config, secrets(明文 dict)}} 仅 ETL 用
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
    datasource: dict = {}  # {source_type, config, secrets(明文 dict)}
    variable_to_return: str | None = 'result'
    timeout: int = 60


class PyExtractReq(BaseModel):
    code: str
    datasources: dict = {}  # {code: {source_type, config, secrets(明文 dict)}};get_handler 据此建连
    variable_to_return: str | None = 'result'
    timeout: int = 60


@app.get('/health')
async def health() -> dict:
    return {'status': 'ok', 'fork': _HAS_FORK}


@app.post('/task/execute')
async def task_execute(req: TaskReq, authorization: str = Header(default='')) -> dict:
    """通用任务执行:沙箱即远程 executor,按 template_code/runner_type 复用平台 runner。"""
    _auth(authorization)
    payload = {
        'template_code': req.template_code,
        'runner_type': req.runner_type,
        'runner_code': req.runner_code,
        'params': req.params,
        'datasources': req.datasources,
        'logger_config': req.logger_config,
        'timeout': req.timeout,
    }
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


@app.post('/python/extract')
async def python_extract(req: PyExtractReq, authorization: str = Header(default='')) -> dict:
    """代码取数(爬虫/任意取数):注入 get_handler(code),code 产出 result(list[dict])。"""
    _auth(authorization)
    payload = {'code': req.code, 'datasources': req.datasources, 'variable_to_return': req.variable_to_return}
    return await run_in_threadpool(_execute_with_timeout, 'pyextract', payload, req.timeout)


def main() -> None:
    import uvicorn

    print(f'[sandbox] FastAPI listening on :{PORT} (fork={_HAS_FORK})', flush=True)
    uvicorn.run(app, host='0.0.0.0', port=PORT, log_level='warning')


if __name__ == '__main__':
    main()
