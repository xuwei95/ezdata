'''
redis缓存相关工具类
'''
from config import REDIS_HOST, REDIS_PORT, REDIS_PASS, REDIS_DB
import redis
import time
import json

pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS, db=REDIS_DB)
redis_cli = redis.Redis(connection_pool=pool)


def set_key_exp(key, value, exp_time, nx=None):
    '''
    对指定键值对设置过期时间
    :param key:
    :param value:
    :param exp_time:
    :return:
    '''
    try:
        result = redis_cli.set(key, value, ex=exp_time, nx=nx)
        return result
    except Exception as e:
        print(e)
        return None


def get_key_value(key):
    '''
    获取键的值
    :param key:
    :return:
    '''
    try:
        return redis_cli.get(key)
    except Exception as e:
        print(e)
        return None


def hset_dict(name, key, p_dict):
    '''
    对哈希设置键和值
    :param name:
    :param key:
    :param p_dict:
    :return:
    '''
    redis_cli.hset(name, key, json.dumps(p_dict))


def hget_dict(name, key):
    '''
    获取哈希字典的值
    :param name:
    :param key:
    :param p_dict:
    :return:
    '''
    data = redis_cli.hget(name, key)
    if data:
        return json.loads(data)


def hdel_dict(name, key):
    '''
    删除哈希字典的值
    :param name:
    :param key:
    :param p_dict:
    :return:
    '''
    data = redis_cli.hdel(name, key)
    if data:
        return json.loads(data)


def get_lock(name, value, ex=3, timeout=10):
    '''
    获取锁，超时未获取则返回 False
    # nx - 如果设置为True，则只有name不存在时，当前set操作才执行
    # ex - 锁的过期时间（秒）
    # timeout - 最大等待时间（秒），超时返回 False
    '''
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = redis_cli.set(name, value, nx=True, ex=ex)
        if result:
            return True
        time.sleep(0.05)
    return False


def release_lock(name, value):
    '''
    释放锁，仅在锁的持有者与 value 匹配时才删除
    '''
    # redis.get 返回 bytes，需统一编码后比较
    old_value = redis_cli.get(name)
    if old_value is not None and old_value.decode('utf-8') == str(value):
        redis_cli.delete(name)


if __name__ == '__main__':
    a = set_key_exp('test', 1, 10, nx=True)
    print(a)
    a = set_key_exp('test', 1, 10)
    print(a)
    b = get_key_value('test')
    print(b)

