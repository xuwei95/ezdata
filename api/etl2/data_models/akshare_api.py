import json
from etl2.data_models import DataModel
from utils.common_utils import trans_rule_value, gen_json_response, parse_json
import inspect


class AkShareModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        model_conf = self._model.get('model_conf', {})
        self.method = model_conf.get('method', '')
        self.auth_types = model_conf.get('auth_type', '').split(',')

    def connect(self):
        '''
        连通性测试
        '''
        try:
            import akshare as ak
            if self.method != '':
                self.fetch_function = getattr(ak, self.method)
                sig = inspect.signature(self.fetch_function)
                params = sig.parameters
                default_parmas = {}
                for name, param in params.items():
                    default_parmas[name] = param.default
                self.func_params = default_parmas
            return True, '连接成功'
        except Exception as e:
            return False, str(e)

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及数据库元数据信息
        '''
        self.connect()
        info_prompt = f"""
一个基于 akshare财经数据接口的封装类
# 使用示例：
实例化此类的reader对象，执行函数，读取结果转为dataframe
query_params = {self.func_params}
df = reader.fetch_function(**query_params)

# MetaData:
fetch_function doc
{self.fetch_function.__doc__}

        """
        return info_prompt

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        flag, res_data = self.gen_extract_rules()
        if not flag:
            assert ValueError(res_data)
        res_fields = []
        try:
            for column in self.df.columns:
                dic = {
                    'field_name': column,
                    'field_value': column,
                }
                res_fields.append(dic)
        except Exception as e:
            print(e)
        return res_fields

    def get_search_type_list(self):
        '''
        获取可用高级查询类型
        '''
        flag, _ = self.connect()
        if not flag:
            return []
        return [{
            'name': '查询参数',
            'value': 'query_params',
            "default": json.dumps(self.func_params, ensure_ascii=False, indent=2)
        }]

    def get_extract_rules(self):
        '''
        获取可筛选项
        :return:
        '''
        rules = [{
            'name': '等于',
            'value': 'equal'
          }, {
            'name': '不等于',
            'value': 'f_equal'
          }, {
            'name': '大于',
            'value': 'gt'
          }, {
            'name': '大于等于',
            'value': 'gte'
          }, {
            'name': '小于',
            'value': 'lt'
          }, {
            'name': '小于等于',
            'value': 'lte'
          }
        ]
        return rules

    def gen_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        # 若查询参数中有函数参数，替换函数参数
        params_rules = [i for i in self.extract_rules if i['field'] == 'search_text' and i['rule'] == 'query_params' and i['value']]
        if params_rules != []:
            self.func_params = parse_json(params_rules[0].get('value'), self.func_params)
        # 若请求参数中有函数参数，替换函数参数
        ext_query_params = [i for i in self.extract_rules if i['field'] in self.func_params and i['value']]
        if ext_query_params != []:
            for i in ext_query_params:
                self.func_params[i['field']] = i['value']
        query_params = {}
        for k in self.func_params:
            query_params[k] = trans_rule_value(self.func_params[k])
        try:
            self.df = self.fetch_function(**query_params)
        except Exception as e:
            return False, str(e)
        for i in self.extract_rules:
            field = i.get('field')
            rule = i.get('rule')
            value = i.get('value')
            value = trans_rule_value(value)
            if field and value:
                if rule in ['equal', 'eq']:
                    self.df = self.df[self.df[field] == value]
                elif rule in ['f_equal', 'neq']:
                    self.df = self.df[self.df[field] != value]
                elif rule == 'gt':
                    self.df = self.df[self.df[field] > value]
                elif rule == 'gte':
                    self.df = self.df[self.df[field] >= value]
                elif rule == 'lt':
                    self.df = self.df[self.df[field] < value]
                elif rule == 'lte':
                    self.df = self.df[self.df[field] <= value]
        self.df.fillna("", inplace=True)
        data_li = []
        for k, row in self.df.iterrows():
            data_li.append(row.to_dict())
        return True, data_li

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        flag, res_data = self.connect()
        if not flag:
            return False, res_data
        flag, res_data = self.gen_extract_rules()
        if not flag:
            return False, res_data
        total = len(res_data)
        data_li = res_data
        res_data = {
            'records': data_li,
            'total': total,
            'pagination': False  # 禁用分页
        }
        return True, gen_json_response(data=res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :param res_type: 返回形式
        :return:
        '''
        flag, res_data = self.connect()
        if not flag:
            return False, res_data
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
                'records': res_data[(page-1)*pagesize:page*pagesize],
                'total': total
            }
            yield True, gen_json_response(result)
