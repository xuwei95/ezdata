from ezetl.data_models.base_db_table import BaseDBTableModel
from ezetl.data_models.base_db_sql import BaseDBSqlModel
from sqlalchemy import Column, String, MetaData, Table


def gen_string_column():
    obj = Column(String)
    return obj


class HiveTableModel(BaseDBTableModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        self.column_gen_map = {
            'TEXT': gen_string_column,
            'String': gen_string_column
        }

    def create(self, field_arr=[]):
        '''
        创建表
        '''
        if 'create' not in self.auth_types:
            return False, '无创建权限'
        try:
            metadata = MetaData()
            metadata.reflect(bind=self.db_engine)
            if self.table_name not in metadata.tables.keys():
                # 定义表格结构
                _table = Table(self.table_name, metadata)
                for i in field_arr:
                    if i['type'] in self.column_gen_map:
                        column = self.column_gen_map[i['type']](i)
                    else:
                        column = self.genColumn(i)
                    column.name = i['field_value']
                    _table.append_column(column)
                # 执行建表操作
                metadata.create_all(self.db_engine)
            self.db_engine.dispose()
            # 重新获取模型
            self.get_table_model()
            return True, '创建成功'
        except Exception as e:
            return False, str(e)


class HiveSqlModel(BaseDBSqlModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        model_conf = self._model.get('model_conf', {})
        self.sql = model_conf.get('sql', 'SHOW TABLES')
        self.default_sql = self.sql