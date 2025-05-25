"""
任务调度api接口服务
"""
from config import CELERY_DEFAULT_QUEUE
from tasks import task_dict
from web_apps.scheduler.services.scheduler_service import get_jobs, add_or_modify_job, remove_job, run_task, publish_task
from flask_apscheduler.utils import job_to_dict
from utils.common_utils import gen_json_response, format_date


class JobApiService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        page = int(page)
        pagesize = int(pagesize)
        job_list = get_jobs()
        total = len(job_list)
        result = []
        for job in job_list[(page-1) * pagesize: page*pagesize]:
            dic = job_to_dict(job)
            if 'next_run_time' in dic:
                dic['next_run_time'] = format_date(dic['next_run_time'])
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def get_obj_info(self, req_dict):
        job_id = req_dict.get('id')
        dic = job_to_dict(job_id)
        dic['next_run_time'] = format_date(dic['next_run_time'])
        return gen_json_response(data=dic)

    def start_job(self, req_dict):
        '''
        启动调度
        '''
        return handle_job_add(req_dict)

    def remove_job(self, req_dict):
        '''
        删除调度
        '''
        if 'id' in req_dict:
            del_ids = [req_dict['id']]
        elif 'ids' in req_dict:
            del_ids = req_dict.get('ids')
        else:
            del_ids = req_dict
        has_self = [i for i in del_ids if str(i).startswith('self_')]
        if has_self != []:
            return gen_json_response(code=400, msg="含有内置定时任务，禁止删除!")
        for del_id in del_ids:
            remove_job(del_id)
        return gen_json_response(msg="删除成功!", extends={'success': True})


def handle_job_add(req_dict):
    '''
    处理添加任务
    '''
    job_id = str(req_dict.get('job_id'))
    func = req_dict.get('func')
    func_args = req_dict.get('func_args', {})
    run_type = req_dict.get('run_type', 'base')
    trigger = req_dict.get('trigger', {'trigger': 'once'})
    if_exist = req_dict.get('if_exist', 'remove')
    worker_queue = req_dict.get('worker_queue', CELERY_DEFAULT_QUEUE)
    priority = req_dict.get('priority', 1)
    if func not in task_dict:
        return gen_json_response(code=400, msg='未找到该任务执行器')
    func_args = {'func': func, 'kwargs': func_args}
    task_uuid = None
    if run_type == 'base':
        # 本地直接执行
        add_or_modify_job(job_id=job_id, trigger=trigger, func=run_task, if_exist=if_exist, args=func_args)
    else:
        if worker_queue not in [None, '']:
            func_args['worker_queue'] = worker_queue
        func_args['priority'] = priority
        if trigger.get('trigger') == 'once':
            if if_exist == 'remove':
                # 删除定时任务job
                remove_job(job_id)
            # 单次，直接发送任务, 返回celery task_uuid
            print(func_args)
            task_uuid = publish_task(**func_args)
        else:
            # 发送到celery异步执行
            add_or_modify_job(job_id=job_id, trigger=trigger, func=publish_task, if_exist=if_exist, args=func_args)
    return gen_json_response(data={'task_uuid': task_uuid}, code=200, msg='任务调度成功')
