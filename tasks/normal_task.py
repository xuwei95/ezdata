'''
普通任务
'''
import json
from celery_app import celery_app
from web_apps.task.db_models import Task, TaskTemplate
from web_apps import db
from utils.task_util import get_task_instance, update_task_instance, set_task_running_id, set_task_instance_running, set_task_instance_failed, set_task_instance_retry
from utils.log_utils import get_task_logger
from utils.common_utils import gen_uuid, get_now_time
from tasks.task_runners import runner_dict, DynamicTaskRunner
from web_apps.alert.strategys.task_alert_strategys import handle_task_fail_alert


@celery_app.task(bind=True)
def normal_task(self, task_id):
    '''
    普通任务
    :return:
    '''
    uuid = self.request.id if self.request.id else gen_uuid()
    worker = self.request.hostname if self.request.hostname else ''
    logger = get_task_logger(p_name='normal_task', task_log_keys={'task_uuid': uuid})
    logger.info(f'任务开始，任务id:{uuid}, 执行worker:{worker}')
    task_instance_obj = get_task_instance(uuid, task_id, {'worker': worker})
    task_obj = db.session.query(Task).filter(Task.id == task_id).first()
    if task_obj is None or task_obj.del_flag == 1:
        set_task_instance_failed(task_instance_obj, '任务未找到或已被删除')
        return
    retry = task_obj.retry
    countdown = task_obj.countdown
    try:
        params = json.loads(task_obj.params)
        set_task_instance_running(task_instance_obj, task_obj, {'progress': 0})
        set_task_running_id(task_obj, uuid)
        task_template_obj = db.session.query(TaskTemplate).filter(TaskTemplate.code == task_obj.template_code).first()
        runner_type = task_template_obj.runner_type
        if runner_type == 1:
            template_code = task_obj.template_code
            Runner = runner_dict.get(template_code)
            if Runner is None:
                raise ValueError(f'处理失败:未找到任务执行器')
            else:
                task_runner = Runner(params=params, logger=logger)
        else:
            runner_code = task_template_obj.runner_code
            task_runner = DynamicTaskRunner(params=params, logger=logger, runner_code=runner_code)
        task_runner.run()
        update_task_instance(task_instance_obj, {'status': 'success', 'progress': 100, 'closed': 1, 'result': '成功',
                                                 'end_time': get_now_time('datetime')})
    except Exception as e:
        logger.exception(e)
        set_task_instance_failed(task_instance_obj, f'处理失败:{str(e)[:1000]}')
        retries = self.request.retries
        if retries < retry:
            logger.info(f'任务出错，第{retries + 1}次重试')
            set_task_instance_retry(task_instance_obj, retries)
            self.retry(exc=e, countdown=countdown, max_retries=retry)
        else:
            alert_conf = {
                'alert_strategy_ids': task_obj.alert_strategy_ids,
                'task_uuid': uuid,
                'worker': worker,
                'retries': retries,
                'exception': str(e),
                'exception_line': str(e.__traceback__.tb_lineno),
                'exception_file': e.__traceback__.tb_frame.f_globals["__file__"],
                'type': 'normal_task',
                'task_info': task_obj.to_dict()
            }
            handle_task_fail_alert(alert_conf)
            raise e


if __name__ == '__main__':
    # 参数 说明
    # PENDING 任务等待中
    # STARTED 任务已开始
    # SUCCESS 任务执行成功
    # FAILURE 任务执行失败
    # RETRY 任务将被重试
    # REVOKED 任务取消
    # PROGRESS 任务进行中
    # a = normal_task.delay(60)
    # print(a, type(a), type(str(a)))
    a = normal_task('6c6395371bac4f8a8e5b4db23eaa010a')


