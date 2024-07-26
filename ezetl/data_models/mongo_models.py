import json
import mongoengine
from ezetl.data_models import DataModel
from ezetl.utils.common_utils import trans_rule_value, gen_json_response, parse_json


class MongoModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        conn_conf = self._source['conn_conf']
        model_conf = self._model.get('model_conf', {})
        conn_url = f"mongodb://{conn_conf.get('username')}:{conn_conf.get('password')}@{conn_conf.get('host')}:{conn_conf.get('port')}/{conn_conf.get('database_name')}"
        self.conn = mongoengine.connect(host=conn_url)
        self.collection = model_conf.get('name', '')
        if self.collection != '':
            class Model(mongoengine.DynamicDocument):
                meta = {'collection': model_conf.get('name', '')}
            self.model = Model
        else:
            self.model = None

    def connect(self):
        '''
        连通性测试
        '''
        try:
            db = mongoengine.connection.get_db()
            collection_names = db.list_collection_names()
            if self.collection == '':
                if db:
                    return True, '连接成功'
                else:
                    return False, '连接失败'
            else:
                if self.collection in collection_names:
                    return True, '连接成功'
                else:
                    return False, '连接失败'
        except Exception as e:
            print(e)
            return False, str(e)[:100]

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及数据库元数据信息
        '''
        # 查询集合中有哪些字段
        fields = self.model._fields.keys()
        # 查询元数据信息
        metadata = self.model._meta
        metadata_info = f"""
collection name: {metadata['collection']}
fields: {fields.keys()}
indexes: {metadata['indexes']}
ordering: {metadata['ordering']}
        """
        info_prompt = f"""
一个mongoengine封装类，并且提供了一些数据操作的方法
类中部分参数如下:
collection：集合名称
model: python mongoengine库 集合 实例，可用此对象，执行数据操作，如查询数据
# 使用示例：
实例化此类的reader对象，查询数据转为dataframe：
obj_list = reader.model.objects().all()
data_li = [json.loads(obj.to_json()) for obj in obj_list]
df = pd.DataFrame(data_li)
reader.conn.close()

# DataSource type: 
mongodb
# MetaData:
{metadata_info}
        """
        return info_prompt

    def gen_models(self):
        '''
        生成子数据模型
        '''
        db = mongoengine.connection.get_db()
        collection_names = db.list_collection_names()
        model_list = []
        for collection_name in collection_names:
            dic = {
                'type': f'mongodb_collection',
                'model_conf': {
                    "name": collection_name,
                    "auth_type": "query,create,edit_fields,delete,extract,load"
                }
            }
            model_list.append(dic)
        return model_list

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        res_fields = []
        try:
            # todo: 获取不到具体字段
            fields = self.model._fields
            for k, v in fields.items():
                dic = {
                    'field_name': v.name,
                    'field_value': v.name
                }
                res_fields.append(dic)
        except Exception as e:
            print(e)
        return res_fields

    def create(self, field_arr=[]):
        '''
        创建表
        '''
        try:
            return True, '创建成功'
        except Exception as e:
            return False, str(e)

    def delete(self):
        '''
        删除
        '''
        try:
            db = mongoengine.connection.get_db()
            table = getattr(db, self.collection)
            table.drop()
            return True, '删除成功'
        except Exception as e:
            return False, str(e)

    def set_field(self, field, options={}):
        '''
        设置字段
        '''
        try:
            return True, '操作成功'
        except Exception as e:
            return False, str(e)

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
          }
        ]
        return rules

    def gen_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        if self.model is None:
            return False, '表不存在'
        query = self.model.objects()
        for i in self.extract_rules:
            field = i.get('field')
            rule = i.get('rule')
            value = i.get('value')
            value = trans_rule_value(value)
            if field and field not in ['sql', 'search_key']:
                if value:
                    q_dict = {}
                    if rule in ['equal', 'eq']:
                        q_dict = {field: value}
                    elif rule in ['f_equal', 'neq']:
                        q_dict = {f"{field}__ne": value}
                    elif rule == 'gt':
                        q_dict = {f"{field}__gt": value}
                    elif rule == 'lt':
                        q_dict = {f"{field}__lt": value}
                    elif rule == 'gte':
                        q_dict = {f"{field}__gte": value}
                    elif rule == 'lte':
                        q_dict = {f"{field}__lte": value}
                    elif rule == 'contain':
                        q_dict = {f"{field}__in": value}
                    elif rule == 'f_contain':
                        q_dict = {f"{field}__nin": value}
                    if q_dict != {}:
                        query = query.filter(**q_dict)
                else:
                    if rule == 'sort_asc':
                        query = query.order_by(field)
                    elif rule == 'sort_desc':
                        query = query.order_by(f"-{field}")
        return True, query

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        if self.model is False:
            return False, '数据库链接错误'
        flag, query = self.gen_extract_rules()
        if not flag:
            return False, query
        total = query.count()
        query = query.skip((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        self.conn.close()
        data_li = []
        for obj in obj_list:
            dic = json.loads(obj.to_json())
            data_li.append(dic)
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
        if self.model is False:
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
                dic = json.loads(obj.to_json())
                data_li.append(dic)
            res_data = {
                'records': data_li,
                'total': total
            }
            yield True, gen_json_response(res_data)
        self.conn.close()

    def write(self, res_data):
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert', 'update', 'upsert']:
            return False, '写入类型参数错误'
        self.only_fields = self._load_info.get('only_fields', [])
        if self.model is None:
            return False, '表不存在'
        contents = []
        if isinstance(res_data, list) and res_data != []:
            contents = res_data
        if isinstance(res_data, dict):
            if 'contents' in res_data and res_data['contents'] != []:
                contents = res_data['contents']
            else:
                contents = [res_data]
        try:
            insert_contents = []
            if self.load_type == 'insert':
                insert_contents = contents
            elif self.load_type in ['update', 'upsert']:
                for c in contents:
                    query_dict = {k: v for k, v in c.items() if k in self.only_fields}
                    query = self.model.objects()
                    for k in query_dict:
                        query = query.filter(**{k: query_dict[k]})
                    obj = query.first()
                    if obj is not None:
                        for k in c:
                            setattr(obj, k, c[k])
                        obj.save()
                    elif self.load_type == 'upsert':
                        insert_contents.append(c)
            if insert_contents != []:
                # 创建 insert 对象
                for c in insert_contents:
                    obj = self.model(**c)
                    obj.save()
        except Exception as e:
            return False, f'{str(e)[:100]}'
        return True, res_data

