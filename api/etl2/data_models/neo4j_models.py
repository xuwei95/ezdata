from py2neo import NodeMatcher, RelationshipMatcher
from etl.data_models import DataModel
from etl.utils.common_utils import trans_rule_value, flatten_dict, gen_json_response
from etl.libs.n4j import NjClient


class N4jGraphModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        conn_conf = self._source['conn_conf']
        model_conf = self._model['model_conf']
        self.label = model_conf.get('name')
        n4j_url = f"http://{conn_conf.get('host')}:{conn_conf.get('port')}"
        self.n4j_client = NjClient(n4j_url, **{'username': conn_conf.get('username'), 'password': conn_conf.get('password')})
        self.node_matcher = NodeMatcher(self.n4j_client._client)
        self.relation_matcher = RelationshipMatcher(self.n4j_client._client)

    def connect(self):
        '''
        连通性测试
        '''
        if self.read_page(pagesize=1):
            return True, '连接成功'
        else:
            return False, '连接失败'

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及数据库元数据信息
        '''
        # 获取数据库元数据
        graph = self.n4j_client._client
        # 节点列表
        node_labels = graph.schema.node_labels
        # 关系列表
        relationships = graph.schema.relationship_types
        metadata_info = f"""
Node labels: {list(node_labels)}
Relationship types: {list(relationships)}
        """
        for label in node_labels:
            if model_prompt == '' or label in model_prompt or self.label == label:
                # 获取每个标签的第一个节点进行示例，并获取与该节点有关的关系信息
                query = f"""
                MATCH (n:{label})
                WITH n LIMIT 1
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN properties(n) AS node_properties, type(r) AS relationship_type, properties(r) AS relationship_properties, m as related_node_demo, labels(m) AS related_node_labels
                """
                result = graph.run(query)
                metadata_info += f'\n\n {label} node demo：\n {result}'
        info_prompt = f"""
一个py2neo 封装类，并且提供了一些数据操作的方法
类中部分参数如下:
n4j_client._client：py2neo Graph实例
# 使用示例：
实例化此类的reader对象，查询数据转为dataframe：
query = "MATCH (p:Person) RETURN p.name"
# 执行查询并将结果转换为Dataframe
result = reader.n4j_client._client.run(query).to_data_frame()

# DataSource type:
neo4j
# MetaData:
{metadata_info}
        """
        return info_prompt

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

    def delete(self):
        '''
        删除
        '''
        try:
            del_sql = f'MATCH (n:{self.label}) detach delete n '
            results = self.n4j_client.query(del_sql)
            return True, '删除成功'
        except Exception as e:
            return False, str(e)

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        return None

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
            'value': 'eq'
          }, {
            'name': '不等于',
            'value': 'neq'
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
          }
        ]
        return rules

    def gen_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        query = self.node_matcher.match(self.label)
        for i in self.extract_rules:
            field = i.get('field')
            rule = i.get('rule')
            value = i.get('value')
            value = trans_rule_value(value)
            if field and field not in ['sql']:
                if value:
                    if isinstance(value, str):
                        value = f"'{value}'"
                    if rule in ['eq']:
                        query = query.where(f"_.{field} = {value}")
                    elif rule in ['neq']:
                        query = query.where(f"NOT _.{field} = {value}")
                    elif rule == 'gt':
                        query = query.where(f"_.{field} > {value}")
                    elif rule == 'lt':
                        query = query.where(f"_.{field} < {value}")
                    elif rule == 'gte':
                        query = query.where(f"_.{field} >= {value}")
                    elif rule == 'lte':
                        query = query.where(f"_.{field} <= {value}")
                    elif rule in ['contain', 'not_contain']:
                        if isinstance(value, str):
                            value = f"'.*{value[1:-1]}.*'"
                        else:
                            value = f"'.*{value}.*'"
                        query = query.where(f"{'NOT ' if rule == 'not_contain' else ''}_.{field} =~ {value}")
        return True, query

    def trans_obj_to_dict(self, obj):
        '''
        将结果转为字典类型
        '''
        dic = {
            'type': 'node',
            'identity': obj.identity,
            'labels': [],
            "properties": {}
        }
        if obj.labels is not None:
            for la in obj.labels:
                dic["labels"].append(la)
        for k, v in obj.items():
            dic["properties"][k] = v
        return dic

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        if self.n4j_client is False:
            return False, '数据库链接错误'
        flag, query = self.gen_extract_rules()
        if not flag:
            return False, query
        total = query.count()
        query = query.skip((page-1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        data_li = []
        for obj in obj_list:
            dic = self.trans_obj_to_dict(obj)
            # 将参数带入字典
            dic = flatten_dict(dic, 'properties')
            data_li.append(dic)
        res_data = {
            'records': data_li,
            'total': total
        }
        return True, gen_json_response(res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :return:
        '''
        if self.n4j_client is False:
            yield False, '数据库链接错误'
        flag, query = self.gen_extract_rules()
        if not flag:
            yield False, query
        total = query.count()
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            query = query.skip((page - 1) * pagesize)
            query = query.limit(pagesize)
            obj_list = query.all()
            data_li = []
            for obj in obj_list:
                dic = self.trans_obj_to_dict(obj)
                # 将参数带入字典
                dic = flatten_dict(dic, 'properties')
                data_li.append(dic)
            res_data = {
                'records': data_li,
                'total': total
            }
            yield True, gen_json_response(res_data)

    def write(self, res_data):
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert', 'update', 'upsert']:
            return False, '写入类型参数错误'
        self.only_fields = self._load_info.get('only_fields', [])
        records = []
        if isinstance(res_data, list) and res_data != []:
            records = res_data
        if isinstance(res_data, dict):
            if 'records' in res_data and res_data['records'] != []:
                records = res_data['records']
            else:
                records = [res_data]
        try:
            insert_records = []
            if self.load_type == 'insert':
                insert_records = records
            if insert_records != []:
                for record in records:
                    self.n4j_client.create_node([self.label], record)
        except Exception as e:
            return False, f'{str(e)[:100]}'
        return True, res_data


