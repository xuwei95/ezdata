# coding: utf-8
"""
Redis 数据模型
支持 String、List、Hash(Map)、Stream 等数据类型
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import json
from etl.data_models import DataModel
from utils.common_utils import gen_json_response
import redis
import logging

logger = logging.getLogger(__name__)


class BaseRedisModel(DataModel):
    """
    Redis 基础模型
    """

    def __init__(self, model_info):
        super().__init__(model_info)
        self.db_type = self._source.get('type')
        self.conn_conf = self._source.get('conn_conf', {})
        model_conf = self._model.get('model_conf', {})
        self.redis_key = model_conf.get('redis_key') or model_conf.get('name')
        self.auth_types = model_conf.get('auth_type', '').split(',')
        self._client = None

    @staticmethod
    def get_connection_args():
        """
        获取连接参数定义
        """
        return {
            'host': {
                'type': 'string',
                'required': True,
                'description': 'Redis服务器地址',
                'default': 'localhost',
                'example': 'localhost'
            },
            'port': {
                'type': 'number',
                'required': True,
                'description': 'Redis端口',
                'default': 6379,
                'example': 6379
            },
            'password': {
                'type': 'password',
                'required': False,
                'description': 'Redis密码',
                'default': ''
            },
            'db': {
                'type': 'number',
                'required': False,
                'description': 'Redis数据库编号',
                'default': 0,
                'example': 0
            }
        }

    @classmethod
    def get_form_config(cls):
        """
        获取基础模型配置表单schema
        """
        return [
            {
                'label': 'Key名称',
                'field': 'redis_key',
                'required': True,
                'component': 'Input',
                'default': '',
                'placeholder': '输入Redis的key名称'
            },
            {
                'label': '允许操作',
                'field': 'auth_type',
                'component': 'JCheckbox',
                'default': 'query,extract,load',
                'componentProps': {
                    'options': [
                        {'label': '查询', 'value': 'query'},
                        {'label': '数据抽取', 'value': 'extract'}
                    ]
                }
            }
        ]

    def gen_client(self):
        """
        生成Redis客户端
        """
        try:
            pool = redis.ConnectionPool(
                host=self.conn_conf.get('host'),
                port=int(self.conn_conf.get('port', 6379)),
                password=self.conn_conf.get('password'),
                db=int(self.conn_conf.get('db', 0)),
                decode_responses=False  # 保持二进制响应，手动decode
            )
            self._client = redis.Redis(connection_pool=pool)
        except Exception as e:
            logger.error(f"创建Redis客户端失败: {e}")
            raise

    def connect(self):
        """
        连通性测试
        """
        try:
            self.gen_client()
            self._client.ping()
            return True, '连接成功'
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False, str(e)[:100]

    def get_info_prompt(self, model_prompt=''):
        """
        获取使用提示及元数据信息
        """
        try:
            if not self._client:
                self.gen_client()

            key_type = self._client.type(self.redis_key).decode('utf-8') if self._client.exists(self.redis_key) else 'unknown'
            info_prompt = f"""
一个基于Redis的模型类，并且提供了一些数据操作的方法
类中部分参数如下:
_client: redis.Redis(connection_pool=pool)
# 使用示例：
实例化此类的reader对象，查询数据：
s = reader._client.get(self.redis_key)
data = s.decode()

