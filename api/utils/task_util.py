'''
任务相关函数
'''
from web_apps import db
from web_apps.task.db_models import TaskInstance
from utils.common_utils import get_now_time
from config import ES_CONF, TASK_LOG_INDEX
from utils.es import EsClient
from utils.es_query_tool import EsQueryTool


def get_task_logs(uuid, page=1, pagesize=10):
    '''
    获取任务日志
    '''
    es_client = EsClient(**ES_CONF)
    es_query_tool = EsQueryTool({'index_name': TASK_LOG_INDEX, 'contain[task_uuid]': uuid, 'sort[@timestamp]': 'desc', 'page': page, 'pagesize': pagesize})
    res = es_query_tool.query(es=es_client)
    if res['code'] == 200:
        res['data']['records'] = res['data']['records'][::-1]
    return res


def compute_progress(task_instance_obj):
    '''
    计算任务进度
    :param task_instance_obj:
    :return:
    '''
    total_num = task_instance_obj.total_num
    if total_num is None:
        total_num = 0
    process_num = task_instance_obj.process_num
    if process_num is None:
        process_num = 0
    if total_num == 0:
        if task_instance_obj.status == 'success':
            progress = 100
        elif total_num == 0 and task_instance_obj.status in ['running', 'failed', 'retry']:
            progress = 0
        else:
            progress = 0
    else:
        progress = round((process_num / total_num) * 100, 2)
    return progress


def get_task_instance(uuid, task_obj_id, set_params={}):
    '''
    获取任务实例
    '''
    task_instance_obj = db.session.query(TaskInstance).filter(TaskInstance.id == uuid).first()
    if task_instance_obj is None:
        task_instance_obj = TaskInstance(
            id=uuid,
            task_id=task_obj_id,
            start_time=get_now_time('datetime'),
            status='STARTED'
        )
    for k, v in set_params.items():
        setattr(task_instance_obj, k, v)
    db.session.add(task_instance_obj)
    db.session.commit()
    db.session.flush()
    return task_instance_obj


def update_task_instance(task_instance_obj, update_info=None):
    '''
    更新任务实例
    '''
    if update_info is None:
        update_info = {}
    for k, v in update_info.items():
        setattr(task_instance_obj, k, v)
    db.session.add(task_instance_obj)
    db.session.commit()
    db.session.flush()


def set_task_instance_running(task_instance_obj, task_obj, set_params={}):
    '''
    任务开始运行时将任务信息带入任务实例
    '''
    update_info = {
        'status': 'STARTED',
        'result': '处理中',
        **set_params
    }
    update_task_instance(task_instance_obj, update_info)


def set_task_instance_failed(task_instance_obj, result):
    '''
    任务实例失败时写入信息
    '''
    update_info = {
        'status': 'FAILURE',
        'result':  result,
        'closed': 1,
        'end_time': get_now_time('datetime')
    }
    update_task_instance(task_instance_obj, update_info)


def set_task_instance_retry(task_instance_obj, retry_num=0):
    '''
    任务实例重试时写入信息
    '''
    update_info = {
        'status': 'RETRY',
        'retry_num':  retry_num
    }
    update_task_instance(task_instance_obj, update_info)


def set_task_running_id(task_obj, running_id):
    '''
    为任务设置running_id
    :param task_obj:
    :return:
    '''
    task_obj.running_id = running_id
    db.session.add(task_obj)
    db.session.commit()
    db.session.flush()


if __name__ == '__main__':
    # res = get_task_logs('892e0eea-3d6f-49da-a55f-4eb0462b6226')
    # print(res)
    print(get_now_time('datetime'))