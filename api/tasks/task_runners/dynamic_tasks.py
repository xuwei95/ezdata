from utils.sandbox_utils import get_sandbox_config, execute_python_in_sandbox
from utils.exceptions import TaskException


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
            sandbox_config = get_sandbox_config()

            # 检查是否启用沙箱模式
            if sandbox_config['enabled']:
                self.logger.info('[SANDBOX MODE] Executing dynamic code in sandbox')

                # 将runner_code和调用逻辑合并成完整代码
                full_code = f"""
{self.runner_code}

# 调用动态代码中的run方法
run(params=params, logger=logger)
"""
                context = {
                    'params': self.params
                }

                result = execute_python_in_sandbox(
                    code=full_code,
                    context=context,
                    logger=self.logger,
                    timeout=self.params.get('timeout', sandbox_config['timeout'])
                )

                if not result.get('success'):
                    raise TaskException(f"Sandbox execution failed: {result.get('error', 'Unknown error')}")

                self.logger.info('[SANDBOX MODE] Dynamic code executed successfully')
            else:
                # 直接执行（原有逻辑）
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