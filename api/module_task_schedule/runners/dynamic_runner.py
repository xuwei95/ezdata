"""
动态代码执行器(runner_type=2)：执行任务模板上维护的 run(params, logger) 代码

与 PythonRunner 的区别：代码在「模板」上维护(一份代码，多个任务复用)，任务只填参数。
"""

from typing import Any

from module_task_schedule.runners.base import BaseRunner
from module_task_schedule.runners.sandbox import run_user_code


class DynamicRunner(BaseRunner):
    """执行模板 runner_code 中的动态代码，代码通过 context['runner_code'] 传入"""

    def run(self) -> Any:
        code = self.context.get('runner_code')
        if not code:
            raise ValueError('动态任务模板缺少 runner_code')
        sandbox = self.context.get('sandbox', True)
        self.logger.info('开始执行动态任务代码')
        result = run_user_code(code, self.params, self.logger, sandbox=sandbox)
        self.logger.info('动态任务代码执行完成')
        return result if result is not None else '执行成功'
