import json
from etl.data_models import DataModel
from etl.utils.common_utils import gen_json_response
import redis


class BaseRedisModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        self.db_type = self._source.get('type')
        self.conn_conf = self._source['conn_conf']
        model_conf = self._model.get('model_conf', {})
        self.redis_key = model_conf.get('redis_key')
        self.auth_types = model_conf.get('auth_type', '').split(',')

    def gen_client(self):
        pool = redis.ConnectionPool(
            host=self.conn_conf.get('host'),
            port=self.conn_conf.get('port'),
            password=self.conn_conf.get('password'),
            db=self.conn_conf.get('db'))
        self._client = redis.Redis(connection_pool=pool)

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及元数据信息
        '''
        info_prompt = f"""
一个基于 读取redis的模型类，并且提供了一些数据操作的方法
类中部分参数如下:
_client: redis.Redis(connection_pool=pool)
# 使用示例：
实例化此类的reader对象，查询数据：
s = reader._client.get(self.redis_key)
data = s.decode()

# DataSource type: 
redis
# MetaData:
type：{self._client.type(self.redis_key).decode('utf-8')}
        """
        return info_prompt

    def connect(self):
        '''
        连通性测试
        '''
        try:
            self.gen_client()
            return True, '连接成功'
        except Exception as e:
            return False, str(e)[:100]

    def gen_models(self):
        '''
        生成子数据模型
        '''
        keys = self._client.keys("*")
        model_list = []
        type_map = {
            'string': 'string',
            'list': 'list',
            'map': 'map',
        }
        for key in keys:
            _type = self._client.type(key).decode('utf-8')
            if _type in type_map:
                dic = {
                    'type': f'redis_{_type}',
                    'model_conf': {
                        "name": key,
                        "auth_type": "query,create,edit_fields,delete,extract,load"
                    }
                }
                model_list.append(dic)
        return model_list


class RedisStringModel(BaseRedisModel):

    def __init__(self, model_info):
        super().__init__(model_info)

    def connect(self):
        '''
        连通性测试
        '''
        try:
            self.gen_client()
            if self._client.exists(self.redis_key):
                return True, '连接成功'
            else:
                return False, '未找到对应key'
        except Exception as e:
            return False, str(e)[:100]

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        flag, res = self.connect()
        if not flag:
            return False, res
        data_li = []
        try:
            s = self._client.get(self.redis_key)
            if s is None:
                return False, f"未取到对应值"
            data_li.append({'value': s.decode()})
        except Exception as e:
            return False, f"{e}"
        res_data = {
            'records': data_li,
            'total': len(data_li)
        }
        return True, gen_json_response(res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :param res_type: 返回形式
        :return:
        '''
        yield self.read_page()

    def write(self, res_data):
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'
        if isinstance(res_data, list) or isinstance(res_data, dict):
            record = json.dumps(res_data, ensure_ascii=False)
        else:
            record = res_data
        try:
            self._client.set(self.redis_key, record)
        except Exception as e:
            return False, f'{str(e)[:100]}'
        return True, res_data


class RedisListModel(BaseRedisModel):

    def __init__(self, model_info):
        super().__init__(model_info)

    def connect(self):
        '''
        连通性测试
        '''
        try:
            self.gen_client()
            if self._client.exists(self.redis_key):
                return True, '连接成功'
            else:
                return False, '未找到对应key'
        except Exception as e:
            return False, str(e)[:100]

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        flag, res = self.connect()
        if not flag:
            return False, res
        try:
            total = self._client.llen(self.redis_key)
            start = (page - 1) * pagesize
            end = page*pagesize
            if start > total:
                data_li = []
            else:
                if end > total:
                    end = total
                data_li = self._client.lrange(self.redis_key, start, end)
                data_li = [{'value': i.decode()} for i in data_li]
        except Exception as e:
            return False, f"{e}"
        res_data = {
            'records': data_li,
            'total': len(data_li)
        }
        return True, gen_json_response(res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :param res_type: 返回形式
        :return:
        '''
        flag, res = self.connect()
        if not flag:
            yield False, res
        total = self._client.llen(self.redis_key)
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            yield self.read_page(page, pagesize)

    def write(self, res_data):
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'
        if isinstance(res_data, list) and res_data != []:
            records = res_data
        elif isinstance(res_data, dict):
            if 'records' in res_data and res_data['records'] != []:
                records = res_data['records']
            else:
                records = [res_data]
        else:
            records = [res_data]
        try:
            for record in records:
                if isinstance(record, dict) or isinstance(record, list):
                    record = json.dumps(record, ensure_ascii=False)
                self._client.lpush(self.redis_key, record)
        except Exception as e:
            return False, f'{str(e)[:100]}'
        return True, res_data


class RedisListStreamModel(RedisListModel):

    def __init__(self, model_info):
        super().__init__(model_info)

    def read_batch(self):
        '''
        生成器分批读取数据
        :param res_type: 返回形式
        :return:
        '''
        flag, res = self.connect()
        if not flag:
            yield False, res
        while True:
            try:
                _, v = self._client.brpop(self.redis_key)
                res_data = {
                    'records': [{'value': v.decode()}],
                    'total': 1
                }
                yield True, gen_json_response(res_data)
            except Exception as e:
                print(e)
                self.gen_client()


class RedisMapModel(BaseRedisModel):

    def __init__(self, model_info):
        super().__init__(model_info)

    def connect(self):
        '''
        连通性测试
        '''
        try:
            self.gen_client()
            if self._client.exists(self.redis_key):
                return True, '连接成功'
            else:
                return False, '未找到对应key'
        except Exception as e:
            return False, str(e)[:100]

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        flag, res = self.connect()
        if not flag:
            return False, res
        try:
            all_keys = self._client.hkeys(self.redis_key)
            all_keys = sorted(all_keys)
            total = len(all_keys)
            _keys = all_keys[(page - 1) * pagesize:page * pagesize]
            _keys = [i.decode() for i in _keys]
            values = self._client.hmget(self.redis_key, _keys)
            values = [i.decode() if i is not None else i for i in values]
            data_li = [{"key": k, "value": v} for k, v in zip(_keys, values)]
        except Exception as e:
            return False, f"{e}"
        res_data = {
            'records': data_li,
            'total': total
        }
        return True, gen_json_response(res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :param res_type: 返回形式
        :return:
        '''
        flag, res = self.connect()
        if not flag:
            yield False, res
        all_keys = self._client.hkeys(self.redis_key)
        all_keys = sorted(all_keys)
        total = len(all_keys)
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            _keys = all_keys[(page - 1) * pagesize:page * pagesize]
            _keys = [i.decode() for i in _keys]
            if _keys != []:
                values = self._client.hmget(self.redis_key, _keys)
                values = [i.decode() if i is not None else i for i in values]
                data_li = [{"key": k, "value": v} for k, v in zip(_keys, values)]
                res_data = {
                    'records': data_li,
                    'total': total
                }
                yield True, res_data

    def write(self, res_data):
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'
        records = []
        if isinstance(res_data, list) and res_data != []:
            records = res_data
        elif isinstance(res_data, dict):
            if 'records' in res_data and res_data['records'] != []:
                records = res_data['records']
            else:
                records = [res_data]
        try:
            for record in records:
                _key = record.get('key')
                if _key is not None:
                    _key = str(_key)
                    _value = str(record.get('value'))
                    self._client.hset(self.redis_key, _key, _value)
        except Exception as e:
            return False, f'{str(e)[:100]}'
        return True, res_data
