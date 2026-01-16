import json
from etl.data_models import DataModel
from utils.common_utils import trans_rule_value, gen_json_response, parse_json
import inspect


def get_akshare_functions_options():
    """
    动态获取akshare所有公开函数，生成下拉框选项
    返回格式: [{'label': '函数说明', 'value': '函数名'}, ...]
    """
    try:
        import akshare as ak
        options = []

        # 获取akshare模块的所有成员
        for name, obj in inspect.getmembers(ak):
            # 过滤：只要函数，排除私有函数和内置函数
            if inspect.isfunction(obj) and not name.startswith('_'):
                try:
                    # 获取函数文档的第一行作为描述
                    doc = inspect.getdoc(obj) or ''
                    # 取第一行作为简短描述
                    doc_lines = doc.split('\n')
                    first_line = doc_lines[0].strip() if doc_lines else name

                    # 如果第一行太长，截取前80个字符
                    if len(first_line) > 80:
                        first_line = first_line[:77] + '...'

                    # 如果没有文档，使用函数名作为label
                    label = first_line if first_line else name

                    options.append({
                        'label': f"{label}_{name}" if label != name else name,
                        'value': name
                    })
                except Exception as e:
                    # 如果处理某个函数出错，跳过它
                    continue

        # 按函数名排序
        options.sort(key=lambda x: x['value'])
        return options
    except Exception as e:
        # 如果获取失败，返回空列表
        print(f"获取akshare函数列表失败: {e}")
        return []


class AkShareModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        model_conf = self._model.get('model_conf', {})
        self.method = model_conf.get('method', '')
        self.auth_types = model_conf.get('auth_type', '').split(',')

    @classmethod
    def get_form_config(cls):
        '''
        获取AkShare API模型的配置表单schema
        '''
        # 动态获取akshare函数列表
        akshare_options = get_akshare_functions_options()

        return [
            {
                'label': '数据接口函数',
                'field': 'method',
                'required': True,
                'component': 'JSelectInput',
                'componentProps': {
                    'showSearch': True,
                    'placeholder': '请选择或搜索数据接口函数',
                    'options': akshare_options,
                    'placement': 'bottomLeft',
                    'dropdownStyle': {
                        'position': 'absolute',
                        'zIndex': 999999
                    },
                    'dropdownClassName': 'akshare-select-dropdown',
                }
            },
            {
                'label': '允许操作',
                'field': 'auth_type',
                'component': 'JCheckbox',
                'default': 'query,extract',
                'componentProps': {
                    'options': [
                        {'label': '查询', 'value': 'query'},
                        {'label': '数据抽取', 'value': 'extract'},
                    ]
                }
            }
        ]

    @staticmethod
    def get_connection_args():
        """
        获取连接参数定义
        AkShare是免费开源的财经数据接口，无需连接参数
        """
        return {}

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

if __name__ == '__main__':
    a = get_akshare_functions_options()
    print(a)