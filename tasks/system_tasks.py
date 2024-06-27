'''
系统任务
'''
import json
from celery_app import celery_app
from web_apps import db, app
from utils.log_utils import get_task_logger
from utils.common_utils import gen_uuid, parse_json, format_date, get_now_time
from web_apps.scheduler.services.celery_api_services import CeleryApiService
from config import ES_CONF
from ezetl.libs.es import EsClient
from datetime import datetime, timedelta
from web_apps.task.db_models import TaskInstance


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
        # 找到运行时长超过10分钟的未关闭任务
        last_time = format_date(get_now_time() - 600, res_type='timestamp')
        unclosed_tasks = db.session.query(TaskInstance).filter(TaskInstance.closed == 0, TaskInstance.start_time <= last_time).all()
        for task in unclosed_tasks:
            res = CeleryApiService().get_task_info({'task_id': task.id})
            if res['status'] == '':
                pass


@celery_app.task(bind=True)
def self_remove_task_history(self):
    '''
    清除任务实例记录及日志
    '''
    es_client = EsClient(**ES_CONF)
    save_days = 7
    # 计算n天前的日期
    three_days_ago = datetime.now() - timedelta(days=save_days)
    # 构造查询条件，删除3天前的数据
    query = {
        "query": {
            "range": {
                "@timestamp": {
                    "lt": three_days_ago.strftime("%Y-%m-%dT%H:%M:%S")
                }
            }
        }
    }

    # 执行删除操作
    result = es_client.deleteAllByQuery("sys_logs", query)
    # 输出结果
    # 执行删除操作
    result = es_client.deleteAllByQuery("task_logs", query)
    # 输出结果
    with app.app_context():
        query = db.session.query(TaskInstance).filter(TaskInstance.start_time <= three_days_ago)
        deleted_instances = query.delete()
        print(deleted_instances)
        # 提交更改
        db.session.commit()
        # 关闭会话
        db.session.close()


if __name__ == '__main__':
    a = self_scan_unclosed_tasks()