from ezetl.etl_task import etl_task_process
from utils.etl_utils import MyEtlTask


class EtlTaskRunner(object):
    '''
    数据集成任务执行器
    '''
    def __init__(self, params, logger):
        self.params = params
        self.logger = logger

    def run(self):
        '''
        执行任务
        '''
        try:
            etl_task_process(params=self.params, run_load=True, logger=self.logger, task_class=MyEtlTask)
            self.logger.info(self.params)
        except Exception as e:
            self.logger.exception(e)
            raise e


if __name__ == '__main__':
    from utils.logger.logger import get_logger
    logger = get_logger('test', 'etl_task')
    task_conf = {

    }
    runner = EtlTaskRunner(task_conf, logger)
    runner.run()
