'''
es查询接口封装
'''
import requests
from ezetl.libs.es import EsClient
from ezetl.utils.common_utils import parse_json
import re
from urllib import parse
import json
import base64


class EsQueryTool(object):
    '''
    es根据接口字段拼接query查询
    '''
    def __init__(self, params, index_names=[]):
        '''
        初始化参数
        :param params: 查询参数
        :param index_names: 允许查询索引名列表
        '''
        self.params = params
        self.params_lists = []
        for k in self.params:
            self.params_lists.append((k, [self.params[k]]))
        self.page = int(params.get('page', 1))
        self.pagesize = int(params.get('pagesize', 20))
        self.es_host = params.get('host')
        self.es_port = params.get('port')
        self.es_username = params.get('username')
        self.es_password = params.get('password')
        self.api_test = params.get('api_test', 0)
        if index_names == []:
            self.index_name = params.get('index_name', '')
        else:
            index_name = params.get('index_name', '')
            if index_name == '':
                self.index_name = ','.join(index_names)
            else:
                li = index_name.split(',')
                names = [i for i in li if i in index_names]
                self.index_name = ','.join(names)
        self.query_body = {
            'from': (self.page - 1) * self.pagesize,
            'size': self.pagesize,
            'query': {},
            'sort': {},
            'aggs': {},
            'track_total_hits': True  # 获取真实数量，不设置会只返回10000
        }
        self.content_tag = self.params.get('content_tag', '1')
        self.doc_ids = self.parse_doc_ids()
        self.equal_list = self.parse_equal()
        self.f_equal_list = self.parse_f_equal()
        self.contain_list = self.parse_contain()
        self.f_contain_list = self.parse_f_contain()
        self.range_params = self.parse_range()
        self.jl_tag = self.parse_jl_tag()
        self.sort = self.parse_sort()
        self.return_fields = self.parse_return_fields()
        self.search_key = self.parse_search_key()
        self.err_info = None

    def parse_jl_tag(self):
        '''
        解析聚类字段
        jl_tag[coin]=coin_bucket&jl_type[coin_bucket]=terms&jl_size[coin_bucket]=10
        :return:
        '''
        jl_tag = self.params.get('jl_tag', '')
        jl_pagesize_map = {}
        for k, li in self.params_lists:
            if k.startswith('jl_page_size'):
                key = re.findall('\[(.*?)\]', k)
                if key and key != ['']:
                    for i in li:
                        try:
                            jl_pagesize_map[key[0]] = int(i)
                        except Exception as e:
                            print(e)
        jl_type_map = {}
        for k, li in self.params_lists:
            if k.startswith('jl_type'):
                key = re.findall('\[(.*?)\]', k)
                if key and key != ['']:
                    for i in li:
                        jl_type_map[key[0]] = i
        jl_tag_list = []
        if jl_tag != '':
            jl_tag_list = jl_tag.split(',')
            for tag in jl_tag_list:
                pagesize = jl_pagesize_map.get(tag, 20)
                jl_type = jl_type_map.get(tag, 'terms')
                if jl_type == 'terms':
                    self.query_body['aggs'][tag] = {"terms": {"field": tag, "size": pagesize, "shard_size": 1200}}
                elif jl_type in ['max', 'min', 'avg', 'sum', 'stats']:
                    self.query_body['aggs'][tag] = {jl_type: {"field": tag}}
        return jl_tag_list

    def change_search_key(self, tmp_str):
        tmp_str = parse.unquote(str(tmp_str).strip())
        match = re.findall("[A-Za-z0-9\_]+[(](.*?)[)]", tmp_str)
        if match:
            for ii in match:
                if ii[0] == '"' and ii[-1] == '"':
                    tmp_str = tmp_str.replace('(' + ii + ')', ' = ' + ii, 1)
                else:
                    if ii[0] == '"':
                        tmp_str = tmp_str.replace('(' + ii + ')', ' like ' + ii[1:], 1)
                    elif ii[-1] == '"':
                        tmp_str = tmp_str.replace('(' + ii + ')', ' like ' + ii[:-1], 1)
                    else:
                        if ii == '^':
                            tmp_str = tmp_str.replace('(' + ii + ')', ' is not null ', 1)
                        else:
                            tmp_str = tmp_str.replace('(' + ii + ')', ' like ' + ii, 1)
        else:
            if '=' in tmp_str:
                tmp_str = tmp_str.replace('=', ' like ', 1)
            else:
                if tmp_str[0] == '"' and tmp_str[-1] == '"':
                    tmp_str = {"match_phrase": {"_all": {"query": tmp_str}}}
                else:
                    tmp_str = {"multi_match": {"query": tmp_str, "type": "most_fields", "fields": [], "operator": "and",
                                               "tie_breaker": 0.3, "minimum_should_match": "75%", "slop": 1}}
        return tmp_str

    def parse_sql(self, sql):
        '''
        解析sql语句拼接query
        :param sql:
        :return:
        '''
        try:
            if 'where' not in sql:
                sql = f'select * from {self.index_name} where {sql}'
            headers = {
                'Content-Type': 'application/json'
            }
            if self.es_username != '':
                headers['Authorization'] = f'Basic {base64.b64encode(f"{self.es_username}:{self.es_password}".encode()).decode()}'
            req_data = {
                'sql': sql
            }
            url = f'http://{self.es_host}:{str(self.es_port)}/_nlpcn/sql/explain'
            res = requests.post(url, headers=headers, json=req_data)
            res = json.loads(res.text)
            if 'error' in res:
                return True, res['error']

            if 'bool' not in self.query_body['query']:
                self.query_body['query']['bool'] = {}
            if 'must' not in self.query_body['query']['bool']:
                self.query_body['query']['bool']['must'] = []
            if 'bool' in res['query'] and 'filter' in res['query']['bool']:
                self.query_body['query']['bool']['must'].extend(res['query']['bool']['filter'])
            return False, res
        except Exception as e:
            return True, str(e)

    def parse_search_key(self):
        '''
        解析search_key参数
        :return:
        '''
        search_key = self.params.get('search_key', '')
        if search_key:
            if search_key.startswith('sql:'):  # 以sql: 开头的解析sql语句
                err, err_info = self.parse_sql(search_key[4:])
                if err:
                    self.err_info = err_info
            elif search_key.startswith('query_body:'):  # 以query_body: 开头的,将查询体设为设置的查询
                query_body = self.parse_sql(search_key[11:])
                query_body = parse_json(query_body)
                if isinstance(query_body, dict):
                    if "query" in query_body:
                        self.query_body["query"] = query_body["query"]
                    if "aggs" in query_body:
                        self.query_body["aggs"] = query_body["aggs"]
            else:
                tmp_str = self.change_search_key(search_key)
                if isinstance(tmp_str, dict):
                    if 'bool' not in self.query_body['query']:
                        self.query_body['query']['bool'] = {}
                    if 'must' not in self.query_body['query']['bool']:
                        self.query_body['query']['bool']['must'] = []
                    self.query_body['query']['bool']['must'].append(tmp_str)
                else:
                    sql = f'select * from {self.index_name} where {tmp_str}'
                    err, err_info = self.parse_sql(sql)
                    if err:
                        self.err_info = err_info
        return search_key

    def parse_equal(self):
        '''
        解析equal参数, 根据聚类字段值筛选数据。
        普通字段 equal[key]=value => obj.key == value
        嵌套字段 equal[key1][key2] => obj.key1.key2 == value
        例：equal[PY][]=2000,2001，取PY为2000或者2001的数据
        :return:
        '''
        equal_list = []
        for k, li in self.params_lists:
            if k.startswith('equal'):
                key = re.findall('\[(.*?)\]', k)
                if key != ['']:
                    for i in li:
                        equal_list.append({'key': key, 'value': i.split(',')})
        if equal_list != []:
            if 'bool' not in self.query_body['query']:
                self.query_body['query']['bool'] = {}
            if 'filter' not in self.query_body['query']['bool']:
                self.query_body['query']['bool']['filter'] = []
            for equal in equal_list:
                if len(equal['key']) == 1 or len(equal['key']) == 2 and equal['key'][1] == '':  # 普通字段
                    terms = {'terms': {equal['key'][0]: equal['value']}}
                else:  # 嵌套字段
                    key1 = equal['key'][0]
                    key2 = equal['key'][1]
                    terms = {"nested": {"path": f"{key1}", "query": {
                        "bool": {"filter": [{"terms": {f"{key1}.{key2}": equal['value']}}]}}}}
                self.query_body['query']['bool']['filter'].append(terms)
        return equal_list

    def parse_f_equal(self):
        '''
        解析f_equal参数，用于排除不需要的数据
        普通字段 f_equal[key]=value => obj.key != value
        嵌套字段 f_equal[key1][key2]=value => obj.key1.key2 != value
        f_equal[PY][]=2000&f_equal[PY][]=2001或f_equal[PY][]=2000,2001  取PY不等于2000且不等于2001的数据
        :return:
        '''
        f_equal_list = []
        for k, li in self.params_lists:
            if k.startswith('f_equal'):
                key = re.findall('\[(.*?)\]', k)
                if key != ['']:
                    for i in li:
                        f_equal_list.append({'key': key, 'value': i.split(',')})
        if f_equal_list != []:
            if 'bool' not in self.query_body['query']:
                self.query_body['query']['bool'] = {}
            if 'must_not' not in self.query_body['query']['bool']:
                self.query_body['query']['bool']['must_not'] = []
            for f_equal in f_equal_list:
                if len(f_equal['key']) == 1 or len(f_equal['key']) == 2 and f_equal['key'][1] == '':  # 普通字段
                    terms = {'terms': {f_equal['key'][0]: f_equal['value']}}
                else:  # 嵌套字段
                    key1 = f_equal['key'][0]
                    key2 = f_equal['key'][1]
                    terms = {"nested": {"path": f"{key1}", "query": {
                        "bool": {"must": [{"terms": {f"{key1}.{key2}": f_equal['value']}}]}}}}
                self.query_body['query']['bool']['must_not'].append(terms)
        return f_equal_list

    def parse_contain(self):
        '''
        解析contain参数, 查询包含条件。
        普通字段 contain[key]=value => obj.key like value
        嵌套字段 contain[key1][key2] => obj.key1.key2 like value
        例：contain[TITLE][]= beijing 取TITLE中包含beijing的数据
        :return:
        '''
        contain_list = []
        for k, li in self.params_lists:
            if k.startswith('contain'):
                key = re.findall('\[(.*?)\]', k)
                if key != ['']:
                    for i in li:
                        contain_list.append({'key': key, 'value': i})
        if contain_list != []:
            if 'bool' not in self.query_body['query']:
                self.query_body['query']['bool'] = {}
            if 'must' not in self.query_body['query']['bool']:
                self.query_body['query']['bool']['must'] = []
            for contain in contain_list:
                if len(contain['key']) == 1 or len(contain['key']) == 2 and contain['key'][1] == '':  # 普通字段
                    terms = {'match_phrase': {contain['key'][0]: contain['value']}}
                else:  # 嵌套字段
                    key1 = contain['key'][0]
                    key2 = contain['key'][1]
                    terms = {"nested": {"path": f"{key1}", "query": {
                        "bool": {"must": [{"match_phrase": {f"{key1}.{key2}": [contain['value']]}}]}}}}
                self.query_body['query']['bool']['must'].append(terms)
        return contain_list

    def parse_f_contain(self):
        '''
        解析f_contain参数, 查询不包含条件。
        普通字段 f_contain[key]=value => obj.key like value
        嵌套字段 f_contain[key1][key2] => obj.key1.key2 like value
        例：f_contain[TITLE][]= beijing 取TITLE中不包含beijing的数据
        :return:
        '''
        contain_list = []
        for k, li in self.params_lists:
            if k.startswith('f_contain'):
                key = re.findall('\[(.*?)\]', k)
                if key != ['']:
                    for i in li:
                        contain_list.append({'key': key, 'value': i})
        if contain_list != []:
            if 'bool' not in self.query_body['query']:
                self.query_body['query']['bool'] = {}
            if 'must_not' not in self.query_body['query']['bool']:
                self.query_body['query']['bool']['must_not'] = []
            for contain in contain_list:
                if len(contain['key']) == 1 or len(contain['key']) == 2 and contain['key'][1] == '':  # 普通字段
                    terms = {'match_phrase': {contain['key'][0]: contain['value']}}
                else:  # 嵌套字段
                    key1 = contain['key'][0]
                    key2 = contain['key'][1]
                    terms = {"nested": {"path": f"{key1}", "query": {
                        "bool": {"must": [{"match_phrase": {f"{key1}.{key2}": [contain['value']]}}]}}}}
                self.query_body['query']['bool']['must_not'].append(terms)
        return contain_list

    def parse_range(self):
        '''
        解析range参数, gt, gte,lt, lte
        例：gt[PY]=2000&lt[PY]=2010表示取PY（2001~2009）,
        包含起始；一个参数 gte[PY]=2000表示PY大于等于2010
        :return:
        '''
        range_map = {}
        for k, li in self.params_lists:
            if k.startswith(('gt', 'gte', 'lt', 'lte')):
                key = re.findall('\[(.*?)\]', k)
                rule = k.split('[')[0]
                if key != [''] and len(li) == 1:
                    key = str(key)
                    if key not in range_map:
                        range_map[key] = {rule: li[0]}
                    else:
                        range_map[key][rule] = li[0]
        if range_map != {}:
            if 'bool' not in self.query_body['query']:
                self.query_body['query']['bool'] = {}
            if 'filter' not in self.query_body['query']['bool']:
                self.query_body['query']['bool']['filter'] = []
            for key, value in range_map.items():
                key = eval(key)
                for k in value:
                    value[k] = value[k]
                if len(key) == 1 or len(key) == 2 and key[1] == '':  # 普通字段
                    terms = {'range': {key[0]: [value]}}
                else:  # 嵌套字段
                    key1 = key[0]
                    key2 = key[1]
                    terms = {"nested": {"path": f"{key1}", "query": {
                        "bool": {"must": [{"range": {f"{key1}.{key2}": [value]}}]}}}}
                self.query_body['query']['bool']['filter'].append(terms)
        return range_map

    def parse_doc_ids(self):
        '''
        解析doc_ids参数, 根据唯一id获取内容，eg：1,2,3多个以逗号连接
        例：doc_ids=1,2,3表示取_id=1或2或3的值
        :return:
        '''
        doc_ids = self.params.get('doc_ids', '')
        if doc_ids != '':
            doc_ids = doc_ids.split(',')
            if 'bool' not in self.query_body['query']:
                self.query_body['query']['bool'] = {}
            if 'filter' not in self.query_body['query']['bool']:
                self.query_body['query']['bool']['filter'] = []
            terms = {'terms': {"_id": doc_ids}}
            self.query_body['query']['bool']['filter'].append(terms)
            return doc_ids
        else:
            return []

    def parse_return_fields(self):
        '''
        解析return_fields参数, 根据筛选返回字段。
        :return:
        '''
        return_fields = self.params.get('return_fields', '')
        if return_fields != '':
            return_fields = return_fields.split(',')
            self.query_body["_source"] = {
                "includes": return_fields
            }
        else:
            return_fields = []
        return return_fields

    def parse_sort(self):
        '''
        解析sort参数, 内容排序，eg:PY DESC,id ASC
        例：sort=PY DESC或sort=PY+DESC或sort[PY]=DESC 表示按PY从大到小排序，
        sort=id ASC或sort=id+ASC或sort[id]=ASC 表示按id从小到大排序
        :return:
        '''
        sort_list = []
        for k, li in self.params_lists:
            if k == 'sort':
                for i in li:
                    if '+' in i:
                        v = i.split('+')
                    else:
                        v = i.split(' ')
                    if len(v) == 2:
                        key, value = v
                        value = value.upper()
                        if value in ['DESC', 'ASC']:
                            sort_list.append({'key': key, 'value': value})
            if k.startswith('sort['):
                key = re.findall('\[(.*?)\]', k)
                if key != [''] and len(li) == 1:
                    key = key[0]
                    value = li[0].upper()
                    if value in ['DESC', 'ASC']:
                        sort_list.append({'key': key, 'value': value})
        for sort in sort_list:
            if sort['key'] not in self.query_body['sort']:
                self.query_body['sort'][sort['key']] = {"order": sort['value']}
        return sort_list

    def valid_params(self):
        '''
        检测各参数合法性
        :return:
        '''
        if self.page < 1:
            return {
                'code': 400,
                'msg': '页数不能小于1'
            }
        if self.index_name == '':
            return {
                'code': 400,
                'msg': '待查索引为空'
            }
        return False

    def gen_contents(self, data_li, valid_fields=['*']):
        '''
        根据content_tag类型组合返回内容
        '''
        content_tag = str(self.content_tag)
        if content_tag == '0':
            contents = []
        elif content_tag == '1':
            contents = []
            for i in data_li:
                if '*' not in valid_fields:
                    i['_source'] = {k: v for k, v in i['_source'].items() if k in valid_fields}
                if 'highlight' in i:
                    i['_source']['_highlight'] = i['highlight']
                dic = {
                    '_id': i['_id'],
                    '_index': i['_index'],
                    '_score': i['_score'],
                    '_type': i['_type'],
                    **i['_source']
                }
                contents.append(dic)
        elif content_tag == '2':
            contents = {}
            for i in data_li:
                if '*' not in valid_fields:
                    i['_source'] = {k: v for k, v in i['_source'].items() if k in valid_fields}
                if 'highlight' in i:
                    i['_source']['_highlight'] = i['highlight']
                source_dict = i['_source']
                for k, v in source_dict.items():
                    if k not in contents:
                        contents[k] = [v]
                    else:
                        contents[k].append(v)
        else:
            contents = []
            for i in data_li:
                if '*' not in valid_fields:
                    i['_source'] = {k: v for k, v in i['_source'].items() if k in valid_fields}
                if 'highlight' in i:
                    i['_source']['_highlight'] = i['highlight']
                contents.append(i)
        return contents

    def gen_result(self, result, valid_fields=['*']):
        '''
        组合返回结果
        :return:
        '''
        print(result)
        total = result['hits']['total']['value']
        data_li = result['hits']['hits']
        contents = self.gen_contents(data_li, valid_fields)
        aggregations = result.get('aggregations', {})
        if self.api_test != 0:
            res_data = {
                'data': {
                    'query_body': self.query_body,
                    'result': result,
                    'total': total,
                },
                'code': 200,
                'msg': '查询成功'
            }
        else:
            res_data = {
                'code': 200,
                'msg': '查询成功',
                'data': {
                    'records': contents,
                    'aggs': aggregations,
                    'total': total
                },
            }
        return res_data

    def query(self, valid_fields=['*'], es=None):
        '''
        执行查询返回结果
        :return:
        '''
        not_valid = self.valid_params()
        if not_valid:
            return not_valid
        if self.err_info:
            res_data = {
                'code': 400,
                'msg': '查询错误',
                'err_info': self.err_info
            }
            return res_data
        if self.query_body['query'] == {}:
            self.query_body['query'] = {'match_all': {}}
        try:
            if es is None:
                es_hosts = [{'host': self.es_host, 'port': self.es_port}]
                es = EsClient(hosts=es_hosts, http_auth=(self.es_username, self.es_password))
            print(self.query_body)
            result = es.query_all(self.index_name, self.query_body)
            res_data = self.gen_result(result, valid_fields)
            return res_data
        except Exception as e:
            print(e)
            return {
                'code': 400,
                'msg': f'接口错误{str(e)}'
            }


if __name__ == '__main__':
    params = {
        'page': 1,
        'pagesize': 20,
        'index_name': 'test',
        'gte[PY]': 2020,
        'lt[PY]': 2022,
        'equal[name]': '张三',
        'sort[PY]': 'ASC',
        'search_key': 'sql:select * from datacenter_logs where ip_raw is null'
    }
    es_tool = EsQueryTool(params=params)
    print(es_tool.query_body)
