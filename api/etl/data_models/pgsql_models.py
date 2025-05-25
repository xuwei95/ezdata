from etl.data_models.base_db_table import BaseDBTableModel
from etl.data_models.base_db_sql import BaseDBSqlModel
from sqlalchemy import Column, TEXT


def gen_string_column(i):
    if 'nullable' in i.keys():
        i['nullable'] = i['nullable'] == 1
    else:
        i['nullable'] = True
    obj = Column(TEXT, nullable=i['nullable'])
    return obj


class PgsqlTableModel(BaseDBTableModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        self.column_gen_map = {
            'String': gen_string_column
        }


class PgsqlSqlModel(BaseDBSqlModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        model_conf = self._model.get('model_conf', {})
        self.sql = model_conf.get('sql', 'select * from pg_tables')
        self.default_sql = self.sql