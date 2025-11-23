from celery import Celery
from config import CELERY_BACKEND_URL, CELERY_BROKER_URL, CELERY_DEFAULT_QUEUE
from kombu import Exchange, Queue
from celery_once import QueueOnce

celery_app = Celery(
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL
)
celery_app.conf.ONCE = {
  'backend': 'celery_once.backends.Redis',
  'settings': {
    'url': CELERY_BROKER_URL,
    'default_timeout': 60 * 60
  }
}
# 默认队列
default_exchange = Exchange(CELERY_DEFAULT_QUEUE, type='direct')
# 计算类任务队列，用于处理cpu密集型任务
compute_exchange = Exchange('compute', type='direct')
# eventlet协程队列，用于处理大并发量不耗cpu的任务，如爬虫等
eventlet_exchange = Exchange('eventlet', type='direct')
# 实时任务处理队列,用于处理kafka监听，binlog监听等实时监听任务
realtime_exchange = Exchange('realtime', type='direct')

# 定义不同的队列
CELERY_QUEUES = (
    Queue(CELERY_DEFAULT_QUEUE, default_exchange, routing_key=CELERY_DEFAULT_QUEUE),
    Queue('compute', compute_exchange, routing_key='compute'),
    Queue('eventlet', eventlet_exchange, routing_key='eventlet'),
    Queue('realtime', realtime_exchange, routing_key='realtime')
)


celery_app.conf.update(
    CELERY_DEFAULT_QUEUE=CELERY_DEFAULT_QUEUE,
    CELERY_DEFAULT_EXCHANGE=CELERY_DEFAULT_QUEUE,
    CELERY_DEFAULT_ROUTTING_KEY=CELERY_DEFAULT_QUEUE,
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
    CELERY_RESULT_SERIALIZER='json',
    CELERY_ENABLE_UTC=True,
    CELERY_TASK_PROTOCOL=1,
    CELERYD_FORCE_EXECV=True,    # 有些情况下可以防止死锁
    CELERYD_MAX_TASKS_PER_CHILD=500,    # 每个worker最多执行n个任务就会被销毁重新开启进程，可防止内存泄露
    # CELERYD_TASK_TIME_LIMIT=60 * 60 * 24,   # 单个任务的运行时间不超过此值，否则会被SIGKILL 信号杀死
    # CELERY_IGNORE_RESULT=False,  # 是否忽略结果,
    # 任务结果保留时间
    CELERY_TASK_RESULT_EXPIRES=60 * 60
)


class MyTask(QueueOnce):

    def before_start(self, task_id, args, kwargs):
        '''
        任务开始前
        :param task_id:
        :param args:
        :param kwargs:
        :return:
        '''
        pass