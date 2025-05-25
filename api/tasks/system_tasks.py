'''
系统任务
'''
import json
from celery_app import celery_app
from web_apps import db, app
from utils.log_utils import get_task_logger
from utils.common_utils import gen_uuid, parse_json, format_date, get_now_time
from web_apps.scheduler.services.celery_api_services import CeleryApiService
from config import LOGGER_TYPE, ES_CONF, SYS_CONF
from etl.libs.es import EsClient
from datetime import datetime, timedelta
from web_apps.task.db_models import TaskInstance
from utils.task_util import update_task_instance


@celery_app.task(bind=True)
def self_scan_unclosed_tasks(self):
    '''
    扫描未关闭任务,同步状态
    :return:
    '''
    with app.app_context():
        uuid = self.request.id if self.request.id else gen_uuid()
        worker = self.request.hostname if self.request.hostname else ''
        logger = get_task_logger(p_name='self_scan_unclosed_tasks', task_log_keys={'task_uuid': uuid})
        logger.info(f'任务开始，任务id:{uuid}, 执行worker:{worker}')
        # 找到运行时长超过10分钟的未关闭任务,同步状态
        last_time = format_date(get_now_time() - 600, res_type='datetime')
        unclosed_tasks = db.session.query(TaskInstance).filter(TaskInstance.closed == 0, TaskInstance.start_time <= last_time).all()
        for task in unclosed_tasks:
            res = CeleryApiService().get_task_info({'task_id': task.id})
            if res['code'] == 200:
                info = res['data']
                state = info['state']
                update_info = {}
                if state == 'SUCCESS':
                    update_info = {
                        'status': 'SUCCESS',
                        'result': '执行成功',
                        'closed': 1,
                        'end_time': format_date(int(info.get('succeeded', get_now_time())),  res_type='datetime')
                    }
                if state == 'FAILURE':
                    update_info = {
                        'status': 'FAILURE',
                        'result': '执行失败',
                        'closed': 1,
                        'end_time': format_date(int(info.get('failed', get_now_time())), res_type='datetime')
                    }
                if state == 'REVOKED':
                    update_info = {
                        'status': 'REVOKED',
                        'result': '已撤销',
                        'closed': 1,
                        'end_time': format_date(int(info.get('revoked', get_now_time())), res_type='datetime')
                    }
                if state == 'IGNORED':
                    update_info = {
                        'status': 'IGNORED',
                        'result': '已忽略',
                        'closed': 1,
                        'end_time': format_date(int(info.get('ignored', get_now_time())), res_type='datetime')
                    }
                if update_info != {}:
                    update_task_instance(task, update_info)


@celery_app.task(bind=True)
def self_remove_task_history(self):
    '''
    清除任务实例记录及日志
    '''
    with app.app_context():
        uuid = self.request.id if self.request.id else gen_uuid()
        worker = self.request.hostname if self.request.hostname else ''
        logger = get_task_logger(p_name='self_remove_task_history', task_log_keys={'task_uuid': uuid})
        logger.info(f'任务开始，任务id:{uuid}, 执行worker:{worker}')
        save_days = int(SYS_CONF.get('SAVE_DSYS', 7))
        # 计算n天前的日期
        days_ago = datetime.now() - timedelta(days=save_days)
        if LOGGER_TYPE == '':
            es_client = EsClient(**ES_CONF)
            # 构造查询条件，删除3天前的数据
            query = {
                "query": {
                    "range": {
                        "@timestamp": {
                            "lt": days_ago.strftime("%Y-%m-%dT%H:%M:%S")
                        }
                    }
                }
            }
            # 执行删除操作
            result = es_client.deleteAllByQuery("sys_logs", query)
            logger.info(f"清除过期系统日志{result}")
            # 执行删除操作
            result = es_client.deleteAllByQuery("task_logs", query)
            logger.info(f"清除过期任务日志{result}")
        query = db.session.query(TaskInstance).filter(TaskInstance.start_time <= days_ago, TaskInstance.closed == 1)
        deleted_instances = query.delete()
        # 提交更改
        db.session.commit()
        # 关闭会话
        db.session.close()
        logger.info(f"清除任务实例记录{deleted_instances}")


if __name__ == '__main__':
    # a = self_remove_task_history()
    self_scan_unclosed_tasks()