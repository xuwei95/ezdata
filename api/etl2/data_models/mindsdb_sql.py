# -*- coding: utf-8 -*-
"""
基于 MindsDB 的 SQL 数据模型
使用 MindsDB handlers 连接各种数据库，支持 SQL 查询
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from etl2.data_models import DataModel
from etl2.utils.mindsdb_client import IntegrationsClient, StandaloneHandler
from etl.utils.common_utils import gen_json_response, df_to_list
from mindsdb_sql_parser import parse_sql
from mindsdb_sql_parser.ast import (
    Select, Union
)
import logging

logger = logging.getLogger(__name__)


class MindsDBSqlModel(DataModel):
    """
    基于 MindsDB 的 SQL 数据模型
    支持各种数据库的连接和查询
    """

    def __init__(self, model_info):
        super().__init__(model_info)
        self.db_type = self._source.get('type')
        self.conn_conf = self._source.get('conn_conf', {})
        model_conf = self._model.get('model_conf', {})
        self.sql = model_conf.get('sql', 'show tables')
        self.default_sql = self.sql
        self.auth_types = model_conf.get('auth_type', '').split(',')

        # 创建 MindsDB client
        self.client = IntegrationsClient()
        self.handler = None
        self.standalone_handler = None

    @classmethod
    def get_form_config(cls):
        '''
        获取SQL类型模型的配置表单schema
        '''
        return [
            {
                'label': '查询语句',
                'field': 'sql',
                'required': True,
                'default': '',
                'component': 'MonacoEditor',
                'componentProps': {
                    'language': 'sql',
                }
            },
            {
                'label': '允许操作',
                'field': 'auth_type',
                'component': 'JCheckbox',
                'default': 'query,extract',
                'componentProps': {
                    'options': [
                        {'label': '查询', 'value': 'query'},
                        {'label': '自定义sql查询', 'value': 'custom_sql'},
                        {'label': '数据抽取', 'value': 'extract'},
                    ]
                }
            }
        ]

    def connect(self):
        """
        连通性测试
        """
        try:
            # 创建 handler
            self.handler = self.client.create_handler(
                handler_type=self.db_type,
                connection_data=self.conn_conf
            )

            # 包装为 StandaloneHandler 以获得更友好的接口
            self.standalone_handler = StandaloneHandler(self.handler)

            # 检查连接
            status = self.standalone_handler.check_connection()

            if status.get('success'):
                logger.info(f"MindsDB handler 连接成功: {self.db_type}")
                return True, '连接成功'
            else:
                error_msg = status.get('error_message', '连接失败')
                logger.error(f"MindsDB handler 连接失败: {error_msg}")
                return False, error_msg

        except Exception as e:
            logger.error(f"MindsDB handler 连接异常: {e}")
            return False, f'{e}'

    def get_info_prompt(self, model_prompt=''):
        """
        获取使用提示及数据库元数据信息
        """
        if not self.standalone_handler:
            self.connect()

        try:
            # 获取所有表
            tables_df = self.standalone_handler.get_tables()
            tables_info = []

            if not tables_df.empty:
                # 获取表名列（可能是 TABLE_NAME 或其他列名）
                table_col = None
                for col in ['TABLE_NAME', 'table_name', 'name', 'Name']:
                    if col in tables_df.columns:
                        table_col = col
                        break

                if table_col:
                    # 筛选需要获取元数据的表
                    if model_prompt == '':
                        # 获取所有表
                        target_tables = tables_df[table_col].tolist()
                    else:
                        # 只获取 model_prompt 中提到的表
                        target_tables = [
                            table_name for table_name in tables_df[table_col]
                            if str(table_name) in model_prompt
                        ]

                    if target_tables:
                        try:
                            # 使用 meta_get_columns 一次性获取所有表的列元数据信息
                            target_tables_str = [str(t).strip() for t in target_tables if str(t).strip()]
                            meta_columns_df = self.standalone_handler.meta_get_columns(target_tables_str)

                            if not meta_columns_df.empty:
                                # 按表名分组，生成每个表的信息
                                # 找到 TABLE_NAME 和 COLUMN_NAME 列
                                table_name_col = None
                                for col in ['TABLE_NAME', 'table_name', 'name', 'Name']:
                                    if col in meta_columns_df.columns:
                                        table_name_col = col
                                        break

                                if table_name_col:
                                    for table_name in target_tables_str:
                                        # 筛选该表的列信息
                                        table_columns = meta_columns_df[
                                            meta_columns_df[table_name_col] == table_name
                                        ]

                                        if not table_columns.empty:
                                            # 格式化列信息，包含更多详细信息
                                            columns_list = []
                                            for _, row in table_columns.iterrows():
                                                col_info_parts = []

                                                # 列名
                                                col_name = row.get('COLUMN_NAME') or row.get('column_name') or row.get('Field')
                                                col_info_parts.append(f"  - {col_name}")

                                                # 数据类型
                                                data_type = row.get('DATA_TYPE') or row.get('data_type') or row.get('Type')
                                                if data_type:
                                                    col_info_parts.append(f"({data_type})")

                                                # 是否可为空
                                                is_nullable = row.get('IS_NULLABLE') or row.get('is_nullable') or row.get('Null')
                                                if is_nullable is not None:
                                                    nullable_str = 'NULL' if str(is_nullable).upper() in ['YES', 'TRUE', '1'] else 'NOT NULL'
                                                    col_info_parts.append(nullable_str)

                                                # 默认值
                                                default_val = row.get('COLUMN_DEFAULT') or row.get('column_default') or row.get('Default')
                                                if default_val and str(default_val).lower() != 'none':
                                                    col_info_parts.append(f"DEFAULT {default_val}")

                                                # 列描述
                                                description = row.get('COLUMN_DESCRIPTION') or row.get('column_description') or row.get('Comment')
                                                if description and str(description).lower() != 'none':
                                                    col_info_parts.append(f"-- {description}")

                                                columns_list.append(' '.join(col_info_parts))

                                            columns_info = '\n'.join(columns_list)
                                            tables_info.append(f"Table: {table_name}\n{columns_info}")
                                        else:
                                            tables_info.append(f"Table: {table_name}\n  (无列信息)")
                                else:
                                    # 如果找不到 TABLE_NAME 列，回退到简单格式
                                    tables_info.append(f"所有表的列信息:\n{meta_columns_df.to_string()}")
                            else:
                                # 如果 meta_get_columns 返回空，尝试逐个获取
                                for table_name in target_tables_str:
                                    tables_info.append(f"Table: {table_name}\n  (无列信息)")

                        except Exception as e:
                            # 如果 meta_get_columns 失败，回退到原有逻辑
                            logger.warning(f"使用 meta_get_columns 失败，回退到逐个获取: {e}")
                            import traceback
                            logger.debug(traceback.format_exc())

                            for table_name in target_tables_str:
                                try:
                                    # 获取表的列信息
                                    columns_df = self.standalone_handler.get_columns(table_name)

                                    if columns_df is not None and not columns_df.empty:
                                        columns_info = columns_df.to_string()
                                        tables_info.append(f"Table: {table_name}\n{columns_info}")
                                    else:
                                        tables_info.append(f"Table: {table_name}\n  (无列信息)")
                                except Exception as e2:
                                    logger.warning(f"获取表 {table_name} 的列信息失败: {e2}")
                                    tables_info.append(f"Table: {table_name}\n  (列信息获取失败: {str(e2)})")

            tables_metadata = '\n\n'.join(tables_info)

            info_prompt = f"""
