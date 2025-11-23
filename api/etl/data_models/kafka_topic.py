import json
import datetime
from etl.data_models import DataModel
from kafka import KafkaConsumer, KafkaProducer
from etl.libs.kafka_utils import fetch_kafka_data_by_page, list_all_topics
from etl.utils.common_utils import gen_json_response, parse_json


class DateEncoder(json.JSONEncoder):
    """
    自定义类，解决报错：
    TypeError: Object of type 'datetime' is not JSON serializable
    """

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')

        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")

        else:
            return json.JSONEncoder.default(self, obj)


class KafkaTopicModel(DataModel):
    '''
    Kafka
    '''

    def __init__(self, model_info):
        super().__init__(model_info)
        model_conf = self._model.get('model_conf', {})
        self.topic = model_conf.get('name')
        conn_conf = self._source['conn_conf']
        self.bootstrap_servers = conn_conf['bootstrap_servers']
        conn_setting = {'bootstrap_servers': self.bootstrap_servers}
        self.group_id = None
        ext_params = parse_json(self._model.get('ext_params'), {})
        for k in ext_params:
            conn_setting[k] = ext_params[k]
        self.err_info = ''
        self.read_type = 'latest'  # 默认从最新开始读
        self.gen_extract_rules()  # 判断是从头读还是从现在开始读
        conn_setting['auto_offset_reset'] = self.read_type
        if self._extract_info and self.topic:
            try:
                if isinstance(self.topic, list):
                    self.consumer = KafkaConsumer(self.topic[0], **conn_setting)
                    self.consumer.subscribe(self.topic)
                else:
                    self.consumer = KafkaConsumer(self.topic, **conn_setting)
            except Exception as e:
                self.err_info = str(e)
        if self._load_info:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda x: json.dumps(x, cls=DateEncoder).encode('utf-8'),
                    api_version=(0, 10)
                )
            except Exception as e:
                print(e)
                self.err_info = str(e)

    def connect(self):
        '''
        连通性测试
        '''
        try:
            consumer = KafkaConsumer(bootstrap_servers=self.bootstrap_servers)
            topics = consumer.topics()
            if self.topic and self.topic not in topics:
                return False, '连接失败:未找到该topic'
            return True, '连接成功'
        except Exception as e:
            return False, '连接失败:' + str(e)

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及数据库元数据信息
        '''
        demo_data = self.read_page()
        info_prompt = f"""
    一个读取kafka数据的模型类
    # 使用示例：
    实例化此类的reader对象，查询最新数据：
    data = reader.read_page()

    ## 数据示例
    {demo_data}
            """
        return info_prompt
    
    def gen_models(self):
        '''
        生成子数据模型
        '''
        topic_list = list_all_topics(self.bootstrap_servers)
        model_list = []
        for topic in topic_list:
            dic = {
                'type': f'kafka_topic',
                'model_conf': {
                    "name": topic,
                    "auth_type": "query,extract,load"
                }
            }
            model_list.append(dic)
        return model_list

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        return None

    def get_search_type_list(self):
        '''
        获取可用高级查询类型
        '''
        return [{
            'name': '读取方式',
            'value': 'read_type',
            "default": f"latest"
        }]

    def get_extract_rules(self):
        '''
        获取可筛选项
        :return:
        '''
        rules = []
        return rules

    def gen_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        rules = [i for i in self.extract_rules if i['rule'] == 'read_type']
        if rules != []:
            i = rules[0]
            if i['value'] == 'earliest':
                self.read_type = 'earliest'
            else:
                self.read_type = 'latest'

    def read_page(self, page=1, pagesize=1):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        res_data = fetch_kafka_data_by_page(
            page=page,
            pagesize=pagesize,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            topic=self.topic
        )
        return True, res_data

    def read_batch(self):
        '''
        生成器分批读取数据
        :return:
        '''
        for msg in self.consumer:
            try:
                data = msg.value
                if isinstance(data, bytes):
                    data = data.decode()
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except Exception as e:
                        print(e)
                res_data = {
                    'records': [data],
                    'total': 1
                }
                yield True, gen_json_response(res_data)
            except Exception as e:
                print(e)

    def write(self, res_data):
        '''
        写入数据
        :param res_data: 
        :return: 
        '''
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'
        records = []
        if isinstance(res_data, list) and res_data != []:
            records = res_data
        if isinstance(res_data, dict):
            if 'records' in res_data and res_data['records'] != []:
                records = res_data['records']
            else:
                records = [res_data]
        try:
            for c in records:
                self.producer.send(self.topic, value=c)
                print('produce', c)
        except Exception as e:
            return False, f'{str(e)[:-100]}'
        return True, records

