from etl.data_models.base_db_table import BaseDBTableModel
from clickhouse_sqlalchemy import engines
from sqlalchemy import Column, TEXT, String
from sqlalchemy.schema import CreateTable


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
        
        # 设置表引擎参数
        if engine and engine == 'ReplacingMergeTree':
            self.table_args = (
                engines.ReplacingMergeTree(order_by=order_by),
            )
        elif engine and engine == 'MergeTree':
            self.table_args = (
                engines.MergeTree(order_by=order_by),
            )
        else:
            # 默认使用 MergeTree 引擎
            self.table_args = (
                engines.MergeTree(order_by=order_by),
            )
        
        # 确保 table_args 被正确设置
        if not hasattr(self, 'table_args') or not self.table_args:
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
    
    def get_info_prompt(self, model_prompt=''):
        """
        重写父类方法，为 ClickHouse 表提供正确的 DDL 信息
        """
        try:
            # 使用 table_args 中的引擎信息生成 DDL
            if hasattr(self, 'table_args') and self.table_args:
                create_sql = str(CreateTable(self.table, *self.table_args).compile(self.db_engine))
            else:
                # 如果没有 table_args，使用默认引擎
                default_engine = engines.MergeTree(order_by=['id'])
                create_sql = str(CreateTable(self.table, default_engine).compile(self.db_engine))
        except Exception as e:
            # 如果编译失败，手动构建 DDL
            try:
                columns_info = []
                for column in self.table.columns:
                    col_info = f"{column.name} {column.type}"
                    if column.primary_key:
                        col_info += " PRIMARY KEY"
                    if not column.nullable:
                        col_info += " NOT NULL"
                    columns_info.append(col_info)
                
                create_sql = f"CREATE TABLE {self.table.name} (\n  " + ",\n  ".join(columns_info) + "\n)"
                
                # 添加 ClickHouse 引擎信息
                if hasattr(self, 'table_args') and self.table_args:
                    engine_info = str(self.table_args[0])
                    create_sql += f"\n{engine_info}"
                else:
                    create_sql += "\nENGINE = MergeTree()\nORDER BY id"
                    
            except Exception as e2:
                create_sql = f"表信息获取失败: {str(e2)}"
        
        metadata_info = f"""
一个基于 SQLAlchemy 的 ClickHouse 数据表模型类，并且提供了一些数据库操作的方法
使用示例：
实例化此类的reader对象，查询sql转为dataframe：
df = reader.query(sql)

# DataSource type: 
{self.db_type}
# MetaData:
{create_sql}
        """
        return metadata_info