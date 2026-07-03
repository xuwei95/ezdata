"""数据源连接器的依赖诊断与安装。

ezdata 里唯一带副作用/exec 的能力,故独立成模块(与只读的 facade 分开):
- status():只读——按 handler 的 requirements.txt 查各包是否已装(无副作用);
- install():在**当前解释器**跑 `pip install` 装缺失依赖,并让新包在本进程动态生效。

只依赖标准库(subprocess/sys/importlib),不引入任何 api 依赖 → 不破坏 ezdata 隔离性。
cli / mcp / web 均可直接调用。

动态生效:
- 首次安装此前未 import 过的驱动 → `invalidate_caches()` 后本进程即可用,免重启;
- 升级已被本进程 import 过的包 → 旧模块已在内存,不热替换,需重启;
- 容器运行期装的包在临时层,重建容器会丢,持久化仍应写进镜像/requirements。
"""

import importlib
import subprocess
import sys

from ezdata.handlers import handler_dependencies


def status(source_type: str) -> dict:
    """只读诊断:{source_type, requirements, missing, ready}。"""
    return handler_dependencies(source_type)


def install(source_type: str, *, upgrade: bool = False, timeout: int = 600) -> dict:
    """安装该数据源类型的依赖并在当前进程动态生效。

    upgrade=False:只装 missing(已就绪则不动);upgrade=True:对全部 requirements 跑 -U(可能需重启才完全生效)。
    返回 {source_type, installed, ok, ready, pip_returncode, requested, missing_before/after, message, pip_tail}。
    """
    before = handler_dependencies(source_type)
    reqs = before['requirements']
    if not reqs:
        return {**before, 'installed': False, 'ok': True, 'message': '该数据源无 requirements.txt,无需安装'}
    targets = reqs if upgrade else before['missing']
    if not targets:
        return {**before, 'installed': False, 'ok': True, 'message': '依赖已就绪,无需安装'}

    cmd = [sys.executable, '-m', 'pip', 'install', *(['-U'] if upgrade else []), *targets]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)  # noqa: S603
    except subprocess.TimeoutExpired:
        return {**before, 'installed': False, 'ok': False, 'message': f'pip 安装超时(>{timeout}s)'}

    # 让当前进程的 import 机制发现刚装进 site-packages 的新模块
    importlib.invalidate_caches()

    after = handler_dependencies(source_type)
    ok = proc.returncode == 0 and after['ready']
    tail = (proc.stdout or '') + (('\n' + proc.stderr) if proc.returncode else '')
    return {
        'source_type': source_type,
        'installed': True,
        'ok': ok,
        'ready': after['ready'],
        'pip_returncode': proc.returncode,
        'requested': targets,
        'missing_before': before['missing'],
        'missing_after': after['missing'],
        'message': '安装完成,依赖已就绪(当前进程已动态生效)' if ok else '安装未完全成功,请看 pip_tail',
        'pip_tail': tail[-1200:],
    }
