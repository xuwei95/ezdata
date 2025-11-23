'''
http 接口调用任务调度
'''
from config import SCHEDULER_API_URL
import requests
import json


def get_job_list(req_dict):
    '''
    获取任务job列表
    '''
    url = SCHEDULER_API_URL + '/job/list'
    res = requests.get(url, json=req_dict)
    return json.loads(res.text)


def add_job(req_dict):
    '''
    添加任务job
    '''
    url = SCHEDULER_API_URL + '/job/start'
    res = requests.post(url, json=req_dict)
    return json.loads(res.text)


def remove_job(req_dict):
    '''
    删除任务job
    '''
    url = SCHEDULER_API_URL + '/job/remove'
    res = requests.post(url, json=req_dict)
    return json.loads(res.text)
