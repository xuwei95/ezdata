from ezetl.libs.es import EsClient
from ezetl.data_models import DataModel
from ezetl.utils.common_utils import trans_rule_value, parse_json
from ezetl.utils.es_utils import get_index_mapping
from ezetl.utils.es_query_tool import EsQueryTool


class EsIndexModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        model_conf = self._model.get('model_conf', {})
        self.index_name = model_conf.get('name', '')
        self.auth_types = model_conf.get('auth_type', '').split(',')
        conn_conf = self._source['conn_conf']
        url = conn_conf.get('url')
        es_hosts = url.split(',')
        es_conf = {
            'hosts': es_hosts
        }
        auth_type = conn_conf.get('auth_type', 1)
        if auth_type == 2:
            # 用户名密码验证
            username = conn_conf.get('username')
            password = conn_conf.get('password')
            es_conf['http_auth'] = (username, password)
        self.es_client = EsClient(**es_conf)

    def connect(self):
        '''
        连通性测试
        '''
        try:
            mapping = self.es_client.get_mapping(self.index_name)
            if self.index_name != '':
                if self.index_name in mapping:
                    return True, '连接成功'
                else:
                    return False, '连接失败'
            else:
                return True, '连接成功'
        except Exception as e:
            return False, str(e)[:100]

    def query(self, index_name, query, limit=10000):
        '''
        查询数据
        '''
        if 'size' not in query:
            query['size'] = limit
        res = self.es_client._client.search(index=index_name, body=query)
        return res

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及数据库元数据信息
        '''
        mapping = self.es_client.get_mapping(self.index_name)
        query_example = {'query': {'match_all': {}}, 'size': 10000}
        info_prompt = f"""
一个elasticsearch封装类，并且提供了一些数据操作的方法
# 使用示例：
实例化此类的reader对象，查询数据转为dataframe：
query_dict = {query_example}
res = reader.query(index_name='test_index', query=query_dict)
data_li = [i.get('_source') for i in res['hits'].get('hits')]
df = pd.DataFrame(data_li)

# DataSource type: 
elasticsearch
# MetaData:
{mapping}
        """
        return info_prompt

    def gen_models(self):
        '''
        生成子数据模型
        '''
        mapping = self.es_client.get_mapping(self.index_name)
        model_list = []
        for index in mapping:
            dic = {
                'type': f'elasticsearch_index',
                'model_conf': {
                    "name": index,
                    "auth_type": "query,create,edit_fields,delete,extract,load"
                }
            }
            model_list.append(dic)
        return model_list

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        try:
            mapping = get_index_mapping(self.index_name, self.es_client)
            field_dict = mapping[self.index_name]['mappings']['properties']
            res_fields = []
            for field_value in field_dict:
                field = field_dict[field_value]
                field_type = field.get('type')
                dic = {
                    'field_name': field_value,
                    'field_value': field_value,
                    'ext_params': {
                        'type': field_type,
                        'length': 0,
                        'is_primary_key': 0,
                        'nullable': 1,
                        'default': ''
                    }
                }
                res_fields.append(dic)
            return res_fields
        except Exception as e:
            print(e)
            return []

    def check_field(self, field_info, res_fields):
        '''
        检察字段是否存在且一致
        '''
        for field in res_fields:
            if field['field_value'] == field_info['field_value'] and field['type'] == field_info['type']:
                print(field_info, field)
                return True
        return False

    def set_field(self, field):
        '''
        设置字段
        '''
        if 'edit_fields' not in self.auth_types:
            return False, '无操作字段权限'
        mapping = {}
        mapping['properties'] = {}
        mapping['properties'][field['field_value']] = {}
        mapping['properties'][field['field_value']]['type'] = field['type']
        if field['type'] == 'text':
            mapping['properties'][field['field_value']]['fields'] = {
                'keyword': {'type': 'keyword', 'ignore_above': 256}}
        try:
            self.es_client.create_mapping(self.index_name, mapping)
            return True, '操作成功'
        except Exception as e:
            print(e)
            return False, str(e)[:100]

    def create(self, field_arr):
        '''
        创建索引
        '''
        if 'create' not in self.auth_types:
            return False, '无创建权限'
        mapping = {}
        mapping['properties'] = {}
        for field in field_arr:
            mapping['properties'][field['field_value']] = {}
            mapping['properties'][field['field_value']]['type'] = field['type']
            if field['type'] == 'text':
                mapping['properties'][field['field_value']]['fields'] = {'keyword': {'type': 'keyword', 'ignore_above': 256}}
        try:
            self.es_client.create_mapping(self.index_name, mapping)
            ext_params = parse_json(self._model.get('ext_params'), {})
            max_result_window = ext_params.get('max_result_window', 10000000)
            self.es_client.put_settings(self.index_name, {'refresh_interval': "1s", "max_result_window": str(max_result_window)})
            return True, '创建成功'
        except Exception as e:
            return False, str(e)

    def delete(self):
        '''
        删除索引
        '''
        if 'delete' not in self.auth_types:
            return False, '无删除权限'
        try:
            self.es_client.delete_index(self.index_name)
            return True, '删除成功'
        except Exception as e:
            return False, str(e)

    def get_search_type_list(self):
        '''
        获取可用高级查询类型
        '''
        return [{
            'name': '关键词',
            'value': 'search_key',
            "default": f""
        }, {
            'name': 'sql',
            'value': 'sql',
            "default": f"select * from {self.index_name}"
        }, {
            'name': '原生查询',
            'value': 'query_body',
            "default": '{\n    \"query\": {},\n    \"aggs\": {}\n}'
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
            'name': '包含',
            'value': 'contain'
        }, {
            'name': '不包含',
            'value': 'f_contain'
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
        }, {
            'name': '从大到小排序',
            'value': 'sort_desc'
        }, {
            'name': '从小到大排序',
            'value': 'sort_asc'
        }, {
            'name': '统计数量',
            'value': 'jl_terms'
        }, {
            'name': '统计数量页数',
            'value': 'jl_page_size'
        }, {
            'name': '聚合统计',
            'value': 'jl_stats'
        }, {
            'name': '统计总和',
            'value': 'jl_sum'
        }, {
            'name': '统计平均值',
            'value': 'jl_avg'
        }, {
            'name': '统计最小值',
            'value': 'jl_min'
        }, {
            'name': '统计最大值',
            'value': 'jl_max'
        }, {
            'name': '返回字段列表',
            'value': 'return_fields'
        }, {
            'name': '唯一号列表筛选',
            'value': 'doc_ids'
        }, {
            'name': '返回内容',
            'value': 'content_tag'
        }
        ]
        return rules

    def gen_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        api_form = {}
        jl_tag = []
        for i in self.extract_rules:
            field = i.get('field')
            rule = i.get('rule')
            value = i.get('value')
            value = trans_rule_value(value)
            if rule in ['equal', 'eq']:
                api_form[f'equal[{field}]'] = value
            elif rule in ['f_equal', 'neq']:
                api_form[f'f_equal[{field}]'] = value
            elif rule in ['gt', 'gte', 'lt', 'lte', 'contain', 'f_contain', 'jl_page_size']:
                api_form[f'{rule}[{field}]'] = value
            elif rule in ['return_fields', 'doc_ids', 'search_key']:
                api_form[rule] = value
            elif rule == 'sort':
                if field:
                    api_form[f'sort[{field}]'] = value
                else:
                    api_form[f'sort'] = value
            elif rule == 'sort_asc':
                api_form[f'sort[{field}]'] = 'ASC'
            elif rule == 'sort_desc':
                api_form[f'sort[{field}]'] = 'DESC'
            elif rule in ['jl_terms', 'jl_sum', 'jl_avg', 'jl_max', 'jl_min', 'jl_stats']:
                api_form[f'jl_type[{field}]'] = rule.split('_')[-1]
                jl_tag.append(field)
            elif rule == 'content_tag':
                api_form['content_tag'] = value
            elif rule == 'jl_tag':
                jl_tag.extend(value.split(','))
            elif rule == 'jl_type':
                api_form[f'jl_type[{field}]'] = value
                jl_tag.append(field)
            elif rule == 'search_text':
                if field == 'sql':
                    api_form['search_key'] = f"sql:{value}"
                elif field == 'search_key':
                    api_form['search_key'] = value
                elif field == 'query_body':
                    api_form['search_key'] = f"query_body:{value}"
        if jl_tag != []:
            api_form['jl_tag'] = ','.join(list(set(jl_tag)))
        return api_form

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        api_form = self.gen_extract_rules()
        api_form['index_name'] = self.index_name
        api_form['page'] = page
        api_form['pagesize'] = pagesize
        es_tools = EsQueryTool(api_form)
        res_data = es_tools.query(es=self.es_client)
        return True, res_data

    def read_batch(self):
        '''
        生成器分批读取数据
        :return:
        '''
        api_form = self.gen_extract_rules()
        api_form['index_name'] = self.index_name
        # scroll 获取数据
        es_tools = EsQueryTool(api_form)
        query_body = es_tools.query_body
        if query_body['query'] == {}:
            query_body['query'] = {'match_all': {}}
        query_body['size'] = self._extract_info.get('batch_size', 1000)
        result = self.es_client.scroll_search(self.index_name, query_body)
        sid = result['_scroll_id']
        scroll_size = result['hits']['total']['value']
        while scroll_size > 0:
            res_data = es_tools.gen_result(result)
            yield True, res_data
            result = self.es_client.scroll(sid)
            sid = result['_scroll_id']
            if res_data['data']['records'] == []:
                break

    def write(self, res_data):
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert', 'update', 'upsert']:
            return False, '写入类型参数错误'
        records = []
        if isinstance(res_data, list) and res_data != []:
            records = res_data
        if isinstance(res_data, dict):
            if 'records' in res_data and res_data['records'] != []:
                records = res_data['records']
            else:
                records = [res_data]
        try:
            if self.load_type == 'insert':
                self.es_client.add_data_bulk(self.index_name, records)
            elif self.load_type == 'update':
                self.es_client.update_data_bulk(self.index_name, records)
            elif self.load_type == 'upsert':
                self.es_client.update_data_bulk(self.index_name, records, upsert=True)
        except Exception as e:
            return False, f'{str(e)[:-100]}'
        return True, records
