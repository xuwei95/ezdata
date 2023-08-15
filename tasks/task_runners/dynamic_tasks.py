class DynamicTaskRunner(object):
    '''
    动态代码任务执行器
    '''

    def __init__(self, params, logger, runner_code=''):
        self.params = params
        self.logger = logger
        self.runner_code = runner_code

    def run(self):
        '''
        执行任务
        '''
        try:
            exec(self.runner_code, globals())
            # 调用动态代码中的run方法执行逻辑
            run(params=self.params, logger=self.logger)
        except Exception as e:
            self.logger.exception(e)
            raise e


if __name__ == '__main__':
    from utils.logger.logger import get_logger
    logger = get_logger('test', 'dynamic_task')
    runner_code = """
def run(params, logger):
    logger.info(params)
    """
    runner = DynamicTaskRunner({'a': '1'}, logger, runner_code)
    runner.run()