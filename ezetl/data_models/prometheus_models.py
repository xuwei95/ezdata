from ezetl.data_models import DataModel
from ezetl.utils.common_utils import trans_rule_value, gen_json_response, format_date
from ezetl.libs.prometheus import PrometheusClient


class BasePromModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        self.conn_conf = self._source['conn_conf']
        self.model_conf = self._model.get('model_conf', {})
        self.url = self.conn_conf.get('url')
        self.auth_types = self.model_conf.get('auth_type', '').split(',')
        self._client = PrometheusClient(**{"url": self.url, 'disable_ssl': True})

    def connect(self):
        '''
        连通性测试
        '''
        try:
            self._client.conn_test()
            return True, '连接成功'
        except Exception as e:
            return False, str(e)[:100]

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及元数据信息
        '''
        info_prompt = f"""
一个 读取prometheus的模型类，并且提供了一些数据操作的方法
类中部分参数如下:
_client: prometheus_api_client库的PrometheusConnect(**kwargs)
# 使用示例：
实例化此类的reader对象，查询promql数据：
reader._client.query(promql, **query_dict)

# DataSource type: 
promtheus
# MetaData:
{self._client.get_all_metrics()}
        """
        return info_prompt

class PromMetricModel(BasePromModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        self.metric = self.model_conf.get('name')

    def connect(self):
        '''
        连通性测试
        '''
        try:
            all_metrics = self._client.get_all_metrics()
            if self.metric in all_metrics:
                return True, '连接成功'
            else:
                return False, '未找到该指标'
        except Exception as e:
            return False, str(e)[:100]

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        res_fields = []
        try:
            pass
        except Exception as e:
            print(e)
        return res_fields

    def get_search_type_list(self):
        '''
        获取可用高级查询类型
        '''
        return []

    def get_extract_rules(self):
        '''
        获取可筛选项
        :return:
        '''
        rules = [{
            'name': '开始时间',
            'value': 'start_time',
            "default": ''
        }, {
            'name': '结束时间',
            'value': 'end_time',
            "default": ''
        }, {
            'name': '步长',
            'value': 'step',
            "default": ''
        }]
        return rules

    def gen_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        try:
            query_dict = {}
            for i in self.extract_rules:
                field = i.get('field')
                rule = i.get('rule')
                value = i.get('value')
                value = trans_rule_value(value)
                if field and value:
                    if rule == 'start_time':
                        start_time = format_date(value, res_type='timestamp')
                        if start_time is not None:
                            query_dict['start_time'] = start_time
                    if rule == 'end_time':
                        end_time = format_date(value, res_type='timestamp')
                        if end_time is not None:
                            query_dict['end_time'] = end_time
                    if rule == 'step':
                        try:
                            query_dict['step'] = float(value)
                        except Exception as e:
                            print(e)
            data_li = self._client.query(self.metric, **query_dict)
            return True, data_li
        except Exception as e:
            return False, str(e)[:500]

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        flag, res_data = self.gen_extract_rules()
        if not flag:
            return False, res_data
        total = len(res_data)
        data_li = res_data[(page - 1) * pagesize:page * pagesize]
        res_data = {
            'records': data_li,
            'total': total
        }
        return True, gen_json_response(data=res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :return:
        '''
        flag, res_data = self.gen_extract_rules()
        if not flag:
            yield False, res_data
        total = len(res_data)
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            result = {
                'records': res_data[(page - 1) * pagesize:page * pagesize],
                'total': total
            }
            yield True, gen_json_response(result)


class PromQlModel(BasePromModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        promql = self.model_conf.get('promql')
        self.promql = promql
        self.default_promql = promql

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        res_fields = []
        try:
            pass
        except Exception as e:
            print(e)
        return res_fields

    def get_search_type_list(self):
        '''
        获取可用高级查询类型
        '''
        return [{
            'name': 'promql',
            'value': 'promql',
            "default": self.promql
        }]

    def get_extract_rules(self):
        '''
        获取可筛选项
        :return:
        '''
        rules = [{
            'name': '开始时间',
            'value': 'start_time',
            "default": ''
        }, {
            'name': '结束时间',
            'value': 'end_time',
            "default": ''
        }, {
            'name': '步长',
            'value': 'step',
            "default": ''
        }]
        return rules

    def gen_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        try:
            rules = [i for i in self.extract_rules if i['field'] == 'search_text' and i['rule'] == 'promql' and i['value']]
            if rules != []:
                self.promql = rules[0].get('value')
            if 'custom_sql' not in self.auth_types and self.promql != self.default_promql:
                return False, '无修改promql权限'
            query_dict = {}
            for i in self.extract_rules:
                field = i.get('field')
                rule = i.get('rule')
                value = i.get('value')
                value = trans_rule_value(value)
                if field and value:
                    if rule == 'start_time':
                        start_time = format_date(value, res_type='timestamp')
                        if start_time is not None:
                            query_dict['start_time'] = start_time
                    if rule == 'end_time':
                        end_time = format_date(value, res_type='timestamp')
                        if end_time is not None:
                            query_dict['end_time'] = end_time
                    if rule == 'step':
                        try:
                            query_dict['step'] = float(value)
                        except Exception as e:
                            print(e)
            data_li = self._client.query(self.promql, **query_dict)
            return True, data_li
        except Exception as e:
            return False, str(e)[:500]

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        flag, res_data = self.gen_extract_rules()
        if not flag:
            return False, res_data
        total = len(res_data)
        data_li = res_data[(page - 1) * pagesize:page * pagesize]
        res_data = {
            'records': data_li,
            'total': total
        }
        return True, gen_json_response(data=res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :return:
        '''
        flag, res_data = self.gen_extract_rules()
        if not flag:
            yield False, res_data
        total = len(res_data)
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            result = {
                'records': res_data[(page - 1) * pagesize:page * pagesize],
                'total': total
            }
            yield True, gen_json_response(result)