class N4jSqlModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        conn_conf = self._source.get('conn_conf')
        model_conf = self._model.get('model_conf', {})
        self.sql = model_conf.get('sql', 'CALL db.labels()')
        self.default_sql = self.sql
        self.auth_types = model_conf.get('auth_type', '').split(',')
        n4j_url = f"http://{conn_conf.get('host')}:{conn_conf.get('port')}"
        self.n4j_client = NjClient(n4j_url,
                                   **{'username': conn_conf.get('username'), 'password': conn_conf.get('password')})

    def connect(self):
        '''
        连通性测试
        '''
        if self.read_page(pagesize=1):
            return True, '连接成功'
        else:
            return False, f'连接失败'

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及数据库元数据信息
        '''
        # 获取数据库元数据
        graph = self.n4j_client._client
        # 节点列表
        node_labels = graph.schema.node_labels
        # 关系列表
        relationships = graph.schema.relationship_types
        metadata_info = f"""
    Node labels: {list(node_labels)}
    Relationship types: {list(relationships)}
            """
        for label in node_labels:
            if model_prompt == '' or label in model_prompt:
                # 获取每个标签的第一个节点进行示例，并获取与该节点有关的关系信息
                query = f"""
                    MATCH (n:{label})
                    WITH n LIMIT 1
                    OPTIONAL MATCH (n)-[r]->(m)
                    RETURN properties(n) AS node_properties, type(r) AS relationship_type, properties(r) AS relationship_properties, m as related_node_demo, labels(m) AS related_node_labels
                    """
                result = graph.run(query)
                metadata_info += f'\n\n {label} node demo：\n {result}'
        info_prompt = f"""
    一个py2neo 封装类，并且提供了一些数据操作的方法
    类中部分参数如下:
    n4j_client._client：py2neo Graph实例
    # 使用示例：
    实例化此类的reader对象，查询数据转为dataframe：
    query = "MATCH (p:Person) RETURN p.name"
    # 执行查询并将结果转换为Dataframe
    result = reader.n4j_client._client.run(query).to_data_frame()

    # DataSource type:
    neo4j
    # MetaData:
    {metadata_info}
            """
        return info_prompt

    def gen_models(self):
        '''
        生成子数据模型
        '''
        labels = self.n4j_client.query('CALL db.labels()')
        model_list = []
        for label in labels:
            dic = {
                'type': f'neo4j_graph',
                'model_conf': {
                    "name": label['label'],
                    "auth_type": "query,create,edit_fields,delete,extract,load"
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
        sql_rules = [i for i in self.extract_rules if i['field'] == 'sql' and i['rule'] == 'search_text' and i['value']]
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
        results = self.n4j_client.query(self.sql)
        total = len(results)
        results = results
        data_li = [obj for obj in results]
        res_data = {
            'records': data_li,
            'total': total,
            'pagination': False  # 禁用分页
        }
        return True, gen_json_response(res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :return:
        '''
        self.gen_extract_rules()
        if 'custom_sql' not in self.auth_types and self.sql != self.default_sql:
            return False, '无修改sql权限'
        results = self.n4j_client.query(self.sql)
        total = len(results)
        data_li = [obj for obj in results]
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            li = data_li[(page-1)*pagesize:page*pagesize]
            res_data = {
                'records': li,
                'total': total
            }
            yield True, gen_json_response(res_data)


