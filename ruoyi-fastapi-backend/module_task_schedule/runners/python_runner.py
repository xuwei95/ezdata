"""
Python 任务执行器

参数(由前端内置组件 PythonTask 生成)：
- run_type='code'：执行 params.code 中的 Python 代码(需定义 run(params, logger))
- run_type='file'：以子进程执行 params.file 指定的 .py 文件，附加 params.run_params
"""

from typing import Any

from module_task_schedule.runners.base import BaseRunner, register_runner
from module_task_schedule.runners.proc import stream_subprocess
from module_task_schedule.runners.sandbox import run_user_code


@register_runner('PythonTask')
class PythonRunner(BaseRunner):
    """执行 Python 代码(代码模式)或 Python 文件(文件模式)"""

    def run(self) -> Any:
        run_type = self.params.get('run_type', 'code')

        if run_type == 'file':
            file = self.params.get('file')
            if not file:
                raise ValueError('PythonTask 文件模式缺少参数 file')
            run_params = self.params.get('run_params') or ''
            timeout = int(self.params.get('timeout') or 3600)
            command = f'python {file} {run_params}'.strip()
            return stream_subprocess(command, self.logger, timeout)

        code = self.params.get('code')
        if not code:
            raise ValueError('PythonTask 缺少参数 code')
        sandbox = self.context.get('sandbox', True)
        self.logger.info('开始执行 Python 代码')
        result = run_user_code(code, self.params, self.logger, sandbox=sandbox)
        self.logger.info('Python 代码执行完成')
        return result if result is not None else '执行成功'
