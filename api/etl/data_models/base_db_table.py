from etl.data_models import DataModel
from etl.utils.db_utils import get_database_engine, get_database_model
from etl.utils.common_utils import trans_rule_value, gen_json_response
from sqlalchemy import not_
from sqlalchemy.sql.schema import Table
from sqlalchemy import Column, String, Integer, Text, SmallInteger, DateTime, TIMESTAMP, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import CreateTable
import pandas as pd
import sqlparse
import re


class BaseDBTableModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        self.db_type = self._source.get('type')
        self.conn_conf = self._source['conn_conf']
        self.conn_conf['type'] = self.db_type
        model_conf = self._model['model_conf']
        self.table_name = model_conf.get('name')
        self.auth_types = model_conf.get('auth_type', '').split(',')
        self.column_gen_map = {}
        Base = declarative_base()
        self.get_table_model()

        class BaseModel(Base):
            '''
            数据库orm模型基类
            '''
            __abstract__ = True
            id = Column(String(36), primary_key=True, nullable=False, comment='ID')

        self.BaseModel = BaseModel
        self.table_args = None

    def get_table_model(self):
        '''
        获取表模型
        :return:
        '''
        self.db_engine = get_database_engine(self.conn_conf)
        self.session, self.db_model = get_database_model(self.table_name, self.db_engine, db_type=self.db_type)
        if isinstance(self.db_model, Table):
            self.table = self.db_model
        elif self.db_model:
            self.table = self.db_model.__table__
        else:
            self.table = None

    def connect(self):
        '''
        连通性测试
        '''
        try:
            if self.table is not None:
                return True, '连接成功'
            else:
                return False, '连接失败'
        except Exception as e:
            return False, str(e)[:100]

    def query(self, sql, limit=1000, offset=0):
        '''
        查询数据
        '''
        # 解析SQL查询
        parsed = sqlparse.parse(sql)
        if not parsed:
            raise RuntimeError('sql解析失败')
        pattern = re.compile(r'\b(DELETE|UPDATE|INSERT|DROP|ALTER|TRUNCATE)\b', re.IGNORECASE)
        matches = pattern.findall(sql)
        if matches:
            raise RuntimeError("SQL包含不允许的操作")
        if sql.upper().strip().startswith('SELECT'):
            # 获取第一个语句
            stmt = parsed[0]
            # 检查是否已经有LIMIT子句
            has_limit = any(token.value.upper() == 'LIMIT' for token in stmt.tokens if hasattr(token, 'value'))
            limit_token = None
            for token in stmt.tokens:
                if hasattr(token, 'value') and token.value.upper() == 'LIMIT':
                    has_limit = True
                    limit_token = token
                    break
            if has_limit:
                # 找到LIMIT后的数值
                limit_value = None
                for token in limit_token.parent.tokens:
                    if token.ttype is None and token.value.isdigit():
                        limit_value = token.value
                        break
                if limit_value:
                    # 替换LIMIT的值
                    sql = sql.replace(f"LIMIT {limit_value}", f"LIMIT {limit}")
            else:
                # 如果没有LIMIT，添加LIMIT
                sql += f" LIMIT {limit}"
            # 检查是否已经有OFFSET子句
            has_offset = any(token.value.upper() == 'OFFSET' for token in stmt.tokens if hasattr(token, 'value'))
            # 如果没有OFFSET，添加OFFSET
            if offset and not has_offset:
                sql += f" OFFSET {offset}"
        df = pd.read_sql(sql, con=self.db_engine)
        return df

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及数据库元数据信息
        '''
        create_sql = str(CreateTable(self.table).compile(self.db_engine))
        metadata_info = f"""
一个基于 SQLAlchemy 的sql数据表模型类，并且提供了一些数据库操作的方法
使用示例：
实例化此类的reader对象，查询sql转为dataframe：
df = reader.query(sql)

# DataSource type: 
{self.db_type}
# MetaData:
{create_sql}
        """
        return metadata_info

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        res_fields = []
        try:
            for column in self.table.columns:
                try:
                    length = column.type.length if column.type.length else 0
                except:
                    length = 0
                column_type = str(column.type)
                for t in ['VARCHAR', 'FixedString']:
                    if t in column_type:
                        column_type = t
                        break
                dic = {
                    'field_name': column.comment if column.comment else column.name,
                    'field_value': column.name,
                    'ext_params': {
                        'type': column_type,
                        'length': length,
                        'is_primary_key': column.primary_key,
                        'nullable': column.nullable,
                        'default': column.default
                    }
                }
                res_fields.append(dic)
        except Exception as e:
            print(e)
        return res_fields

    def genColumn(self, i):
        '''
        根据字典获取列参数，组成orm模型字段
        :param i:
        :return:
        '''
        if 'nullable' in i.keys():
            i['nullable'] = i['nullable'] == 1
        else:
            i['nullable'] = True
        if 'primary_key' in i:
            i['is_primary_key'] = i['primary_key'] == 1
        else:
            i['is_primary_key'] = False
        if 'length' not in i:
            i['length'] = '0'
        if 'type' not in i:
            obj = Column(Text, nullable=True)
        elif i['type'] in ['varchar', 'String']:
            obj = Column(String(i['length']), primary_key=i['is_primary_key'], nullable=i['nullable'])
        elif i['type'] in ['text', 'Text']:
            obj = Column(Text, nullable=i['nullable'])
        elif i['type'] in ['int', 'Int', 'Integer']:
            obj = Column(Integer, primary_key=i['is_primary_key'], nullable=i['nullable'])
        elif i['type'] in ['float', 'Float', 'FLOAT']:
            obj = Column(Float, nullable=i['nullable'])
        elif i['type'] == ['smallint', 'SmallInteger']:
            obj = Column(SmallInteger, nullable=i['nullable'])
        elif i['type'] in ['datetime', 'DateTime']:
            obj = Column(DateTime, nullable=i['nullable'])
        elif i['type'] in ['timestamp', 'TimeStamp', 'TIMESTAMP']:
            obj = Column(TIMESTAMP, nullable=i['nullable'])
        else:
            obj = Column(Text, nullable=True)
        if 'field_name' in i:
            obj.comment = i['field_name']
        return obj

    def create(self, field_arr=[]):
        '''
        创建表
        '''
        if 'create' not in self.auth_types:
            return False, '无创建权限'
        table_args = self.table_args
        try:
            table_name = self.table_name

            class Model(self.BaseModel):
                __tablename__ = self.table_name
                if table_args is not None:
                    __table_args__ = table_args

            for i in field_arr:
                if i['field_value'] == 'id':
                    continue
                if i['type'] in self.column_gen_map:
                    column = self.column_gen_map[i['type']](i)
                else:
                    column = self.genColumn(i)
                setattr(Model, i['field_value'], column)

            if table_name not in self.db_engine.table_names():
                create_sql = str(CreateTable(Model.__table__).compile(self.db_engine))
                print(create_sql)
                Model.__table__.create(self.db_engine)
            self.db_engine.dispose()
            # 重新获取模型
            self.get_table_model()
            return True, '创建成功'
        except Exception as e:
            return False, str(e)

    def delete(self):
        '''
        删除表
        '''
        if 'delete' not in self.auth_types:
            return False, '无删除权限'
        try:
            self.table.drop(self.db_engine)
            self.db_engine.dispose()
            return True, '删除表成功'
        except Exception as e:
            return False, str(e)

    def check_field(self, field_info, res_fields):
        '''
        检察字段是否存在且一致
        '''
        for field in res_fields:
            if field['field_value'] == field_info['field_value'] and field['type'] == field_info['type'] and field[
                'length'] == field_info['length'] and field['nullable'] == field_info['nullable']:
                print(field_info, field)
                return True
        return False

    def set_field(self, field):
        '''
        设置字段
        '''
        if 'edit_fields' not in self.auth_types:
            return False, '无操作字段权限'
        try:
            set_type = 'ADD'
            for column in self.table.columns:
                if column.name == field['field_name']:
                    set_type = 'MODIFY'
                    break
            if field['type'] in ['varchar', 'VARCHAR', 'FixedString']:
                field['type'] = f"{field['type']}({field['length']})"
            c_sql = f"""ALTER TABLE `{self.table_name}` {set_type} COLUMN `{field['field_name']}` {field['type']} COMMENT '{field.get('comment', '')}';"""
            print(c_sql)
            self.db_engine.execute(c_sql)
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
            'name': '从大到小排序',
            'value': 'sort_desc'
        }, {
            'name': '从小到大排序',
            'value': 'sort_asc'
        }
        ]
        return rules

    def gen_extract_rules(self, model):
        '''
        解析筛选规则
        :return:
        '''
        query = self.session.query(model)
        if self.table is None:
            return False, '表不存在'

        columns = self.table.columns
        for i in self.extract_rules:
            field = i.get('field')
            rule = i.get('rule')
            value = i.get('value')
            value = trans_rule_value(value)
            if field and field not in ['sql', 'search_text']:
                column = columns.get(field)
                if column is None:
                    return False, f'未找到字段：{field}'
                if value:
                    if rule in ['eq', 'equal']:
                        query = query.filter(column == value)
                    elif rule == ['neq', 'f_equal']:
                        query = query.filter(column != value)
                    elif rule == 'gt':
                        query = query.filter(column > value)
                    elif rule == 'lt':
                        query = query.filter(column < value)
                    elif rule == 'gte':
                        query = query.filter(column >= value)
                    elif rule == 'lte':
                        query = query.filter(column <= value)
                    elif rule == 'contain':
                        text = f"%{value}%"
                        query = query.filter(column.like(text))
                    elif rule == 'f_contain':
                        text = f"%{value}%"
                        query = query.filter(not_(column.like(text)))
                    elif rule == 'sort':
                        if value == 'desc':
                            query = query.order_by(column.desc())
                        else:
                            query = query.order_by(column)
        return True, query

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        if self.db_model is False:
            return False, '数据库链接错误'
        flag, query = self.gen_extract_rules(self.db_model)
        if not flag:
            return False, query
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        data_li = []
        for obj in obj_list:
            dic = {c.name: getattr(obj, c.name) for c in self.table.columns}
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
        if self.db_model is False:
            yield False, '数据库链接错误'
        flag, query = self.gen_extract_rules(self.db_model)
        if not flag:
            yield False, query
        total = query.count()
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            query = query.offset((page - 1) * pagesize)
            query = query.limit(pagesize)
            obj_list = query.all()
            data_li = []
            for obj in obj_list:
                dic = {c.name: getattr(obj, c.name) for c in self.table.columns}
                data_li.append(dic)
            res_data = {
                'records': data_li,
                'total': total
            }
            yield True, gen_json_response(res_data)

    def write(self, res_data):
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert', 'update', 'upsert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'
        self.only_fields = self._load_info.get('only_fields', [])
        if self.table is None:
            return False, '表不存在'
        columns = self.table.columns
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
            elif self.load_type in ['update', 'upsert']:
                for c in records:
                    query_dict = {k: v for k, v in c.items() if k in self.only_fields}
                    query = self.session.query(self.db_model)
                    for k in query_dict:
                        query = query.filter(getattr(self.db_model, k) == query_dict[k])
                    obj = query.first()
                    if obj is not None:
                        for k in c:
                            setattr(obj, k, c[k])
                        self.session.add(obj)
                        self.session.commit()
                    elif self.load_type == 'upsert':
                        insert_records.append(c)
            if insert_records != []:
                # 创建 insert 对象
                ins = self.table.insert()
                conn = self.db_engine.connect()
                tmp_list = [{k: v for k, v in c.items() if k in columns} for c in insert_records]
                conn.execute(ins, tmp_list)
                conn.commit()
        except Exception as e:
            return False, f'{str(e)[:100]}'
        return True, res_data
