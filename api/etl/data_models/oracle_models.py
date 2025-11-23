from etl.data_models.base_db_table import BaseDBTableModel
from etl.data_models.base_db_sql import BaseDBSqlModel
from sqlalchemy import Column, TEXT, MetaData
from sqlalchemy.schema import CreateTable


def gen_string_column(i):
    if 'nullable' in i.keys():
        i['nullable'] = i['nullable'] == 1
    else:
        i['nullable'] = True
    obj = Column(TEXT, nullable=i['nullable'])
    return obj


class OracleTableModel(BaseDBTableModel):

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


class OracleSqlModel(BaseDBSqlModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        model_conf = self._model.get('model_conf', {})
        self.sql = model_conf.get('sql', 'SELECT table_name FROM user_tables')
        self.default_sql = self.sql