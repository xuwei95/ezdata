'''
influxdb
'''
from etl.data_models import DataModel
from etl.libs.ixdb import IxClient
from etl.utils.common_utils import trans_rule_value, gen_json_response


class InfluxDBTableModel(DataModel):
    '''
    InfluxDB 表
    '''
    def __init__(self, model_info):
        super().__init__(model_info)
        conn_conf = self._source['conn_conf']
        model_conf = self._model['model_conf']
        self.table_name = model_conf.get('name')
        self.db_name = conn_conf.get('database')
        self.ix_client = IxClient(**conn_conf)

    def connect(self):
        '''
        连通性测试
        '''
        flag, res = self.read_page(pagesize=1)
        if flag:
            return True, '连接成功'
        else:
            return False, '连接失败'

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及元数据信息
        '''
        result = self.ix_client.query(f'show field keys on "{self.db_name}"."{self.table_name}"')
        field_keys = list(result.get_points())
        result = self.ix_client.query(f'show tag keys on "{self.db_name}"."{self.table_name}"')
        tag_keys = list(result.get_points())
        metadata = {
            'field_keys': field_keys,
            'tag_keys': tag_keys
        }
        info_prompt = f"""
一个influxdb数据表模型类
类中部分参数如下:
table_name: 表名
ix_client._client: python influxdb库的InfluxDBClient
ix_client.query_as_df: 查询sql转为dataframe
# 使用示例：
实例化此类的reader对象，执行sql查询转为dataframe：
sql = 'select * from {self.table_name} limit 10'
df = reader.ix_client.query_as_df(sql)

# DataSource type: 
influxdb
# MetaData:
{metadata}
"""
        return info_prompt

    def delete(self):
        '''
        删除索引
        '''
        try:
            self.ix_client._client.drop_measurement(self.table_name)
            return True, '删除成功'
        except Exception as e:
            return False, str(e)

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        time_dic = {
            'field_name': '时间',
            'field_value': 'time',
            'ext_params': {
                'type': 'time',
            }
        }
        res_fields = [time_dic]
        tags_sql = f'show tag keys on "{self.db_name}" from "{self.table_name}"'
        tags_df = self.ix_client.query_as_df(tags_sql)
        tag_fields = [row['tagKey'] for k, row in tags_df.iterrows()]
        for tag_field in tag_fields:
            dic = {
                'field_name': tag_field,
                'field_value': tag_field,
                'ext_params': {
                    'type': 'tag',
                }
            }
            res_fields.append(dic)
        fields_sql = f'show field keys on "{self.db_name}" from "{self.table_name}"'
        fields_df = self.ix_client.query_as_df(fields_sql)
        field_fields = [row['fieldKey'] for k, row in fields_df.iterrows()]
        for field in field_fields:
            dic = {
                'field_name': field,
                'field_value': field,
                'ext_params': {
                    'type': 'field',
                }
            }
            res_fields.append(dic)
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
            'name': '等于',
            'value': 'equal',
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
            'name': '时间从大到小排序',
            'value': 'sort_desc'
        }, {
            'name': '时间从小到大排序',
            'value': 'sort_asc'
        }
        ]
        return rules

    def gen_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        filter_sql = ""
        condition_list = []
        sort_str = ''
        for i in self.extract_rules:
            field = i.get('field')
            rule = i.get('rule')
            value = i.get('value')
            value = trans_rule_value(value)
            if value:
                if isinstance(value, str):
                    value = f"'{value}'"
                condition_str = ''
                if rule in ['equal', 'eq']:
                    condition_str = f"{field} = {value}"
                elif rule in ['f_equal', 'neq']:
                    condition_str = f"{field} != {value}"
                elif rule == 'gt':
                    condition_str = f"{field} > {value}"
                elif rule == 'lt':
                    condition_str = f"{field} < {value}"
                elif rule == 'gte':
                    condition_str = f"{field} >= {value}"
                elif rule == 'lte':
                    condition_str = f"{field} <= {value}"
                elif rule == 'contain':
                    condition_str = f"{field}=~/.*{value[1:-1] if isinstance(value, str) else value}.*/"
                if condition_str != '':
                    condition_list.append(condition_str)
            else:
                if rule == 'sort_asc':
                    sort_str = 'ORDER BY time asc'
                elif rule == 'sort_desc':
                    sort_str = 'ORDER BY time desc'
        n = 0
        for i in condition_list:
            if n == 0:
                filter_sql += f" where {i}"
            else:
                filter_sql += f" and {i}"
            n += 1
        if sort_str != '':
            filter_sql += f" {sort_str}"
        return True, filter_sql

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        flag, filter_sql = self.gen_extract_rules()
        if not flag:
            res_data = {
                'code': 400,
                'msg': filter_sql
            }
            return False, res_data
        count_sql = f"select count(*) from {self.table_name} {filter_sql}"
        print(count_sql)
        total_df = self.ix_client.query_as_df(count_sql)
        print(total_df)
        total = 0
        for k, row in total_df.iterrows():
            row = row.to_dict()
            for k in row:
                total = int(row[k])
        query_sql = f"select * from {self.table_name} {filter_sql} limit {pagesize} offset {(page - 1) * pagesize}"
        print(query_sql)
        df = self.ix_client.query_as_df(query_sql)
        df.fillna("", inplace=True)
        results = []
        for k, row in df.iterrows():
            dic = row.to_dict()
            results.append(dic)
        res_data = {
            'records': results,
            'total': total
        }
        return True, gen_json_response(res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :return:
        '''
        flag, filter_sql = self.gen_extract_rules()
        if not flag:
            res_data = {
                'code': 400,
                'msg': filter_sql
            }
            return False, res_data
        count_sql = f"select count(*) from {self.table_name} {filter_sql}"
        print(count_sql)
        total_df = self.ix_client.query_as_df(count_sql)
        print(total_df)
        total = 0
        for k, row in total_df.iterrows():
            row = row.to_dict()
            for k in row:
                total = int(row[k])
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            query_sql = f"select * from {self.table_name} {filter_sql} limit {pagesize} offset {(page - 1) * pagesize}"
            print(query_sql)
            df = self.ix_client.query_as_df(query_sql)
            results = []
            for k, row in df.iterrows():
                dic = row.to_dict()
                results.append(dic)
            res_data = {
                'records': results,
                'total': total
            }
            yield True, gen_json_response(res_data)

    def write(self, res_data):
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
            if self.load_type == 'insert':
                insert_records = records
                self.ix_client.write_points(insert_records)
        except Exception as e:
            return False, f'{str(e)[:100]}'
        return True, res_data


class InfluxDBSqlModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        conn_conf = self._source['conn_conf']
        model_conf = self._model.get('model_conf', {})
        self.sql = model_conf.get('sql', 'show measurements')
        self.default_sql = self.sql
        self.auth_types = model_conf.get('auth_type', '').split(',')
        self.ix_client = IxClient(**conn_conf)

    def connect(self):
        '''
        连通性测试
        '''
        try:
            flag, res = self.read_page(pagesize=1)
            if flag:
                return True, '连接成功'
            else:
                return False, '连接失败'
        except Exception as e:
            return False, f'连接失败:{e}'

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及元数据信息
        '''
        df = self.ix_client.query_as_df('show measurements')
        df.fillna("", inplace=True)
        metadata_list = []
        for k, row in df.iterrows():
            table_name = row['name']
            if model_prompt == '' or table_name in model_prompt:
                result = self.ix_client.query(f'show field keys on "{table_name}"')
                field_keys = list(result.get_points())
                result = self.ix_client.query(f'show tag keys on "{table_name}"')
                tag_keys = list(result.get_points())
                metadata = {
                    'table_name': table_name,
                    'field_keys': field_keys,
                    'tag_keys': tag_keys
                }
                metadata_list.append(metadata)
        metadata_info = '\n'.join(metadata_list)
        info_prompt = f"""
一个influxdb sql模型类
类中部分参数如下:
ix_client._client: python influxdb库的InfluxDBClient
ix_client.query_as_df: 查询sql转为dataframe
# 使用示例：
实例化此类的reader对象，执行sql查询转为dataframe：
df = reader.ix_client.query_as_df(sql)

# DataSource type: 
influxdb
# MetaData:
{metadata_info}
"""
        return info_prompt

    def gen_models(self):
        '''
        生成子数据模型
        '''
        df = self.ix_client.query_as_df('show measurements')
        df.fillna("", inplace=True)
        model_list = []
        for k, row in df.iterrows():
            table_name = row['name']
            dic = {
                'type': f'influxdb_table',
                'model_conf': {
                    "name": table_name,
                    "auth_type": "query,edit_fields,extract,load"
                }
            }
            model_list.append(dic)
        return model_list

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        flag, res = self.read_page(pagesize=1)
        if flag and res.get('code') == 200:
            records = res['data']['records']
            if records != []:
                record = records[0]
                fields = []
                for k in record:
                    field_dic = {
                        'field_name': k,
                        'field_value': k,
                        'ext_params': {}
                    }
                    fields.append(field_dic)
                return fields
        return []

    def get_search_type_list(self):
        '''
        获取可用高级查询类型
        '''
        return [{
            'name': 'sql',
            'value': 'sql',
            "default": self.sql
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
        sql_rules = [i for i in self.extract_rules if i['field'] == 'search_text' and i['rule'] == 'sql' and i['value']]
        if sql_rules != []:
            self.sql = sql_rules[0].get('value')

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        self.gen_extract_rules()
        if 'custom_sql' not in self.auth_types and self.sql != self.default_sql:
            return False, '无修改sql权限'
        df = self.ix_client.query_as_df(self.sql)
        df.fillna("", inplace=True)
        results = []
        for k, row in df.iterrows():
            results.append(row.to_dict())
        total = len(results)
        results = results
        res_data = {
            'records': results,
            'total': total,
            'pagination': False  # 禁用分页
        }
        return True, gen_json_response(data=res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :return:
        '''
        self.gen_extract_rules()
        if 'custom_sql' not in self.auth_types and self.sql != self.default_sql:
            return False, '无修改sql权限'
        df = self.ix_client.query_as_df(self.sql)
        df.fillna("", inplace=True)
        results = []
        for k, row in df.iterrows():
            results.append(row.to_dict())
        total = len(results)
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            li = results[(page-1)*pagesize:page*pagesize]
            res_data = {
                'records': li,
                'total': total
            }
            yield True, gen_json_response(data=res_data)

