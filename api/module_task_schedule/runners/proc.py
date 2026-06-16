"""子进程执行公共逻辑：执行命令并逐行将 stdout/stderr 写入任务日志。

供 ShellTask(代码/文件模式)、PythonTask(文件模式)复用。
安全提示：执行权限较大，应仅允许超管创建此类任务，并尽量在受限容器中运行 worker。
"""

import subprocess
from typing import Any


def stream_subprocess(command: str, logger: Any, timeout: int = 3600) -> str:
    """执行 shell 命令，逐行写日志；退出码非0则抛出异常。返回执行摘要。"""
    logger.info(f'开始执行: {command}')
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace',
    )
    output_lines: list[str] = []
    try:
        assert process.stdout is not None
        for line in process.stdout:
            line = line.rstrip('\n')
            output_lines.append(line)
            logger.info(line)
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        raise RuntimeError(f'命令执行超时(>{timeout}s)')

    if process.returncode != 0:
        raise RuntimeError(f'命令退出码非0: {process.returncode}')
    logger.info('命令执行完成')
    return f'退出码0，输出{len(output_lines)}行'
