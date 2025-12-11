# coding: utf-8
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from etl.data_models import DataModel
from etl.utils.mindsdb_client import IntegrationsClient, StandaloneHandler
from etl.utils.sql_rule_builder import SQLRuleBuilder
from utils.common_utils import gen_json_response, df_to_list
from mindsdb_sql_parser import parse_sql
from mindsdb_sql_parser.ast import Select, Union, Constant, Show
import logging
import re

logger = logging.getLogger(__name__)


class MindsDBTableModel(DataModel):
    def __init__(self, model_info):
        super().__init__(model_info)
        self.db_type = self._source.get('type')
        self.conn_conf = self._source.get('conn_conf', {})
        model_conf = self._model.get('model_conf', {})
        self.table_name = model_conf.get('name')
        self.auth_types = model_conf.get('auth_type', '').split(',')
        self.client = IntegrationsClient()
        self.handler = None
        self.standalone_handler = None
        self.table_columns = []

        # 初始化SQL规则构建器
        self.sql_rule_builder = SQLRuleBuilder(field_type_getter=self._get_field_type)

    @classmethod
    def get_form_config(cls):
        '''
        获取表格类型模型的配置表单schema
        '''
        return [
            {
                'label': '表名',
                'field': 'name',
                'required': True,
                'component': 'Input',
                'default': '',
            },
            {
                'label': '允许操作',
                'field': 'auth_type',
                'component': 'JCheckbox',
                'componentProps': {
                    'options': [
                        {'label': '查询', 'value': 'query'},
                        {'label': '数据抽取', 'value': 'extract'},
                        {'label': '数据装载', 'value': 'load'},
                    ]
                }
            }
        ]

    def connect(self):
        try:
            # 使用缓存的 get_or_create_handler 方法
            self.handler = self.client.get_or_create_handler(
                handler_type=self.db_type,
                connection_data=self.conn_conf
            )
            self.standalone_handler = StandaloneHandler(self.handler)
            status = self.standalone_handler.check_connection()
            if not status.get('success'):
                return False, status.get('error_message', 'connect failed')
            columns_df = self.standalone_handler.get_columns(self.table_name)
            if not columns_df.empty:
                self.table_columns = columns_df.to_dict('records')
                return True, 'success'
            return False, f'table {self.table_name} not found'
        except Exception as e:
            return False, str(e)

    def get_info_prompt(self, model_prompt=''):
        """
        获取使用提示及数据库元数据信息
        """
        if not self.standalone_handler:
            self.connect()
        try:
            info_prompt = f"""
一个基于 MindsDB 的 数据表模型类，提供了数据表操作的方法
# 使用示例：
实例化此类的 reader 对象，查询 SQL 转为 dataframe：
df = reader.query(sql)

# DataSource type:
{self.db_type}
# MetaData:
table_name:{self.table_name}
columns:
{self.table_columns}
                """
            return info_prompt
        except Exception as e:
            logger.error(f"获取元数据信息失败: {e}")
            return f"MindsDB SQL Model for {self.db_type}"

    def get_res_fields(self):
        if not self.table_columns:
            flag, msg = self.connect()
            if not flag:
                return []
        fields = []
        for col in self.table_columns:
            col_name = col.get('COLUMN_NAME') or col.get('column_name') or col.get('name') or col.get('Field')
            if col_name:
                data_type = col.get('DATA_TYPE') or col.get('data_type') or col.get('type', '').lower() or col.get('Type', '').lower()
                col['type'] = data_type
                fields.append({'field_name': col_name, 'field_value': col_name, 'ext_params': col})
        return fields

    def get_extract_rules(self):
        """
        获取可筛选项
        """
        # 使用统一规则构建器获取操作符
        return self.sql_rule_builder.get_supported_operators()

    def get_supported_operators(self):
        """
        获取支持的筛选操作符列表（使用统一的SQL规则构建器）
        """
        return self.sql_rule_builder.get_supported_operators()

    def _get_field_type(self, field_name):
        """
        获取字段的数据类型
        """
        for col in self.table_columns:
            col_name = col.get('COLUMN_NAME') or col.get('column_name') or col.get('name')
            if col_name == field_name:
                # 获取字段类型信息
                data_type = col.get('DATA_TYPE') or col.get('data_type') or col.get('type', '').lower()
                return data_type
        return 'text'  # 默认为文本类型

    def _convert_value_by_type(self, value, field_type):
        """
        根据字段类型转换值
        """
        if value is None or value == '':
            return None

        # 处理列表值（用于IN操作）
        if isinstance(value, (list, tuple)):
            converted_list = []
            for v in value:
                converted = self._convert_single_value_by_type(v, field_type)
                if converted is not None:
                    converted_list.append(converted)
            return converted_list

        return self._convert_single_value_by_type(value, field_type)

    def _convert_single_value_by_type(self, value, field_type):
        """
        转换单个值
        """
        try:
            field_type = field_type.lower()

            # 数值类型
            if field_type in ['int', 'integer', 'bigint', 'smallint', 'tinyint']:
                return int(float(str(value)))  # 支持字符串数字转换

            # 浮点类型
            elif field_type in ['float', 'double', 'decimal', 'numeric', 'real']:
                return float(str(value))

            # 日期时间类型
            elif field_type in ['date', 'datetime', 'timestamp', 'time']:
                if isinstance(value, str):
                    # 基本日期格式验证
                    return value  # 保持原样，让数据库处理

            # 布尔类型
            elif field_type in ['boolean', 'bool']:
                if isinstance(value, str):
                    value_lower = value.lower()
                    if value_lower in ['true', '1', 'yes', 'on']:
                        return True
                    elif value_lower in ['false', '0', 'no', 'off']:
                        return False
                    else:
                        return None  # 无法转换，跳过
                return bool(value)

            # 文本类型（默认）
            else:
                return str(value) if value is not None else None

        except (ValueError, TypeError) as e:
            logger.warning(f"值转换失败: {value} -> {field_type}, 错误: {str(e)}")
            return None  # 转换失败，返回None表示跳过此条件

    def _escape_sql_value(self, value, field_type):
        """
        根据类型转义SQL值
        """
        if value is None:
            return 'NULL'

        field_type = field_type.lower()

        # 数值类型不需要引号
        if field_type in ['int', 'integer', 'bigint', 'smallint', 'tinyint',
                         'float', 'double', 'decimal', 'numeric', 'real', 'boolean', 'bool']:
            return str(value)

        # 其他类型需要引号并转义
        if isinstance(value, str):
            # 转义单引号
            escaped_value = value.replace("'", "''")
            return f"'{escaped_value}'"

        return f"'{str(value)}'"

    def gen_extract_rules(self):
        """
        解析筛选规则，使用统一的SQL规则构建器
        """
        return self.sql_rule_builder.build_sql_clauses(self.extract_rules)

    def query(self, sql=None, limit=1000, offset=0):
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                raise RuntimeError(f'connect failed: {msg}')

        # 如果没有提供 SQL，构建查询
        if sql is None:
            where_clauses, order_clauses = self.gen_extract_rules()
            sql = f"SELECT * FROM {self.table_name}"
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            if order_clauses:
                sql += " ORDER BY " + ", ".join(order_clauses)

        # 解析 SQL 为 ASTNode
        try:
            ast_query = parse_sql(sql)
        except Exception as e:
            logger.error(f"SQL 解析失败: {e}")
            raise RuntimeError(f'SQL 解析失败: {e}')

        # 检查是否包含不允许的操作（只读模式）
        if not isinstance(ast_query, (Select, Union, Show)):
            operation_type = type(ast_query).__name__
            logger.error(f"不允许的 SQL 操作: {operation_type}")
            raise RuntimeError(f"SQL 包含不允许的操作: {operation_type}")

        # 如果是 SELECT 查询，处理 LIMIT 和 OFFSET
        if isinstance(ast_query, Select):
            # 设置或更新 LIMIT
            if ast_query.limit is None:
                ast_query.limit = Constant(limit)
            # 设置或更新 OFFSET
            if offset > 0:
                if ast_query.offset is None:
                    # 如果没有 OFFSET，添加 OFFSET
                    ast_query.offset = Constant(offset)

        elif isinstance(ast_query, Union):
            # 对于 UNION 查询，在外层添加 LIMIT
            # 设置或更新 LIMIT
            if ast_query.limit is None:
                ast_query.limit = Constant(limit)
            # 设置或更新 OFFSET
            if offset > 0:
                if ast_query.offset is None:
                    # 如果没有 OFFSET，添加 OFFSET
                    ast_query.offset = Constant(offset)
        try:
            # 使用 query 方法传入 ASTNode
            df = (self.standalone_handler.query(ast_query))
            return df
        except Exception as e:
            logger.error(f"查询失败: {e}")
            raise RuntimeError(f'查询失败: {e}')

    def get_total_count(self):
        """
        获取符合条件的总记录数
        """
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                return 0

        try:
            where_clauses, order_clauses = self.gen_extract_rules()
            count_sql = f"SELECT COUNT(*) as total FROM {self.table_name}"
            if where_clauses:
                count_sql += " WHERE " + " AND ".join(where_clauses)
            try:
                ast_query = parse_sql(count_sql)
            except Exception as e:
                logger.error(f"SQL 解析失败: {e}")
                raise RuntimeError(f'SQL 解析失败: {e}')
            count_df = self.standalone_handler.query(ast_query)
            if not count_df.empty:
                return int(count_df.iloc[0]['total'])
            return 0
        except Exception as e:
            logger.warning(f"获取总记录数失败: {str(e)}")
            return 0

    def read_page(self, page=1, pagesize=20):
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                return False, msg
        try:
            # 正常分页处理
            offset = (page - 1) * pagesize

            # 查询数据
            df = self.query(limit=pagesize, offset=offset)
            data_li = df_to_list(df)

            # 获取总记录数
            total_count = self.get_total_count()

            res_data = {
                'records': data_li,
                'total': total_count
            }
            return True, gen_json_response(data=res_data)
        except Exception as e:
            logger.error(f"读取分页数据失败: {str(e)}")
            return False, str(e)

    def read_batch(self):
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                yield False, msg
                return
        try:
            # 正常批量读取
            # 首先获取总记录数
            total_count = self.get_total_count()
            processed_count = 0
            batch_num = 0

            offset = 0
            while True:
                df = self.query(limit=self.batch_size, offset=offset)
                data_li = df_to_list(df)
                if not data_li:
                    break

                batch_num += 1
                processed_count += len(data_li)

                # 构建批次信息
                batch_info = {
                    'records': data_li,
                    'total': total_count
                }

                yield True, gen_json_response(data=batch_info)

                if len(data_li) < self.batch_size or processed_count >= total_count:
                    break
                offset += self.batch_size

        except Exception as e:
            logger.error(f"批量读取数据失败: {str(e)}")
            yield False, str(e)

    def get_table_info(self):
        """
        获取表的详细统计信息
        """
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                return None

        try:
            info = {
                'table_name': self.table_name,
                'total_count': self.get_total_count(),
                'columns': self.table_columns,
                'column_count': len(self.table_columns) if self.table_columns else 0
            }
            return info
        except Exception as e:
            logger.error(f"获取表信息失败: {str(e)}")
            return None

    def write(self, res_data):
        """
        写入数据
        
        Args:
            res_data: 要写入的数据，可以是 list 或 dict
            
        Returns:
            (bool, str): 成功标志和消息
        """
        # 检查权限
        if 'load' not in self.auth_types:
            return False, '无写入权限'
        
        # 获取写入类型
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert', 'update', 'upsert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'
        
        # 获取用于匹配的字段（用于 update 和 upsert）
        self.only_fields = self._load_info.get('only_fields', [])
        
        # 确保连接已建立
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                return False, msg
        
        # 获取表名
        table_name = self.table_name
        # 处理输入数据
        records = []
        if isinstance(res_data, list) and res_data != []:
            records = res_data
        elif isinstance(res_data, dict):
            if 'records' in res_data and res_data['records'] != []:
                records = res_data['records']
            else:
                records = [res_data]
        
        if not records:
            return False, '没有要写入的数据'
        
        try:
            insert_records = []
            
            if self.load_type == 'insert':
                # 直接插入所有记录
                insert_records = records
                
            elif self.load_type in ['update', 'upsert']:
                # 对于 update 和 upsert，需要先查询是否存在
                for record in records:
                    # 构建查询条件
                    query_dict = {k: v for k, v in record.items() if k in self.only_fields}

                    if not query_dict:
                        # 如果没有匹配字段，直接插入
                        insert_records.append(record)
                        continue

                    # 构建 WHERE 条件
                    where_conditions = []
                    for k, v in query_dict.items():
                        field_type = self._get_field_type(k)
                        where_conditions.append(f"{k} = {self._escape_sql_value(v, field_type)}")

                    where_clause = " AND ".join(where_conditions)

                    # 查询是否存在
                    check_sql = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT 1"

                    try:
                        # 解析 SQL 为 ASTNode
                        ast_check = parse_sql(check_sql)
                        df = self.standalone_handler.query(ast_check)

                        if df is not None and not df.empty:
                            # 记录存在，执行更新
                            set_clauses = []
                            for k, v in record.items():
                                field_type = self._get_field_type(k)
                                set_clauses.append(f"{k} = {self._escape_sql_value(v, field_type)}")

                            set_clause = ", ".join(set_clauses)
                            update_sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

                            # 解析 SQL 为 ASTNode
                            ast_update = parse_sql(update_sql)
                            self.standalone_handler.query(ast_update)
                            logger.info(f"更新记录: {where_clause}")
                        else:
                            # 记录不存在
                            if self.load_type == 'upsert':
                                # upsert 模式：不存在则插入
                                insert_records.append(record)
                            # update 模式：不存在则跳过

                    except Exception as e:
                        logger.warning(f"检查记录是否存在失败: {e}，将尝试插入")
                        if self.load_type == 'upsert':
                            insert_records.append(record)

            # 执行批量插入
            if insert_records:
                batch = insert_records

                # 获取第一条记录的列名作为基准
                columns = list(batch[0].keys())
                cols_str = ", ".join(columns)

                # 构建所有记录的 VALUES 子句
                values_clauses = []
                for record in batch:
                    # 确保所有记录都有相同的列
                    values = [self._escape_sql_value(record.get(col), self._get_field_type(col)) for col in columns]
                    vals_str = ", ".join(values)
                    values_clauses.append(f"({vals_str})")
                # 构建批量 INSERT 语句
                values_str = ", ".join(values_clauses)
                insert_sql = f"INSERT INTO {table_name} ({cols_str}) VALUES {values_str}"
                try:
                    # 解析 SQL 为 ASTNode
                    ast_insert = parse_sql(insert_sql)
                    self.standalone_handler.query(ast_insert)
                    logger.info(f"批量插入 {len(batch)} 条记录到 {table_name}")
                except Exception as e:
                    logger.error(f"批量插入失败: {e}")
                    raise
                return True, records
            
            # 如果只有更新操作
            if self.load_type == 'update':
                return True, records
            
            return True, records
            
        except Exception as e:
            error_msg = str(e)[:200]  # 限制错误消息长度
            logger.error(f"写入数据失败: {error_msg}")
            return False, error_msg

    def disconnect(self):
        """
        断开连接（由于使用了缓存，实际上不会真正断开连接）

        缓存系统会自动管理连接的生命周期，在 TTL 过期后自动断开。
        这里只是清理本地引用。
        """
        if self.standalone_handler:
            # 不要调用 disconnect()，因为连接被缓存管理
            # 只清理本地引用
            self.standalone_handler = None
            self.handler = None

    def __del__(self):
        # 清理引用，但不断开连接
        self.standalone_handler = None
        self.handler = None