一个基于 MindsDB 的 SQL 模型类，提供了数据库操作的方法
# 使用示例：
实例化此类的 reader 对象，查询 SQL 转为 dataframe：
df = reader.query(sql)

# DataSource type:
{self.db_type}

# MetaData:
{tables_metadata if tables_metadata else '(未获取到表信息)'}
            """
            return info_prompt
        except Exception as e:
            logger.error(f"获取元数据信息失败: {e}")
            return f"MindsDB SQL Model for {self.db_type}"

    def gen_models(self):
        """
        生成子数据模型
        """
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                return []

        try:
            tables_df = self.standalone_handler.get_tables()
            model_list = []

            if not tables_df.empty:
                # 获取表名列
                table_col = None
                for col in ['TABLE_NAME', 'table_name', 'name', 'Name']:
                    if col in tables_df.columns:
                        table_col = col
                        break

                if table_col:
                    for table_name in tables_df[table_col]:
                        dic = {
                            'type': f'{self.db_type}_table',
                            'model_conf': {
                                "name": str(table_name),
                                "auth_type": "query,create,edit_fields,delete,extract,load"
                            }
                        }
                        model_list.append(dic)

            return model_list
        except Exception as e:
            logger.error(f"生成子模型失败: {e}")
            return []

    def get_res_fields(self):
        """
        获取字段列表
        """
        flag, res = self.read_page(pagesize=1)
        if flag and res.get('code') == 200:
            records = res['data']['records']
            if records:
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
        """
        获取可用高级查询类型
        """
        return [{
            'name': 'sql',
            'value': 'sql',
            "default": self.sql
        }]

    def get_extract_rules(self):
        """
        获取可筛选项
        """
        rules = []
        return rules

    def gen_extract_rules(self):
        """
        解析筛选规则
        """
        sql_rules = [i for i in self.extract_rules if i['field'] == 'search_text' and i['rule'] == 'sql' and i['value']]
        if sql_rules:
            self.sql = sql_rules[0].get('value')

    def query(self, sql, limit=1000, offset=0):
        """
        查询数据

        Args:
            sql: SQL 查询语句
            limit: 返回记录数限制
            offset: 偏移量

        Returns:
            pandas.DataFrame: 查询结果
        """
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                raise RuntimeError(f'数据库连接失败: {msg}')

        # 使用 mindsdb_sql_parser 解析 SQL 查询
        try:
            ast_query = parse_sql(sql)
        except Exception as e:
            logger.error(f"SQL 解析失败: {e}")
            raise RuntimeError(f'SQL 解析失败: {e}')

        # 检查是否包含不允许的操作（只读模式）
        # 只允许 SELECT 和 UNION 查询
        if not isinstance(ast_query, (Select, Union)):
            operation_type = type(ast_query).__name__
            logger.error(f"不允许的 SQL 操作: {operation_type}")
            raise RuntimeError(f"SQL 包含不允许的操作: {operation_type}")

        # 如果是 SELECT 查询，处理 LIMIT 和 OFFSET
        if isinstance(ast_query, Select):
            # 设置或更新 LIMIT
            if ast_query.limit is not None:
                # 如果已有 LIMIT，替换为指定的 limit 值
                ast_query.limit.value = limit
            else:
                # 如果没有 LIMIT，添加 LIMIT
                from mindsdb_sql_parser.ast import Constant
                ast_query.limit = Constant(limit)

            # 设置或更新 OFFSET
            if offset > 0:
                if ast_query.offset is not None:
                    # 如果已有 OFFSET，更新值
                    ast_query.offset.value = offset
                else:
                    # 如果没有 OFFSET，添加 OFFSET
                    from mindsdb_sql_parser.ast import Constant
                    ast_query.offset = Constant(offset)

            # 将修改后的 AST 转回 SQL 字符串
            sql = ast_query.to_string()

        elif isinstance(ast_query, Union):
            # 对于 UNION 查询，在外层添加 LIMIT
            sql = f"({sql}) LIMIT {limit}"
            if offset > 0:
                sql += f" OFFSET {offset}"

        try:
            # 使用 MindsDB handler 执行查询
            df = self.standalone_handler.query(sql)
            return df
        except Exception as e:
            logger.error(f"SQL 查询失败: {e}")
            raise RuntimeError(f'查询失败: {e}')

    def read_page(self, page=1, pagesize=20):
        """
        分页读取数据

        Args:
            page: 页码
            pagesize: 每页记录数

        Returns:
            (success, response): 成功标志和响应数据
        """
        self.gen_extract_rules()

        # 检查权限
        if 'custom_sql' not in self.auth_types and self.sql != self.default_sql:
            return False, '无修改 SQL 权限'

        try:
            df = self.query(self.sql, limit=self.batch_size)
            data_li = df_to_list(df)
            total = len(data_li)

            res_data = {
                'records': data_li,
                'total': total,
                'pagination': False  # 禁用分页
            }
            return True, gen_json_response(data=res_data)
        except Exception as e:
            logger.error(f"分页读取失败: {e}")
            return False, str(e)

    def read_batch(self):
        """
        生成器分批读取数据

        Yields:
            (success, response): 成功标志和响应数据
        """
        self.gen_extract_rules()

        # 检查权限
        if 'custom_sql' not in self.auth_types and self.sql != self.default_sql:
            yield False, '无修改 SQL 权限'
            return

        try:
            df = self.query(self.sql, limit=self.batch_size)
            data_li = df_to_list(df)
            total = len(data_li)

            res_data = {
                'records': data_li,
                'total': total
            }
            yield True, gen_json_response(data=res_data)
        except Exception as e:
            logger.error(f"批量读取失败: {e}")
            yield False, str(e)

    def disconnect(self):
        """
        断开连接
        """
        if self.standalone_handler:
            try:
                self.standalone_handler.disconnect()
                logger.info(f"MindsDB handler 已断开连接: {self.db_type}")
            except Exception as e:
                logger.warning(f"断开连接时出错: {e}")

    def __del__(self):
        """
        析构函数，确保连接被关闭
        """
        self.disconnect()
