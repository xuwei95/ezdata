from subprocess import Popen, PIPE, STDOUT
from utils.common_utils import gen_uuid
from utils.exceptions import TaskException
import os


class FlinkTaskRunner(object):
    '''
    flink任务执行器
    '''
    def __init__(self, params, logger):
        self.params = params
        self.logger = logger
        self.tmp_files = []

    def gen_flink_submit_cmd(self):
        '''
        组合参数生成flink Submit命令
        '''
        concurrency = self.params.get('concurrency', 1)
        language = self.params.get('language', 'python')
        master = self.params.get('master')
        package = self.params.get('package')
        command = f"flink run -m {master} -p {concurrency} "
        if language in ['scala', 'java']:
            main_class = self.params.get('class')
            if main_class:
                command += f"-c {main_class} "
            command += f" {package} "
        elif language == 'python':
            code = self.params.get('code')
            tmp_file = f"{gen_uuid()}.py"
            with open(tmp_file, 'w') as f:
                f.write(code)
            command += f"--python {tmp_file} "
            self.tmp_files.append(tmp_file)
        return command

    def run(self):
        '''
        执行任务
        '''
        try:
            command = self.gen_flink_submit_cmd()
            self.logger.info(command)
            process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
            with process.stdout:
                for line in iter(process.stdout.readline, b''):
                    self.logger.info(line.decode().strip())
            exitcode = process.wait()
            print(process, exitcode)
            for temp_file in self.tmp_files:
                os.remove(temp_file)
            if exitcode != 0:
                raise TaskException(
                    f"Bash command failed. The command returned a non-zero exit code {exitcode}."
                )
        except Exception as e:
            self.logger.exception(e)
            raise e


if __name__ == '__main__':
    from utils.logger.logger import get_logger
    logger = get_logger('test', 'flink_task')
    params = {
        'code': 'print("Hello World")',
        'language': 'python',
        'master': '127.0.0.1:8081',
        'concurrency': 1,
    }
    runner = FlinkTaskRunner(params, logger)
    print(runner.gen_flink_submit_cmd())
    # runner.run()