from ezetl.data_models import DataModel
from ezetl.utils.common_utils import trans_rule_value, gen_json_response, parse_json, request_url


class BaseHttpModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        self.conn_conf = self._source['conn_conf']
        self.model_conf = self._model.get('model_conf', {})
        self.url = self.conn_conf.get('url')
        self.method = self.conn_conf.get('method')
        self.headers = parse_json(self.conn_conf.get('headers', {}))
        try:
            self.timeout = int(self.conn_conf.get('timeout'), 60)
        except Exception as e:
            print(e)
            self.timeout = 60
        self.req_body = parse_json(self.conn_conf.get('req_body'), {})
        self.req_params = {}
        self.auth_types = self.model_conf.get('auth_type', '').split(',')

    def get_search_type_list(self):
        '''
        获取可用高级查询类型
        '''
        return [{
            'name': '请求参数',
            'value': 'req_body',
            "default": str(self.req_body)
        }]

    def connect(self):
        '''
        连通性测试
        '''
        try:
            body_rules = [i for i in self.extract_rules if
                        i['field'] == 'search_text' and i['rule'] == 'req_body' and i['value']]
            if body_rules != []:
                req_body = parse_json(body_rules[0]['value'])
                if req_body is not None:
                    if self.method == 'get':
                        self.req_params = req_body
                    else:
                        self.req_body = req_body
            self.response = request_url(method=self.method, url=self.url, headers=self.headers, params=self.req_params, data=self.req_body, timeout=self.timeout)
            return True, '连接成功'
        except Exception as e:
            return False, str(e)[:100]

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及元数据信息
        '''
        self.connect()
        info_prompt = f"""
一个http读取封装类
# 使用示例：
实例化此类的reader对象，读取结果：
res_text = reader.response.text

# MetaData:
response：{self.response.text[:1000]}
"""
        return info_prompt

    def gen_models(self):
        '''
        生成子数据模型
        '''
        model_list = []
        try:
            parse_json(self.response)
            _type = 'json'
        except Exception as e:
            _type = 'html'
        dic = {
            'type': f'http_{_type}',
            'model_conf': {
                "name": f'http_{_type}',
                "auth_type": "query,extract"
            }
        }
        model_list.append(dic)
        return model_list


class HttpApiModel(BaseHttpModel):

    def __init__(self, model_info):
        super().__init__(model_info)

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        flag, err = self.connect()
        if not flag:
            return False, err
        try:
            result = parse_json(self.response.text)
            if isinstance(result, list):
                total = len(result)
                data_li = result
            else:
                total = 1
                data_li = [result]
            res_data = {
                'records': data_li,
                'total': total
            }
            return True, gen_json_response(data=res_data)
        except Exception as e:
            return False, str(e)[:200]

    def read_batch(self):
        '''
        生成器分批读取数据
        :param res_type: 返回形式
        :return:
        '''
        yield self.read_page()


class HttpHtmlModel(BaseHttpModel):

    def __init__(self, model_info):
        super().__init__(model_info)

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        flag, err = self.connect()
        if not flag:
            return False, err
        try:
            result = self.response.text
            res_data = {
                'records': [{"html": result}],
                'total': 1
            }
            return True, gen_json_response(data=res_data)
        except Exception as e:
            return False, str(e)[:200]

    def read_batch(self):
        '''
        生成器分批读取数据
        :param res_type: 返回形式
        :return:
        '''
        yield self.read_page()


