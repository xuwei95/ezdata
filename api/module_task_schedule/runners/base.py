"""
任务执行器(runner)层

runner 与"执行记录存哪张表"完全解耦：给定 params 与 logger 即可执行。
单任务、DAG 节点都复用同一套 runner。

- 内置 runner(runner_type=1)：按模板编码在 runner_dict 中查找(PythonTask/ShellTask...)
- 动态代码 runner(runner_type=2)：由 DynamicRunner 执行模板上维护的 run(params, logger) 代码
"""

from typing import Any

# 内置 runner 注册表：template_code -> runner 类
runner_dict: dict[str, type['BaseRunner']] = {}


def register_runner(template_code: str):
    """注册内置 runner 的装饰器"""

    def _decorator(cls: type['BaseRunner']) -> type['BaseRunner']:
        runner_dict[template_code] = cls
        return cls

    return _decorator


class BaseRunner:
    """runner 基类。子类实现 run() 并返回结果摘要字符串。"""

    def __init__(self, params: dict[str, Any], logger: Any, context: dict[str, Any] | None = None) -> None:
        self.params = params or {}
        self.logger = logger
        self.context = context or {}

    def run(self) -> Any:
        raise NotImplementedError


def ensure_builtin_runners() -> None:
    """确保内置 runner 模块已导入(触发注册)"""
    from module_task_schedule.runners import python_runner, shell_runner  # noqa: F401


def get_runner(template_code: str) -> type[BaseRunner] | None:
    """按 template_code 获取内置 runner 类"""
    ensure_builtin_runners()
    return runner_dict.get(template_code)
