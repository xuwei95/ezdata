"""
Shell 任务执行器：执行 Shell 命令/脚本

参数(由前端内置组件 ShellTask 生成)：
- run_type='code'：执行 params.code 中的 Shell 脚本
- run_type='file'：执行 params.file 指定的脚本文件，附加 params.run_params
兼容旧参数 params.command(等价于 code)。

安全提示：Shell 执行权限较大，应仅允许超管创建此类任务，并尽量在受限容器中运行 worker。
"""

from typing import Any

from module_task_schedule.runners.base import BaseRunner, register_runner
from module_task_schedule.runners.proc import stream_subprocess


@register_runner('ShellTask')
class ShellRunner(BaseRunner):
    """执行 Shell 命令，逐行将 stdout/stderr 写入任务日志"""

    def run(self) -> Any:
        run_type = self.params.get('run_type', 'code')
        timeout = int(self.params.get('timeout') or 3600)

        if run_type == 'file':
            file = self.params.get('file')
            if not file:
                raise ValueError('ShellTask 文件模式缺少参数 file')
            run_params = self.params.get('run_params') or ''
            command = f'bash {file} {run_params}'.strip()
        else:
            command = self.params.get('code') or self.params.get('command')
            if not command:
                raise ValueError('ShellTask 缺少参数 code')
            # 前端 Monaco 编辑器在 Windows 上保存的脚本带 CRLF；worker 的 /bin/sh 为 dash，
            # 行尾的 \r 会粘到关键字上(如 do\r != do)导致「Syntax error: word unexpected」退出码2。
            # 统一规整为 LF，保证多行 Shell 脚本可正确执行。
            command = command.replace('\r\n', '\n').replace('\r', '\n')

        return stream_subprocess(command, self.logger, timeout)
