from subprocess import Popen, PIPE, STDOUT
from utils.common_utils import gen_uuid
from utils.exceptions import TaskException
import os


class SparkTaskRunner(object):
    '''
    Spark任务执行器
    '''
    def __init__(self, params, logger):
        self.params = params
        self.logger = logger
        self.tmp_files = []

    def gen_spark_submit_cmd(self):
        '''
        组合参数生成Spark Submit命令
        '''
        deploy_mode = self.params.get('deploy_mode', 'client')
        language = self.params.get('language', 'python')
        master = self.params.get('master')
        package = self.params.get('package')
        command = "$SPARK_HOME/bin/spark-submit "
        if deploy_mode in ['cluster']:
            if master is None:
                return False, 'master不能为空'
            command += f"--master {master} "
        if language in ['scala', 'java']:
            command += f"--deploy-mode {deploy_mode} "
            main_class = self.params.get('class')
            if main_class:
                command += f"--class {main_class} "
            command += f" {package} "
        elif language == 'python':
            code = self.params.get('code')
            tmp_file = f"{gen_uuid()}.py"
            with open(tmp_file, 'w') as f:
                f.write(code)
            command += f" {tmp_file} "
            self.tmp_files.append(tmp_file)
        return command

    def run(self):
        '''
        执行任务
        '''
        try:
            command = self.gen_spark_submit_cmd()
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
    logger = get_logger('test', 'spark_task')
    params = {
        'deploy_mode': 'client',
        'class': 'org.apache.spark.examples.SparkPi',
        'package': '$SPARK_HOME/examples/jars/spark-examples_2.11-2.4.7.jar',
        'language': 'java',
    }
    params = {
        'deploy_mode': 'cluster',
        'master': 'spark://124.220.57.72:7077',
        'class': 'org.apache.spark.examples.SparkPi',
        'package': '$SPARK_HOME/examples/jars/spark-examples_2.11-2.4.7.jar',
        'language': 'java',
    }
    # params = {
    #     'deploy_mode': 'client',
    #     'code': 'print("Hello World")',
    #     'language': 'python',
    # }
    runner = SparkTaskRunner(params, logger)
    print(runner.gen_spark_submit_cmd())
    # runner.run()