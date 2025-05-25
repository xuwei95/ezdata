from apscheduler.jobstores.redis import RedisJobStore
from config import REDIS_PORT, REDIS_HOST, REDIS_PASS, REDIS_DB


class SchedulerConfig(object):
    SCHEDULER_API_ENABLED = True  # 添加API
    # 配置job store
    SCHEDULER_JOBSTORES = {
        'default': RedisJobStore(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS, db=REDIS_DB)
    }
    timezone = 'Asia/Shanghai'