# DataSource type:
redis
# MetaData:
key: {self.redis_key}
type: {key_type}
            """
            return info_prompt
        except Exception as e:
            logger.error(f"获取Redis元数据失败: {e}")
            return "Redis Model"

    def gen_models(self):
        """
        生成子数据模型
        """
        try:
            if not self._client:
                self.gen_client()

            keys = self._client.keys("*")
            model_list = []
            type_map = {
                'string': 'redis_string',
                'list': 'redis_list',
                'hash': 'redis_map',
                'set': 'redis_set',
                'zset': 'redis_zset'
            }

            for key in keys[:100]:  # 限制最多返回100个key
                try:
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                    _type = self._client.type(key).decode('utf-8')
                    if _type in type_map:
                        dic = {
                            'type': type_map[_type],
                            'model_conf': {
                                'redis_key': key_str,
                                'auth_type': 'query,extract,load'
                            }
                        }
                        model_list.append(dic)
                except Exception as e:
                    logger.warning(f"处理key失败: {e}")
                    continue

            return model_list
        except Exception as e:
            logger.error(f"生成子模型失败: {e}")
            return []

    def disconnect(self):
        """
        断开连接
        """
        if self._client:
            try:
                self._client.close()
            except:
                pass
            self._client = None

    def __del__(self):
        self.disconnect()


class RedisStringModel(BaseRedisModel):
    """
    Redis String 模型
    处理 Redis String 类型数据
    """

    def __init__(self, model_info):
        super().__init__(model_info)

    def connect(self):
        """
        连通性测试（验证key是否存在）
        """
        try:
            self.gen_client()
            if self._client.exists(self.redis_key):
                return True, '连接成功'
            else:
                return False, '未找到对应key'
        except Exception as e:
            logger.error(f"Redis String连接失败: {e}")
            return False, str(e)[:100]

    def get_res_fields(self):
        """
        获取字段列表
        """
        return [
            {'field_name': 'value', 'field_value': 'value'}
        ]

    def query(self, **kwargs):
        """
        执行查询
        """
        if not self._client:
            flag, msg = self.connect()
            if not flag:
                raise RuntimeError(f'连接失败: {msg}')

        s = self._client.get(self.redis_key)
        if s is None:
            raise RuntimeError(f"未取到对应值")

        return {'value': s.decode('utf-8')}

    def read_page(self, page=1, pagesize=20):
        """
        分页读取数据
        """
        flag, res = self.connect()
        if not flag:
            return False, res

        data_li = []
        try:
            s = self._client.get(self.redis_key)
            if s is None:
                return False, f"未取到对应值"
            data_li.append({'value': s.decode('utf-8')})
        except Exception as e:
            logger.error(f"读取Redis String数据失败: {e}")
            return False, f"{e}"

        res_data = {
            'records': data_li,
            'total': len(data_li),
            'pagination': False  # String类型不需要分页
        }
        return True, gen_json_response(res_data)

    def read_batch(self):
        """
        生成器分批读取数据
        """
        flag, result = self.read_page()
        yield flag, result

    def write(self, res_data):
        """
        写入数据
        """
        if 'load' not in self.auth_types:
            return False, '无写入权限'

        self.load_type = self._load_info.get('load_type', 'insert')
        if self.load_type not in ['insert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'

        if isinstance(res_data, (list, dict)):
            record = json.dumps(res_data, ensure_ascii=False)
        else:
            record = str(res_data)

        try:
            if not self._client:
                self.gen_client()
            self._client.set(self.redis_key, record)
            return True, res_data
        except Exception as e:
            logger.error(f"写入Redis String数据失败: {e}")
            return False, f'{str(e)[:100]}'


class RedisListModel(BaseRedisModel):
    """
    Redis List 模型
    处理 Redis List 类型数据
    """

    def __init__(self, model_info):
        super().__init__(model_info)

    def connect(self):
        """
        连通性测试（验证key是否存在）
        """
        try:
            self.gen_client()
            if self._client.exists(self.redis_key):
                return True, '连接成功'
            else:
                return False, '未找到对应key'
        except Exception as e:
            logger.error(f"Redis List连接失败: {e}")
            return False, str(e)[:100]

    def get_res_fields(self):
        """
        获取字段列表
        """
        return [
            {'field_name': 'value', 'field_value': 'value'},
            {'field_name': 'index', 'field_value': 'index'}
        ]

    def query(self, limit=100, offset=0, **kwargs):
        """
        执行查询
        """
        if not self._client:
            flag, msg = self.connect()
            if not flag:
                raise RuntimeError(f'连接失败: {msg}')

        end = offset + limit - 1
        data = self._client.lrange(self.redis_key, offset, end)
        return [{'value': i.decode('utf-8'), 'index': idx + offset} for idx, i in enumerate(data)]

    def read_page(self, page=1, pagesize=20):
        """
        分页读取数据
        """
        flag, res = self.connect()
        if not flag:
            return False, res

        try:
            total = self._client.llen(self.redis_key)
            start = (page - 1) * pagesize
            end = start + pagesize - 1

            if start >= total:
                data_li = []
            else:
                data = self._client.lrange(self.redis_key, start, end)
                data_li = [{'value': i.decode('utf-8'), 'index': start + idx} for idx, i in enumerate(data)]

        except Exception as e:
            logger.error(f"读取Redis List数据失败: {e}")
            return False, f"{e}"

        res_data = {
            'records': data_li,
            'total': total
        }
        return True, gen_json_response(res_data)

    def read_batch(self):
        """
        生成器分批读取数据
        """
        flag, res = self.connect()
        if not flag:
            yield False, res
            return

        try:
            total = self._client.llen(self.redis_key)
            pagesize = self._extract_info.get('batch_size', 1000)
            total_pages = (total // pagesize) + (1 if total % pagesize > 0 else 0)

            for page in range(1, total_pages + 1):
                flag, result = self.read_page(page, pagesize)
                yield flag, result
        except Exception as e:
            logger.error(f"批量读取Redis List数据失败: {e}")
            yield False, str(e)

    def write(self, res_data):
        """
        写入数据
        """
        if 'load' not in self.auth_types:
            return False, '无写入权限'

        self.load_type = self._load_info.get('load_type', 'insert')
        if self.load_type not in ['insert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'

        # 处理输入数据
        if isinstance(res_data, list) and res_data:
            records = res_data
        elif isinstance(res_data, dict):
            if 'records' in res_data and res_data['records']:
                records = res_data['records']
            else:
                records = [res_data]
        else:
            records = [res_data]

        try:
            if not self._client:
                self.gen_client()

            for record in records:
                if isinstance(record, (dict, list)):
                    record = json.dumps(record, ensure_ascii=False)
                self._client.lpush(self.redis_key, str(record))

            return True, res_data
        except Exception as e:
            logger.error(f"写入Redis List数据失败: {e}")
            return False, f'{str(e)[:100]}'


class RedisListStreamModel(RedisListModel):
    """
    Redis List Stream 模型
    使用 BRPOP 阻塞式读取，用于实时数据流
    """

    def __init__(self, model_info):
        super().__init__(model_info)

    def read_batch(self):
        """
        生成器分批读取数据（阻塞式读取）
        """
        flag, res = self.connect()
        if not flag:
            yield False, res
            return

        while True:
            try:
                result = self._client.brpop(self.redis_key, timeout=1)
                if result:
                    _, v = result
                    res_data = {
                        'records': [{'value': v.decode('utf-8')}],
                        'total': 1
                    }
                    yield True, gen_json_response(res_data)
            except Exception as e:
                logger.error(f"Redis Stream读取失败: {e}")
                # 尝试重新连接
                try:
                    self.gen_client()
                except:
                    yield False, str(e)
                    break


class RedisMapModel(BaseRedisModel):
    """
    Redis Hash(Map) 模型
    处理 Redis Hash 类型数据
    """

    def __init__(self, model_info):
        super().__init__(model_info)

    def connect(self):
        """
        连通性测试（验证key是否存在）
        """
        try:
            self.gen_client()
            if self._client.exists(self.redis_key):
                return True, '连接成功'
            else:
                return False, '未找到对应key'
        except Exception as e:
            logger.error(f"Redis Hash连接失败: {e}")
            return False, str(e)[:100]

    def get_res_fields(self):
        """
        获取字段列表
        """
        return [
            {'field_name': 'key', 'field_value': 'key'},
            {'field_name': 'value', 'field_value': 'value'}
        ]

    def query(self, **kwargs):
        """
        执行查询
        """
        if not self._client:
            flag, msg = self.connect()
            if not flag:
                raise RuntimeError(f'连接失败: {msg}')

        all_data = self._client.hgetall(self.redis_key)
        return [
            {'key': k.decode('utf-8'), 'value': v.decode('utf-8')}
            for k, v in all_data.items()
        ]

    def read_page(self, page=1, pagesize=20):
        """
        分页读取数据
        """
        flag, res = self.connect()
        if not flag:
            return False, res

        try:
            all_keys = self._client.hkeys(self.redis_key)
            all_keys = sorted(all_keys)
            total = len(all_keys)

            start = (page - 1) * pagesize
            end = page * pagesize
            _keys = all_keys[start:end]
            _keys = [i.decode('utf-8') for i in _keys]

            if _keys:
                values = self._client.hmget(self.redis_key, _keys)
                values = [i.decode('utf-8') if i is not None else None for i in values]
                data_li = [{"key": k, "value": v} for k, v in zip(_keys, values)]
            else:
                data_li = []

        except Exception as e:
            logger.error(f"读取Redis Hash数据失败: {e}")
            return False, f"{e}"

        res_data = {
            'records': data_li,
            'total': total
        }
        return True, gen_json_response(res_data)

    def read_batch(self):
        """
        生成器分批读取数据
        """
        flag, res = self.connect()
        if not flag:
            yield False, res
            return

        try:
            all_keys = self._client.hkeys(self.redis_key)
            all_keys = sorted(all_keys)
            total = len(all_keys)
            pagesize = self._extract_info.get('batch_size', 1000)
            total_pages = (total // pagesize) + (1 if total % pagesize > 0 else 0)

            for page in range(1, total_pages + 1):
                start = (page - 1) * pagesize
                end = page * pagesize
                _keys = all_keys[start:end]
                _keys = [i.decode('utf-8') for i in _keys]

                if _keys:
                    values = self._client.hmget(self.redis_key, _keys)
                    values = [i.decode('utf-8') if i is not None else None for i in values]
                    data_li = [{"key": k, "value": v} for k, v in zip(_keys, values)]
                    res_data = {
                        'records': data_li,
                        'total': total
                    }
                    yield True, gen_json_response(res_data)
        except Exception as e:
            logger.error(f"批量读取Redis Hash数据失败: {e}")
            yield False, str(e)

    def write(self, res_data):
        """
        写入数据
        """
        if 'load' not in self.auth_types:
            return False, '无写入权限'

        self.load_type = self._load_info.get('load_type', 'insert')
        if self.load_type not in ['insert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'

        # 处理输入数据
        records = []
        if isinstance(res_data, list) and res_data:
            records = res_data
        elif isinstance(res_data, dict):
            if 'records' in res_data and res_data['records']:
                records = res_data['records']
            else:
                records = [res_data]

        try:
            if not self._client:
                self.gen_client()

            for record in records:
                _key = record.get('key')
                if _key is not None:
                    _key = str(_key)
                    _value = str(record.get('value', ''))
                    self._client.hset(self.redis_key, _key, _value)

            return True, res_data
        except Exception as e:
            logger.error(f"写入Redis Hash数据失败: {e}")
            return False, f'{str(e)[:100]}'
