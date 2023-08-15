# encoding: utf-8
"""
任务调度服务
"""
from flask_apscheduler import APScheduler
from apscheduler.triggers.cron import CronTrigger
from config import CELERY_DEFAULT_QUEUE
from tasks import task_dict
import time

scheduler = APScheduler()


class MyCronTrigger(CronTrigger):
    @classmethod
    def from_crontab(cls, expr, timezone=None):
        expr = expr.replace("？", "*")
        expr = expr.replace("?", "*")
        if expr.endswith(" "):
            expr = expr[0:-1]
        values = expr.split()
        if len(values) == 5:
            return cls(second=0, minute=values[0], hour=values[1], day=values[2], month=values[3],
                       day_of_week=values[4], timezone=timezone)
        elif len(values) == 6:
            return cls(second=values[0], minute=values[1], hour=values[2], day=values[3], month=values[4],
                       day_of_week=values[5], timezone=timezone)
        elif len(values) == 7:
            return cls(second=values[0], minute=values[1], hour=values[2], day=values[3], month=values[4],
                       day_of_week=values[5], year=values[6], timezone=timezone)
        else:
            raise ValueError('Wrong number of fields; got {}, expected 5,6,7'.format(len(values)))


def get_jobs():
    """
    获取job列表
    """
    return scheduler.get_jobs()


def add_job(job_id, trigger, func, args=(), kwargs={}):
    """
    添加一个job
    """
    if isinstance(trigger, dict):
        if trigger.get('trigger') == 'once':
            # 单次，直接运行
            print(func, trigger, args, kwargs)
            func(*args, **kwargs)
        elif trigger.get('trigger') == 'cron' and 'crontab' in trigger:
            trigger = MyCronTrigger.from_crontab(trigger.get('crontab'))
            scheduler.add_job(func=func, id=job_id, trigger=trigger, max_instances=1, args=args, kwargs=kwargs)
        else:
            scheduler.add_job(func=func, id=job_id, **trigger, max_instances=1, args=args, kwargs=kwargs)
    else:
        scheduler.add_job(func=func, id=job_id, trigger=trigger,  max_instances=1, args=args, kwargs=kwargs)


def remove_job(job_id):
    """
    删除一个job
    """
    l_job = scheduler.get_job(job_id)
    if l_job:
        scheduler.remove_job(id=l_job.id)


def add_or_modify_job(job_id, trigger, func, if_exist='remove', args=()):
    """
    添加或者修改一个job
    """
    exist_job = scheduler.get_job(job_id)
    if exist_job:
        if if_exist == 'remove':
            print('job exist, remove')
            scheduler.remove_job(exist_job.id)
        else:
            print('job exist, pass')
            return
    print('add new job')
    if isinstance(args, dict):
        add_job(job_id, trigger, func, kwargs=args)
    else:
        add_job(job_id, trigger, func, args=args)


def run_task(func, args=(), kwargs={}):
    '''
    本地执行任务
    '''
    if isinstance(func, str):
        func = task_dict.get(func)
    print(f'{time.time()}:执行任务{func}_{args}_{kwargs}')
    func(*args, **kwargs)


def publish_task(func, worker_queue=CELERY_DEFAULT_QUEUE, priority=1,  args=(), kwargs={}):
    '''
    发送任务到celery执行
    '''
    if isinstance(func, str):
        func = task_dict.get(func)
    print(f'{time.time()}:发送任务{func}_{args}_{kwargs}_{worker_queue}')
    task_uuid = func.apply_async(queue=worker_queue, args=args, kwargs=kwargs, priority=priority)
    task_uuid = str(task_uuid)
    return task_uuid


def init_scheduler():
    '''
    初始化常驻定时任务
    :return:
    '''
    pass
