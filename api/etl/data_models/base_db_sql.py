from etl.data_models import DataModel
from etl.utils.db_utils import get_database_engine
from etl.utils.common_utils import gen_json_response, df_to_list
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
from sqlalchemy.schema import CreateTable, Table
import pandas as pd
import re
import sqlparse
import logging

logger = logging.getLogger(__name__)


class BaseDBSqlModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        self.db_type = self._source.get('type')
        conn_conf = self._source['conn_conf']
        conn_conf['type'] = self.db_type
        model_conf = self._model.get('model_conf', {})
        self.sql = model_conf.get('sql', 'show tables')
        self.default_sql = self.sql
        self.auth_types = model_conf.get('auth_type', '').split(',')
        self.db_engine = get_database_engine(conn_conf)
        DBSession = sessionmaker(bind=self.db_engine)
        self.session = DBSession()

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
            return False, f'{e}'

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及数据库元数据信息
        '''
        metadata = MetaData()
        metadata.reflect(bind=self.db_engine)
        create_sql_list = []
        for table_name in metadata.tables:
            if model_prompt == '' or table_name in model_prompt:
                table = Table(table_name, metadata, autoload_with=self.db_engine)
                create_sql = str(CreateTable(table).compile(self.db_engine))
                create_sql_list.append(create_sql)
        tables_info = '\n'.join(create_sql_list)
        info_prompt = f"""
一个基于 SQLAlchemy 的sql模型类，并且提供了一些数据库操作的方法
类中部分参数如下:
db_engine: SQLAlchemy数据库链接engine实例，可用此对象，执行数据库操作，如查询，执行sql
# 使用示例：
实例化此类的reader对象，查询sql转为dataframe：
df = reader.query(sql)

# DataSource type: 
{self.db_type}
# MetaData:
{tables_info}
        """
        return info_prompt

    def gen_models(self):
        '''
        生成子数据模型
        '''
        metadata = MetaData()
        metadata.reflect(bind=self.db_engine)
        model_list = []
        for table_name in metadata.tables:
            dic = {
                'type': f'{self.db_type}_table',
                'model_conf': {
                    "name": table_name,
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
        sql_rules = [i for i in self.extract_rules if i['field'] == 'search_text' and i['rule'] == 'sql' and i['value']]
        if sql_rules != []:
            self.sql = sql_rules[0].get('value')

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
        df = self.query(self.sql, limit=self.batch_size)
        data_li = df_to_list(df)
        total = len(data_li)
        res_data = {
            'records': data_li,
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
            yield False, '无修改sql权限'
        df = self.query(self.sql, limit=self.batch_size)
        data_li = df_to_list(df)
        total = len(data_li)
        res_data = {
            'records': data_li,
            'total': total
        }
        yield True, gen_json_response(data=res_data)
