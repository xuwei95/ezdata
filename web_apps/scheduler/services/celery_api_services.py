'''
celery flower api封装
'''
import json
from utils.common_utils import request_url, gen_json_response
from config import FLOWER_API_URL


def post_flower_api(path, req_data, retry=1):
    '''
    向flower api发送post请求, 获取返回数据
    '''
    url = FLOWER_API_URL + path
    res = request_url(url, method='post', json=req_data, retry=retry)
    print(url, res, res.text)
    if res.status_code == 200:
        res_data = json.loads(res.text)
        return True, res_data
    elif res.status_code != 404:
        return False, res.text
    else:
        return False, '404 not found'


def get_flower_api(path, req_data, retry=1):
    '''
    向flower api发送get请求, 获取返回数据
    '''
    url = FLOWER_API_URL + path
    print(url)
    res = request_url(url, method='get', params=req_data, retry=retry)
    print(url, res, res.text)
    if res.status_code == 200:
        res_data = json.loads(res.text)
        return True, res_data
    elif res.status_code != 404:
        res_data = json.loads(res.text)
        return False, res_data
    else:
        return False, '404 not found'


class CeleryApiService(object):
    def __init__(self):
        pass

    def get_worker_base_list(self, req_dict):
        '''
        获取worker 基础信息
        '''
        api_path = '/dashboard?json=1'
        flag, res_data = get_flower_api(api_path, {})
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        data_li = res_data['data']
        total = len(data_li)
        res_data = {
            'records': data_li[(page-1) * pagesize: page*pagesize],
            'total': total
        }
        return gen_json_response(data=res_data)

    def get_worker_list(self, req_dict):
        '''
        获取worker 列表
        '''
        api_path = '/api/workers'
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        refresh = req_dict.get('refresh', True)
        workername = req_dict.get('workername', None)
        status = req_dict.get('status', 'false')
        fetch_data = {
            'refresh': refresh,
            'workername': workername,
            'status': status
        }
        page = int(page)
        pagesize = int(pagesize)
        flag, res_data = get_flower_api(api_path, fetch_data)
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        data_li = []
        for k in res_data:
            print(k, res_data[k])
            if isinstance(res_data[k], dict):
                dic = {
                    'name': k,
                    **res_data[k]
                }
                data_li.append(dic)
        total = len(data_li)
        res_data = {
            'records': data_li[(page - 1) * pagesize: page * pagesize],
            'total': total
        }
        return gen_json_response(data=res_data)

    def restart_worker(self, req_dict):
        '''
        重启worker
        '''
        worker_name = req_dict.get('worker_name')
        api_path = f'/api/worker/pool/restart/{worker_name}'
        flag, res_data = post_flower_api(api_path, {})
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        return gen_json_response(msg='重启worker成功', extends={'success': True})

    def shutdown_worker(self, req_dict):
        '''
        关闭worker
        '''
        workername = req_dict.get('workername')
        api_path = f'/api/worker/shutdown/{workername}'
        flag, res_data = post_flower_api(api_path, {})
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        return gen_json_response(msg='关闭worker成功', extends={'success': True})

    def add_concurrency(self, req_dict):
        '''
        为worker增加并发数
        '''
        workername = req_dict.get('workername')
        concurrency = req_dict.get('concurrency', 1)
        api_path = f'/api/worker/pool/grow/{workername}?n={concurrency}'
        flag, res_data = post_flower_api(api_path, {})
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        return gen_json_response(msg='增加并发数成功', extends={'success': True})

    def reduce_concurrency(self, req_dict):
        '''
        为worker减少并发数
        '''
        workername = req_dict.get('workername')
        concurrency = req_dict.get('concurrency', 1)
        api_path = f'/api/worker/pool/shrink/{workername}?n={concurrency}'
        flag, res_data = post_flower_api(api_path, {})
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        return gen_json_response(msg='减少并发数成功', extends={'success': True})

    def autoscale_concurrency(self, req_dict):
        '''
        为worker设置伸缩并发数
        '''
        worker_name = req_dict.get('worker_name')
        min = req_dict.get('min')
        max = req_dict.get('max')
        api_path = f'/api/worker/pool/autoscale/{worker_name}?min={min}&max={max}'
        flag, res_data = post_flower_api(api_path, {})
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        return gen_json_response(msg='设置伸缩并发数成功', extends={'success': True})

    def add_consumer(self, req_dict):
        '''
        增加消费队列
        '''
        workername = req_dict.get('workername')
        queue = req_dict.get('queue')
        api_path = f'/api/worker/queue/add-consumer/{workername}?queue={queue}'
        flag, res_data = post_flower_api(api_path, {})
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        return gen_json_response(msg='增加消费队列成功', extends={'success': True})

    def cancel_consumer(self, req_dict):
        '''
        移除消费队列
        '''
        workername = req_dict.get('workername')
        queue = req_dict.get('queue')
        api_path = f'/api/worker/queue/cancel-consumer/{workername}?queue={queue}'
        flag, res_data = post_flower_api(api_path, {})
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        return gen_json_response(msg='移除消费队列成功', extends={'success': True})

    def get_task_list(self, req_dict):
        '''
        获取任务列表
        limit - 最大任务数
        offset – 跳过前 n 个任务
        sort_by – 按属性（名称、状态、已接收、已启动）对任务进行排序
        workername – 按 workername 过滤任务
        taskname – 按任务名称过滤任务
        state – 按状态过滤任务
        received_start – 按接收日期过滤任务（必须大于）格式 %Y-%m-%d %H:%M
        received_end – 按接收日期过滤任务（必须小于）格式 %Y-%m-%d %H:%M
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        req_dict['limit'] = pagesize
        req_dict['offset'] = (page - 1) * pagesize
        api_path = f'/api/tasks'
        flag, res_data = get_flower_api(api_path, req_dict)
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        result = []
        for k in res_data:
            dic = res_data[k]
            result.append(dic)
        res_data = {
            'records': result,
            'total': len(result)
        }
        return gen_json_response(data=res_data)

    def get_task_info(self, req_dict):
        '''
        获取任务详情
        '''
        task_id = req_dict.get('task_id')
        api_path = f'/api/task/info/{task_id}'
        flag, res_data = get_flower_api(api_path, {})
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        return gen_json_response(data=res_data)

    def revoke_task(self, req_dict):
        '''
        对任务发送操控信号
        '''
        task_id = req_dict.get('task_id')
        terminate = req_dict.get('terminate', 'false')
        signal = req_dict.get('signal', 'SIGTERM')
        api_path = f'/api/task/revoke/{task_id}?terminate={terminate}&signal={signal}'
        flag, res_data = post_flower_api(api_path, {})
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        return gen_json_response(data=res_data, msg="操作成功", extends={'success': True})

    def get_task_types(self, req_dict):
        '''
        获取任务类型
        '''
        api_path = f'/api/task/types'
        flag, res_data = get_flower_api(api_path, {})
        if not flag:
            return gen_json_response(code=500, msg=res_data)
        return gen_json_response(data=res_data)


if __name__ == '__main__':
    # res = CeleryApiService().get_worker_list({'refresh': False})
    # for i in res['data']:
    #     print(i)
    # res = CeleryApiService().shutdown_worker({'worker_name': 'celery@VM-16-14-ubuntu'})
    # print(res)
    # res = CeleryApiService().restart_worker({'worker_name': 'celery@VM-16-14-ubuntu'})
    # print(res)
    # res = CeleryApiService().add_consumer({'worker_name': 'celery@localhost', 'queue': 'realtime'})
    # print(res)
    # res = CeleryApiService().cancel_consumer({'worker_name': 'celery@localhost', 'queue': 'realtime'})
    # print(res)
    # res = CeleryApiService().add_concurrency({'worker_name': 'celery@w1', 'num': 1})
    # print(res)
    # res = CeleryApiService().reduce_concurrency({'worker_name': 'celery@localhost', 'num': 2})
    # print(res)
    # res = CeleryApiService().autoscale_concurrency({'worker_name': 'celery@localhost', 'min': 1, 'max': 5})
    # print(res)
    res = CeleryApiService().get_task_list({'pagesize': 9})
    print(res)
    # res = CeleryApiService().get_task_info({'task_id': '38ad2b0c-7e69-4e81-8a3e-6376ec249d12'})
    # print(res)
    # res = CeleryApiService().revoke_task({'task_id': '579bfa33-4401-494e-804b-787d166d21c1', 'terminate': 'true'})
    # print(res)

