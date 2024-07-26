from ezetl.data_models.base_db_table import BaseDBTableModel
from ezetl.data_models.base_db_sql import BaseDBSqlModel
from sqlalchemy import Column, TEXT, MetaData
from ezetl.utils.common_utils import gen_json_response
from sqlalchemy.schema import CreateTable


def gen_string_column(i):
    if 'nullable' in i.keys():
        i['nullable'] = i['nullable'] == 1
    else:
        i['nullable'] = True
    obj = Column(TEXT, nullable=i['nullable'])
    return obj


class SqlServerTableModel(BaseDBTableModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        self.column_gen_map = {
            'String': gen_string_column
        }

    def create(self, field_arr=[]):
        '''
        创建表
        '''
        if 'create' not in self.auth_types:
            return False, '无创建权限'
        table_args = self.table_args
        try:
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

            metadata = MetaData()
            metadata.reflect(bind=self.db_engine)
            if self.table_name not in metadata.tables.keys():
                create_sql = str(CreateTable(Model.__table__).compile(self.db_engine))
                print(create_sql)
                Model.__table__.create(self.db_engine)
            self.db_engine.dispose()
            # 重新获取模型
            self.get_table_model()
            return True, '创建成功'
        except Exception as e:
            return False, str(e)

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
        query = query.order_by(self.table.columns[0])
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
        if not self.db_model:
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
            query = query.order_by(self.table.columns[0])
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


class SqlServerSqlModel(BaseDBSqlModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        model_conf = self._model.get('model_conf', {})
        self.sql = model_conf.get('sql', 'SELECT name FROM sys.tables')
        self.default_sql = self.sql