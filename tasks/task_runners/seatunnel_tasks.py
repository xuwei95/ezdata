from subprocess import Popen, PIPE, STDOUT
from utils.common_utils import gen_uuid
import os


class SeaTunnelTaskRunner(object):
    '''
    seatunnel任务执行器
    '''
    def __init__(self, params, logger):
        self.params = params
        self.logger = logger
        self.tmp_files = []

    def gen_seatunnel_submit_cmd(self):
        '''
        组合参数生成seatunnel 运行命令
        '''
        depoly_mode = self.params.get('deploy_mode', 'client')
        master = self.params.get('master')
        engine = self.params.get('engine', 'spark')
        commond = f"$SEATUNNEL/bin/start-seatunnel-{engine}.sh "
        if master is None:
            return False, 'master不能为空'
        commond += f"--master {master} "
        commond += f"--deploy-mode {depoly_mode} "
        code = self.params.get('code')
        tmp_file = f"{gen_uuid()}.conf"
        with open(tmp_file, 'w') as f:
            f.write(code)
        commond += f"--config {tmp_file} "
        self.tmp_files.append(tmp_file)
        return commond

    def run(self):
        '''
        执行任务
        '''
        try:
            command = self.gen_seatunnel_submit_cmd()
            self.logger.info(command)
            process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
            with process.stdout:
                for line in iter(process.stdout.readline, b''):
                    self.logger.info(line.decode().strip())
            exitcode = process.wait()
            print(process, exitcode)
            for temp_file in self.tmp_files:
                os.remove(temp_file)
        except Exception as e:
            self.logger.exception(e)
            raise e


if __name__ == '__main__':
    from utils.logger.logger import get_logger
    logger = get_logger('test', 'spark_task')
    params = {
        'deploy_mode': 'client',
        'master': 'spark://124.220.57.72:7077',
        'code': '''
env {
   spark.app.name = "SeaTunnel"
  spark.executor.instances = 2
  spark.executor.cores = 1
  spark.executor.memory = "1g"
}
source {
 Fake {
    result_table_name = "my_dataset"
  }
}
transform_algs {
}

sink {
  Console {}
}
        ''',
    }
    runner = SeaTunnelTaskRunner(params, logger)
    print(runner.gen_seatunnel_submit_cmd())
    # runner.run()