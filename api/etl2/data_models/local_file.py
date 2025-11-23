# -*- coding: utf-8 -*-
"""
本地文件数据模型
基于mindsdb file handler实现本地文件读取
"""

import os
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

from mindsdb.integrations.utilities.files.file_reader import FileReader
from etl2.data_models import DataModel
from etl2.utils.sql_rule_builder import SQLRuleBuilder
from utils.common_utils import gen_json_response, df_to_list

# 用于SQL查询处理
try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False


class LocalFileModel(DataModel):
    """
    本地文件数据模型
    支持读取多种格式的本地文件：CSV, Excel, JSON, Parquet, TXT, PDF
    支持基于SQL查询的数据筛选
    """

    name = "local_file"

    # 支持的文件格式
    SUPPORTED_FORMATS = [
        'csv', 'xlsx', 'xls', 'json', 'parquet',
        'txt', 'pdf', 'tsv'
    ]

    def __init__(self, model_info):
        super().__init__(model_info)
        self.db_type = self._source.get('type', 'local_file')
        self.conn_conf = self._source.get('conn_conf', {})

        # 获取表名（用于mindsdb files handler兼容性）
        model_conf = self._model.get('model_conf', {})
        self.table_name = model_conf.get('name') or self._model.get('name', '')

        # 使用localfile模型，从conn_conf获取配置
        self.file_path = self.conn_conf.get('path') or ''
        self.sheet_name = self.conn_conf.get('sheet_name')
        self.encoding = self.conn_conf.get('encoding') or 'utf-8'  # 默认编码
        self.delimiter = self.conn_conf.get('delimiter')

        # 从extract_info中获取批处理大小
        self.chunk_size = self._extract_info.get('batch_size', 1000)

        # SQL筛选配置
        self.sql_query = self._extract_info.get('sql', '')
        self.where_clause = self._extract_info.get('where_clause', '')
        self.select_columns = self._extract_info.get('select_columns', [])  # 列名列表
        self.order_by = self._extract_info.get('order_by', '')
        self.limit_count = self._extract_info.get('limit', None)
        self.offset_count = self._extract_info.get('offset', 0)
        self.group_by = self._extract_info.get('group_by', '')

        # 内部状态
        self._file_reader = None
        self._pages_list = []
        self._current_page = None
        self._total_rows = 0
        self._cached_df = None  # 缓存完整数据帧用于SQL查询

        # 使用localfile模型，配置来源固定为conn_conf
        self._config_source = 'conn_conf'

        # 初始化SQL规则构建器
        self.sql_rule_builder = SQLRuleBuilder(field_type_getter=self._get_field_type)

    def connect(self):
        """
        连接测试 - 验证文件是否存在且可读
        """
        try:
            if not self.file_path:
                return False, "文件路径不能为空"

            if not os.path.exists(self.file_path):
                return False, f"文件不存在: {self.file_path}"

            # 初始化文件读取器
            self._file_reader = FileReader(path=self.file_path)

            # 检查文件格式
            file_format = self._file_reader.get_format()
            if file_format not in self.SUPPORTED_FORMATS:
                return False, f"不支持的文件格式: {file_format}"

            # 获取文件页列表（对于多页文件如Excel）
            self._pages_list = self._file_reader.get_pages()
            print(f"Available pages: {self._pages_list}")

            # 如果指定了sheet_name，验证其有效性
            if self.sheet_name and self.sheet_name not in self._pages_list:
                return False, f"指定的sheet不存在: {self.sheet_name}. 可用的sheets: {self._pages_list}"

            # 解析筛选规则
            self.parse_extract_rules()

            return True, '连接成功'

        except Exception as e:
            print(f"连接失败: {str(e)}")
            return False, f"连接失败: {str(e)}"

    def get_info_prompt(self, model_prompt=''):
        """
        获取模型信息提示
        """
        info = f"""
本地文件数据模型（支持SQL筛选）
类型: {self.db_type}
# 使用示例：
实例化此类的 reader 对象，查询 SQL 转为 dataframe：
sql = 'select * from df limit 100'
df = reader.query(sql)
        """
        return info

    def get_connection_args(self):
        """
        获取连接参数定义
        """
        return {
            'file_path': {
                'type': 'string',
                'required': True,
                'description': '本地文件路径',
                'placeholder': '/path/to/file.csv'
            },
            'sheet_name': {
                'type': 'string',
                'required': False,
                'description': 'Excel工作表名称（仅对Excel文件有效）',
                'placeholder': 'Sheet1'
            },
            'encoding': {
                'type': 'string',
                'required': False,
                'description': '文件编码',
                'default': 'utf-8',
                'placeholder': 'utf-8'
            },
            'delimiter': {
                'type': 'string',
                'required': False,
                'description': 'CSV分隔符（仅对CSV文件有效）',
                'placeholder': ','
            }
        }

    def gen_models(self):
        """
        生成子数据模型（对于多页文件）
        """
        if not self._file_reader:
            self.connect()

        models = []
        for i, page_name in enumerate(self._pages_list):
            if page_name != 'main':  # 跳过默认的main页
                model_info = self.model_info.copy()
                model_info['source']['sheet_name'] = page_name
                model_info['model']['name'] = f"{self.name}_{page_name}"

                model = LocalFileModel(model_info)
                models.append({
                    'name': page_name,
                    'type': 'table',
                    'model': model
                })

        return models

    def get_res_fields(self) -> List[str]:
        """
        获取字段列表
        """
        try:
            df_sample = self._read_sample_data()
            if df_sample is not None and not df_sample.empty:
                return list(df_sample.columns)
            return []
        except Exception:
            return []

    def get_search_type_list(self):
        """
        获取可用高级查询类型
        """
        return [
            {'value': 'equals', 'label': '等于'},
            {'value': 'contains', 'label': '包含'},
            {'value': 'starts_with', 'label': '开始于'},
            {'value': 'ends_with', 'label': '结束于'},
            {'value': 'greater_than', 'label': '大于'},
            {'value': 'less_than', 'label': '小于'},
            {'value': 'is_null', 'label': '为空'},
            {'value': 'is_not_null', 'label': '不为空'}
        ]

    def get_extract_rules(self):
        """
        获取可筛选规则选项
        """
        fields = self.get_res_fields()
        rules = []

        for field in fields:
            rules.append({
                'field': field,
                'label': field,
                'type': 'string',  # 默认为字符串类型，可根据实际情况调整
                'operators': [
                    {'value': 'equals', 'label': '等于'},
                    {'value': 'contains', 'label': '包含'},
                    {'value': 'starts_with', 'label': '开始于'},
                    {'value': 'ends_with', 'label': '结束于'},
                    {'value': 'is_null', 'label': '为空'},
                    {'value': 'is_not_null', 'label': '不为空'}
                ]
            })

        return rules

    def parse_extract_rules(self):
        """
        解析筛选规则 - 支持SQL和规则转换
        """
        extract_rules = self._extract_info.get('extract_rules', {})

        if not extract_rules:
            return ""

        # 如果extract_rules包含完整的SQL查询
        if 'sql' in extract_rules:
            self.sql_query = extract_rules['sql']
            return self.sql_query

        # 解析各种筛选组件
        where_conditions = []

        # 解析字段条件
        if 'conditions' in extract_rules:
            conditions = extract_rules['conditions']
            if isinstance(conditions, list):
                for condition in conditions:
                    if isinstance(condition, dict):
                        field = condition.get('field', '')
                        operator = condition.get('operator', '=')
                        value = condition.get('value', '')

                        if field:
                            # 构建WHERE条件
                            if operator.lower() == 'contains':
                                where_conditions.append(f"CAST({field} AS VARCHAR) LIKE '%{value}%'")
                            elif operator.lower() == 'starts_with':
                                where_conditions.append(f"CAST({field} AS VARCHAR) LIKE '{value}%'")
                            elif operator.lower() == 'ends_with':
                                where_conditions.append(f"CAST({field} AS VARCHAR) LIKE '%{value}'")
                            elif operator.lower() == 'equals':
                                if isinstance(value, str):
                                    where_conditions.append(f"CAST({field} AS VARCHAR) = '{value}'")
                                else:
                                    where_conditions.append(f"{field} = {value}")
                            elif operator.lower() == 'greater_than':
                                where_conditions.append(f"{field} > {value}")
                            elif operator.lower() == 'less_than':
                                where_conditions.append(f"{field} < {value}")
                            elif operator.lower() == 'is_null':
                                where_conditions.append(f"{field} IS NULL")
                            elif operator.lower() == 'is_not_null':
                                where_conditions.append(f"{field} IS NOT NULL")

        # 组合WHERE条件
        if where_conditions:
            logic_operator = extract_rules.get('logic', 'AND')
            self.where_clause = f" {logic_operator} ".join(where_conditions)
        else:
            self.where_clause = extract_rules.get('where_clause', '')

        # 解析其他组件
        self.select_columns = extract_rules.get('select_columns', [])
        self.order_by = extract_rules.get('order_by', '')
        self.limit_count = extract_rules.get('limit')
        self.offset_count = extract_rules.get('offset', 0)
        self.group_by = extract_rules.get('group_by', '')

        return self.where_clause

    def query(self, sql=None, limit=1000, offset=0):
        """
        使用SQL查询数据，优先使用配置的SQL查询
        """
        try:
            # 读取原始数据
            read_kwargs = {}
            if self.encoding:
                read_kwargs['encoding'] = self.encoding
            if self.delimiter:
                read_kwargs['delimiter'] = self.delimiter
            if self.sheet_name:
                read_kwargs['page_name'] = self.sheet_name

            df = self._file_reader.get_page_content(**read_kwargs)

            if df is None or df.empty:
                return df

            # 如果有自定义SQL查询，优先使用
            if self.sql_query:
                return self._apply_sql_query(df, self.sql_query)

            # 如果传入SQL参数，使用它
            if sql:
                return self._apply_sql_query(df, sql)

            # 否则应用筛选条件
            filtered_df = self._apply_filters(df)

            # 应用分页限制
            if offset > 0:
                filtered_df = filtered_df.iloc[offset:]
            if limit is not None:
                filtered_df = filtered_df.head(limit)

            return filtered_df

        except Exception as e:
            print(f"查询数据失败: {str(e)}")
            return pd.DataFrame()

    def get_total_count(self):
        """
        获取符合条件的总记录数
        """
        try:
            # 读取原始数据
            read_kwargs = {}
            if self.encoding:
                read_kwargs['encoding'] = self.encoding
            if self.delimiter:
                read_kwargs['delimiter'] = self.delimiter
            if self.sheet_name:
                read_kwargs['page_name'] = self.sheet_name

            df = self._file_reader.get_page_content(**read_kwargs)

            if df is None or df.empty:
                return 0

            # 如果有完整SQL查询，需要计算总数
            if self.sql_query:
                # 尝试将SELECT部分改为COUNT(*)来获取总数
                count_sql = self.sql_query
                # 简单替换，实际使用中可能需要更复杂的SQL解析
                if count_sql.strip().upper().startswith('SELECT'):
                    # 找到FROM位置
                    from_pos = count_sql.upper().find(' FROM ')
                    if from_pos != -1:
                        count_sql = 'SELECT COUNT(*) as total' + count_sql[from_pos:]
                        # 移除ORDER BY和LIMIT
                        order_pos = count_sql.upper().find(' ORDER BY ')
                        if order_pos != -1:
                            count_sql = count_sql[:order_pos]
                        limit_pos = count_sql.upper().find(' LIMIT ')
                        if limit_pos != -1:
                            count_sql = count_sql[:limit_pos]

                        count_df = self._apply_sql_query(df, count_sql)
                        if not count_df.empty and 'total' in count_df.columns:
                            return int(count_df.iloc[0]['total'])

                # 如果SQL解析失败，返回筛选后的数据长度
                filtered_df = self._apply_sql_query(df, self.sql_query)
                return len(filtered_df)

            # 应用筛选条件并计数
            filtered_df = self._apply_filters(df)
            return len(filtered_df)

        except Exception as e:
            print(f"获取总记录数失败: {str(e)}")
            return 0

    def _get_field_type(self, field_name):
        """
        获取字段的数据类型（用于SQL规则构建器）
        """
        if not self._file_reader:
            return 'text'  # 默认文本类型

        try:
            # 获取样本数据来推断字段类型
            sample_df = self._read_sample_data(sample_size=10)
            if sample_df is None or sample_df.empty or field_name not in sample_df.columns:
                return 'text'

            # 根据pandas数据类型推断SQL类型
            dtype = sample_df[field_name].dtype
            if pd.api.types.is_integer_dtype(dtype):
                return 'int'
            elif pd.api.types.is_float_dtype(dtype):
                return 'float'
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                return 'datetime'
            elif pd.api.types.is_bool_dtype(dtype):
                return 'boolean'
            else:
                return 'text'

        except Exception:
            return 'text'  # 出错时默认为文本类型

    def gen_extract_rules(self):
        """
        生成筛选规则 - 使用统一的SQL规则构建器
        """
        return self.sql_rule_builder.build_sql_clauses(self.extract_rules)

    def get_supported_operators(self):
        """
        获取支持的筛选操作符列表（使用统一的SQL规则构建器）
        """
        return self.sql_rule_builder.get_supported_operators()

    def read_page(self, page: int = 1, pagesize: int = 20):
        """
        分页读取数据，若配置了SQL查询则禁止分页
        """
        try:
            # 如果有完整SQL查询，禁止分页返回所有数据
            if self.sql_query:
                df = self.query()
                data_li = df_to_list(df)
                res_data = {
                    'records': data_li,
                    'total': len(data_li),
                    'pagination': False  # 禁用分页
                }
                return True, gen_json_response(data=res_data)

            # 使用query方法进行分页查询
            offset = (page - 1) * pagesize
            df = self.query(limit=pagesize, offset=offset)

            # 获取总记录数
            total_count = self.get_total_count()

            # 转换为列表格式
            data_li = df_to_list(df)

            # 构建返回数据
            res_data = {
                'records': data_li,
                'total': total_count
            }

            return True, gen_json_response(data=res_data)

        except Exception as e:
            print(f"读取数据失败: {str(e)}")
            return False, str(e)

    def read_batch(self):
        """
        分批读取数据，若配置了SQL查询则禁止分页
        """
        try:
            # 如果有完整SQL查询，一次性返回所有数据
            if self.sql_query:
                df = self.query()
                if df.empty:
                    return
                data_li = df_to_list(df)
                batch_info = {
                    'records': data_li,
                    'total': len(data_li)
                }
                yield True, gen_json_response(data=batch_info)
                return

            # 获取总记录数
            total_count = self.get_total_count()
            processed_count = 0
            batch_num = 0

            offset = 0
            while True:
                df = self.query(limit=self.chunk_size, offset=offset)
                if df.empty:
                    break

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

                offset += self.chunk_size

                # 如果已经处理完所有数据，退出循环
                if processed_count >= total_count:
                    break

        except Exception as e:
            print(f"批量读取失败: {str(e)}")
            yield False, str(e)

    def _read_sample_data(self, sample_size: int = 100) -> Optional[pd.DataFrame]:
        """
        读取样本数据用于字段分析
        """
        try:
            if not self._file_reader:
                return None

            read_kwargs = {}
            if self.encoding:
                read_kwargs['encoding'] = self.encoding
            if self.delimiter:
                read_kwargs['delimiter'] = self.delimiter
            if self.sheet_name:
                read_kwargs['page_name'] = self.sheet_name

            df = self._file_reader.get_page_content(**read_kwargs)

            # 检查是否为None
            if df is None:
                return None

            # 返回样本数据
            if len(df) > sample_size:
                return df.head(sample_size)
            return df

        except Exception as e:
            print(f"读取样本数据失败: {str(e)}")
            return None

    def _apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        应用筛选规则 - 使用统一的SQL规则构建器
        """
        if df is None or df.empty:
            return df

        # 优先使用完整的SQL查询
        if self.sql_query:
            return self._apply_sql_query(df, self.sql_query)

        # 使用统一规则构建器
        extract_rules = self._extract_info.get('extract_rules', {})

        # 如果是条件列表格式，转换为规则并构建SQL
        if 'conditions' in extract_rules:
            where_clauses, order_clauses = self.gen_extract_rules()

            # 构建SQL查询
            sql_parts = []

            # SELECT子句
            if self.select_columns:
                clean_columns = self._sanitize_column_names(self.select_columns)
                if clean_columns:
                    sql_parts.append(f"SELECT {', '.join(clean_columns)}")
                else:
                    sql_parts.append("SELECT *")
            else:
                sql_parts.append("SELECT *")

            # FROM子句
            sql_parts.append("FROM df")

            # WHERE子句
            if where_clauses:
                sql_parts.append(f"WHERE {' AND '.join(where_clauses)}")

            # GROUP BY子句
            if self.group_by:
                sql_parts.append(f"GROUP BY {self.group_by}")

            # ORDER BY子句
            if self.order_by:
                sql_parts.append(f"ORDER BY {self.order_by}")
            elif order_clauses:
                sql_parts.append(f"ORDER BY {', '.join(order_clauses)}")

            # LIMIT和OFFSET子句
            if self.limit_count is not None:
                if self.offset_count > 0:
                    sql_parts.append(f"LIMIT {self.limit_count} OFFSET {self.offset_count}")
                else:
                    sql_parts.append(f"LIMIT {self.limit_count}")
            elif self.offset_count > 0:
                sql_parts.append(f"OFFSET {self.offset_count}")

            # 组合SQL查询
            constructed_query = " ".join(sql_parts)

            return self._apply_sql_query(df, constructed_query)

        # 如果有组件化配置，构建简单查询
        if self.where_clause or self.order_by or self.select_columns:
            sql_parts = []

            # SELECT子句
            if self.select_columns:
                clean_columns = self._sanitize_column_names(self.select_columns)
                if clean_columns:
                    sql_parts.append(f"SELECT {', '.join(clean_columns)}")
                else:
                    sql_parts.append("SELECT *")
            else:
                sql_parts.append("SELECT *")

            # FROM子句
            sql_parts.append("FROM df")

            # WHERE子句
            if self.where_clause:
                sql_parts.append(f"WHERE {self.where_clause}")

            # GROUP BY子句
            if self.group_by:
                sql_parts.append(f"GROUP BY {self.group_by}")

            # ORDER BY子句
            if self.order_by:
                sql_parts.append(f"ORDER BY {self.order_by}")

            # LIMIT和OFFSET子句
            if self.limit_count is not None:
                if self.offset_count > 0:
                    sql_parts.append(f"LIMIT {self.limit_count} OFFSET {self.offset_count}")
                else:
                    sql_parts.append(f"LIMIT {self.limit_count}")
            elif self.offset_count > 0:
                sql_parts.append(f"OFFSET {self.offset_count}")

            # 组合SQL查询
            constructed_query = " ".join(sql_parts)

            return self._apply_sql_query(df, constructed_query)

        # 没有筛选条件，返回原始数据
        return df

    def _apply_sql_query(self, df: pd.DataFrame, sql_query: str) -> pd.DataFrame:
        """
        使用DuckDB执行SQL查询
        """
        if not DUCKDB_AVAILABLE:
            print("警告: DuckDB未安装，无法执行SQL查询。返回原始数据。")
            return self._build_simple_filters(df)

        # 验证SQL安全性
        if not self._validate_sql_safety(sql_query):
            print("SQL查询安全性验证失败。返回原始数据。")
            return df

        try:
            # 创建DuckDB连接
            con = duckdb.connect(database=":memory:")

            # 注册DataFrame
            con.register('df', df)

            # 执行查询
            result_df = con.execute(sql_query).fetchdf()

            # 关闭连接
            con.close()

            return result_df

        except Exception as e:
            print(f"SQL查询执行失败: {sql_query}")
            print(f"错误: {str(e)}")
            print("尝试使用简单筛选，返回原始数据")
            return self._build_simple_filters(df)

    def _build_simple_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        构建简单的pandas筛选条件（当DuckDB不可用时的备选方案）
        """
        filtered_df = df.copy()

        # 应用简单的WHERE条件
        if self.where_clause:
            try:
                # 这里可以添加简单的WHERE条件解析
                # 目前只作为DuckDB不可用时的备选方案
                pass
            except Exception as e:
                print(f"简单筛选失败: {str(e)}")

        # 应用列选择
        if self.select_columns:
            try:
                available_columns = [col for col in self.select_columns if col in df.columns]
                if available_columns:
                    filtered_df = filtered_df[available_columns]
            except Exception as e:
                print(f"列选择失败: {str(e)}")

        # 应用排序
        if self.order_by:
            try:
                # 简单的ORDER BY解析
                order_parts = self.order_by.split(',')
                sort_columns = []
                ascending = []

                for part in order_parts:
                    part = part.strip()
                    if part.upper().endswith(' DESC'):
                        sort_columns.append(part[:-5].strip())
                        ascending.append(False)
                    else:
                        if part.upper().endswith(' ASC'):
                            part = part[:-4].strip()
                        sort_columns.append(part)
                        ascending.append(True)

                # 只对存在的列进行排序
                valid_columns = [col for col in sort_columns if col in filtered_df.columns]
                if valid_columns:
                    valid_ascending = [ascending[i] for i, col in enumerate(sort_columns) if col in filtered_df.columns]
                    filtered_df = filtered_df.sort_values(by=valid_columns, ascending=valid_ascending)

            except Exception as e:
                print(f"排序失败: {str(e)}")

        # 应用LIMIT和OFFSET
        if self.offset_count > 0:
            filtered_df = filtered_df.iloc[self.offset_count:]

        if self.limit_count is not None:
            filtered_df = filtered_df.head(self.limit_count)

        return filtered_df

    def _validate_sql_safety(self, sql_query: str) -> bool:
        """
        验证SQL查询的安全性（基础防护）
        """
        if not sql_query:
            return True

        # 检查危险的SQL关键字
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER',
            'TRUNCATE', 'EXEC', 'EXECUTE', 'UNION', 'MERGE', 'GRANT',
            'REVOKE', 'COMMIT', 'ROLLBACK', 'SAVEPOINT'
        ]

        sql_upper = sql_query.upper()

        for keyword in dangerous_keywords:
            if f' {keyword} ' in f' {sql_upper} ' or sql_upper.startswith(keyword):
                print(f"警告: 检测到潜在危险的SQL关键字: {keyword}")
                return False

        # 只允许SELECT查询
        if not sql_upper.strip().startswith('SELECT'):
            print("警告: 只允许SELECT查询")
            return False

        return True

    def _sanitize_column_names(self, columns: List[str]) -> List[str]:
        """
        清理列名，防止SQL注入
        """
        sanitized = []
        for col in columns:
            # 移除危险字符
            clean_col = str(col).strip()
            clean_col = ''.join(c for c in clean_col if c.isalnum() or c in '_')
            if clean_col:
                sanitized.append(clean_col)
        return sanitized

    def get_supported_sql_functions(self) -> List[str]:
        """
        获取支持的SQL函数列表（基于DuckDB）
        """
        if not DUCKDB_AVAILABLE:
            return []

        common_functions = [
            # 聚合函数
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
            # 字符串函数
            'UPPER', 'LOWER', 'LENGTH', 'TRIM', 'SUBSTRING', 'REPLACE',
            # 数学函数
            'ABS', 'ROUND', 'FLOOR', 'CEIL', 'SQRT',
            # 日期函数
            'CURRENT_DATE', 'CURRENT_TIME', 'CURRENT_TIMESTAMP',
            # 条件函数
            'CASE', 'COALESCE', 'NULLIF', 'ISNULL'
        ]
        return common_functions

    def write(self, res_data: List[Dict]) -> bool:
        """
        写入数据 - 本地文件模型主要设计为只读
        """
        print("本地文件模型暂不支持写入操作")
        return False

    def update(self, update_data: Dict, where_conditions: Dict) -> bool:
        """
        更新数据 - 本地文件模型主要设计为只读
        """
        print("本地文件模型暂不支持更新操作")
        return False

    def delete(self, where_conditions: Dict) -> bool:
        """
        删除数据 - 本地文件模型主要设计为只读
        """
        print("本地文件模型暂不支持删除操作")
        return False