"""
用户代码执行沙箱(软沙箱)

说明：纯 Python 进程内沙箱无法做到绝对安全，本模块提供"尽力而为"的隔离：
- 限制可用内建函数(去掉 open/eval/exec/compile/input 等危险项)
- import 仅放行白名单内的模块
真正的强隔离仍需配合：模板/动态代码仅超管可创建、Celery worker 运行在受限容器/低权限账号。
"""

import builtins as _builtins
from typing import Any, Callable

# 允许 import 的模块白名单(可按需扩展)
ALLOWED_IMPORTS = {
    'time',
    'datetime',
    'math',
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
}

# 禁用的危险内建
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
}


def _build_safe_builtins() -> dict[str, Any]:
    """构造受限内建命名空间"""
    safe: dict[str, Any] = {}
    for name in dir(_builtins):
        if name.startswith('_'):
            continue
        if name in _BLOCKED_BUILTINS:
            continue
        safe[name] = getattr(_builtins, name)

    def _guarded_import(name: str, *args: Any, **kwargs: Any):
        top = name.split('.')[0]
        if top not in ALLOWED_IMPORTS:
            raise ImportError(f'沙箱模式下禁止导入模块: {name}')
        return _builtins.__import__(name, *args, **kwargs)

    safe['__import__'] = _guarded_import
    return safe


def run_user_code(code: str, params: dict[str, Any], logger: Any, sandbox: bool = True) -> Any:
    """
    执行用户编写的 Python 代码，代码需定义 run(params, logger) 函数。

    :param code: 用户代码文本
    :param params: 传给 run 的参数字典
    :param logger: 传给 run 的任务日志记录器
    :param sandbox: 是否启用软沙箱(限制内建与import)
    :return: run(params, logger) 的返回值
    """
    if not code or not code.strip():
        raise ValueError('代码为空')

    if sandbox:
        exec_globals: dict[str, Any] = {'__builtins__': _build_safe_builtins()}
    else:
        exec_globals = {'__builtins__': _builtins}

    compiled = compile(code, '<task_code>', 'exec')
    exec(compiled, exec_globals)  # noqa: S102 - 受控执行用户任务代码

    run_func: Callable[..., Any] | None = exec_globals.get('run')
    if not callable(run_func):
        raise ValueError('代码必须定义 run(params, logger) 函数')
    return run_func(params, logger)
