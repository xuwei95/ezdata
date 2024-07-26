from ezetl.data_models.base_db_table import BaseDBTableModel
from clickhouse_sqlalchemy import engines
from sqlalchemy import Column, TEXT, String


def gen_fixstring_column(i):
    if 'nullable' in i.keys():
        i['nullable'] = i['nullable'] == 1
    else:
        i['nullable'] = True
    if 'primary_key' in i.keys():
        i['primary_key'] = i['primary_key'] == 1
    else:
        i['primary_key'] = True
    obj = Column(String(i['length']), nullable=i.get('nullable', True), primary_key=i.get('primary_key', False))
    return obj


def gen_string_column(i):
    if 'nullable' in i.keys():
        i['nullable'] = i['nullable'] == 1
    else:
        i['nullable'] = True
    obj = Column(TEXT, nullable=i['nullable'])
    return obj


class CkTableModel(BaseDBTableModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        self.column_gen_map = {
            'FixedString': gen_fixstring_column,
            'String': gen_string_column
        }
        model_conf = self._model.get('model_conf', {})
        engine = model_conf.get('engine', 'MergeTree')
        order_by = model_conf.get('order_by', ['id'])
        if engine and engine == 'ReplacingMergeTree':
            self.table_args = (
                engines.ReplacingMergeTree(order_by=order_by),
            )
        else:
            self.table_args = (
                engines.MergeTree(order_by=order_by),
            )

    def write(self, res_data):
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'
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
            insert_records = records
            # 创建 insert 对象
            ins = self.table.insert()
            conn = self.db_engine.connect()
            tmp_list = [{k: v for k, v in c.items() if k in columns} for c in insert_records]
            conn.execute(ins, tmp_list)
        except Exception as e:
            return False, f'{str(e)[:100]}'
        return True, res_data