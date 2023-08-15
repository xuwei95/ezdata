import os
from subprocess import Popen, PIPE, STDOUT
from utils.exceptions import TaskException
from utils.common_utils import read_file_path


class PyTaskRunner(object):
    '''
    python 任务执行器
    '''
    def __init__(self, params, logger):
        self.params = params
        self.logger = logger

    def run(self):
        '''
        执行任务
        '''
        try:
            print(self.params)
            run_type = self.params.get('run_type', 'code')
            if run_type == 'code':
                exec(self.params.get('code'), {'uuid': self.params.get('uuid'), 'logger': self.logger})
            elif run_type == 'file':
                # 文件模式运行脚本
                file = self.params.get('file')
                flag, is_tmp, file_path = read_file_path(file)
                if not flag:
                    raise TaskException(file_path)
                command = f"python {file_path}"
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
