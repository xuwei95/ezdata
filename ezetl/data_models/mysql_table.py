from ezetl.data_models.base_db_table import BaseDBTableModel
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import LONGTEXT


def gen_longtext_column(i):
    if 'nullable' in i.keys():
        i['nullable'] = i['nullable'] == 1
    else:
        i['nullable'] = True
    obj = Column(LONGTEXT, nullable=i['nullable'])
    return obj


class MysqlTableModel(BaseDBTableModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        self.column_gen_map = {
            'LONGTEXT': gen_longtext_column
        }
