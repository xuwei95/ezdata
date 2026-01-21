import os
from subprocess import Popen, PIPE, STDOUT
from utils.exceptions import TaskException
from utils.common_utils import read_file_path
from utils.sandbox_utils import get_sandbox_config, execute_shell_in_sandbox


class ShellTaskRunner(object):
    '''
    shell 任务执行器
    '''

    def __init__(self, params, logger):
        self.params = params
        self.logger = logger

    def run(self):
        '''
        执行任务
        '''
        try:
            run_type = self.params.get('run_type', 'code')
            sandbox_config = get_sandbox_config()

            if run_type == 'code':
                command = self.params.get('code')

                # 检查是否启用沙箱模式
                if sandbox_config['enabled']:
                    self.logger.info('[SANDBOX MODE] Executing Shell command in sandbox')
                    result = execute_shell_in_sandbox(
                        command=command,
                        logger=self.logger,
                        timeout=self.params.get('timeout', sandbox_config['timeout'])
                    )

                    if not result.get('success'):
                        raise TaskException(f"Sandbox execution failed: {result.get('error', 'Unknown error')}")

                    self.logger.info('[SANDBOX MODE] Shell command executed successfully')
                else:
                    # 直接执行（原有逻辑）
                    process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
                    with process.stdout:
                        for raw_line in iter(process.stdout.readline, b''):
                            self.logger.info(raw_line.decode().strip())
                    exitcode = process.wait()
                    if exitcode != 0:
                        raise TaskException(
                            f"Bash command failed. The command returned a non-zero exit code {exitcode}."
                        )
            elif run_type == 'file':
                # 文件模式运行脚本
                file = self.params.get('file')
                flag, is_tmp, file_path = read_file_path(file)
                if not flag:
                    raise TaskException(file_path)
                command = f"bash {file_path}"
                run_params = self.params.get('run_params')
                if run_params:
                    command += f" {run_params}"
                process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
                with process.stdout:
                    for raw_line in iter(process.stdout.readline, b''):
                        self.logger.info(raw_line.decode().strip())
                exitcode = process.wait()
                if is_tmp:
                    os.remove(file_path)
                if exitcode != 0:
                    raise TaskException(
                        f"Bash command failed. The command returned a non-zero exit code {exitcode}."
                    )
        except Exception as e:
            self.logger.exception(e)
            raise e


if __name__ == '__main__':
    from utils.logger.logger import get_logger
    logger = get_logger('test', 'shell_task')
    code = '''
    #!/bin/bash
    ping -c 1 -W 1 192.168.220.1
    # for i in `seq 1 1`
    # do
    #     echo $i
    #     sleep 1
    # done
    '''
    runner = ShellTaskRunner({'code': code}, logger)
    runner.run()