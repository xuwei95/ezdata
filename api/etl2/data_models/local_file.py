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
        # 支持多种字段名: 'path' 或 'file_path'
        self.file_path = self.conn_conf.get('path')
        self.sheet_name = self.conn_conf.get('sheet_name')
        self.encoding = self.conn_conf.get('encoding') or 'utf-8'  # 默认编码
        self.delimiter = self.conn_conf.get('delimiter')

        # 从extract_info中获取批处理大小
        self.chunk_size = self._extract_info.get('batch_size', 1000)

        # SQL筛选配置 - 从extract_info中获取
        self.sql_query = self._extract_info.get('sql', '')
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
            'path': {
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
            success, message = self.connect()
            if not success:
                print(f"无法连接到文件: {message}")
                return []

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

    def get_extract_rules(self):
        """
        获取可筛选项
        """
        # 使用统一规则构建器获取操作符
        return self.sql_rule_builder.get_supported_operators()

    def get_search_type_list(self):
        """
        获取可用高级查询类型
        """
        return [{
            'name': 'sql',
            'value': 'sql',
            "default": 'select * from df limit 100'
        }]

    def query(self, sql=None, limit=1000, offset=0):
        """
        智能SQL查询数据

        优先级：
        1. 如果传入SQL参数，直接执行
        2. 如果配置了self.sql_query，执行配置的SQL查询
        3. 如果没有完整SQL，使用筛选规则拼接SQL查询
        4. 最后作为备选，应用pandas筛选条件
        """
        print(f"执行查询 - 传入SQL: {sql}, 配置SQL: {self.sql_query}")

        try:
            # 确保文件读取器已初始化
            if not self._file_reader:
                print("文件读取器未初始化，正在尝试连接...")
                success, message = self.connect()
                if not success:
                    print(f"连接失败: {message}")
                    return pd.DataFrame()

            # 构建读取参数
            read_kwargs = {}
            if self.encoding:
                read_kwargs['encoding'] = self.encoding
            if self.delimiter:
                read_kwargs['delimiter'] = self.delimiter
            if self.sheet_name:
                read_kwargs['page_name'] = self.sheet_name

            # 读取原始数据
            print("正在读取文件数据...")
            df = self._file_reader.get_page_content(**read_kwargs)

            if df is None or df.empty:
                print("文件数据为空")
                return df

            print(f"成功读取 {len(df)} 行数据")

            # 确定要执行的SQL查询
            target_sql = None

            # 1. 优先使用传入的SQL参数
            if sql and sql.strip():
                target_sql = sql.strip()
                print(f"使用传入的SQL查询: {target_sql}")

            # 2. 使用配置的SQL查询
            elif self.sql_query and self.sql_query.strip():
                target_sql = self.sql_query.strip()
                print(f"使用配置的SQL查询: {target_sql}")

            # 3. 没有完整SQL时，尝试从筛选规则构建SQL
            else:
                print("未发现完整SQL，尝试从筛选规则构建...")
                target_sql = self._build_sql_from_filters()
                if target_sql:
                    print(f"从筛选规则构建SQL: {target_sql}")
                else:
                    print("无筛选条件，返回原始数据")

            # 执行查询
            if target_sql:
                # 在SQL中添加分页逻辑（如果没有的话）
                final_sql = self._add_pagination_to_sql(target_sql, limit, offset)
                result_df = self._apply_sql_query(df, final_sql)
                print(f"SQL查询完成，返回 {len(result_df)} 行数据")
                return result_df
            else:
                # 没有SQL查询时，应用传统的pandas筛选
                print("使用pandas筛选方式...")
                filtered_df = self._apply_filters(df)

                # 应用分页
                if offset > 0:
                    filtered_df = filtered_df.iloc[offset:]
                if limit is not None:
                    filtered_df = filtered_df.head(limit)

                print(f"pandas筛选完成，返回 {len(filtered_df)} 行数据")
                return filtered_df

        except Exception as e:
            print(f"查询数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def _build_sql_from_filters(self) -> Optional[str]:
        """
        从筛选规则构建SQL查询

        Returns:
            构造的SQL查询字符串，如果没有筛选规则则返回None
        """
        try:
            extract_rules = self._extract_info.get('extract_rules', {})

            # 如果有完整的SQL规则，直接使用
            if 'sql' in extract_rules and extract_rules['sql']:
                return extract_rules['sql'].strip()

            # 如果有条件列表，使用规则构建器
            if 'conditions' in extract_rules and extract_rules['conditions']:
                # 使用现有的规则构建逻辑
                where_clauses, order_clauses = self.gen_extract_rules()

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

                # 组合SQL查询
                return " ".join(sql_parts)

            # 如果有组件化配置，使用简单规则
            if self.where_clause or self.order_by or self.select_columns or self.group_by:
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

                # 组合SQL查询
                return " ".join(sql_parts)

            # 没有筛选规则
            return None

        except Exception as e:
            print(f"构建SQL查询失败: {str(e)}")
            return None

    def _add_pagination_to_sql(self, sql: str, limit: Optional[int], offset: int) -> str:
        """
        向SQL查询添加分页逻辑（如果尚未包含）

        Args:
            sql: 原始SQL查询
            limit: 限制数量
            offset: 偏移量

        Returns:
            添加了分页的SQL查询
        """
        sql_upper = sql.upper().strip()

        # 检查是否已有LIMIT或OFFSET
        has_limit = ' LIMIT ' in f' {sql_upper} '
        has_offset = ' OFFSET ' in f' {sql_upper} '

        # 如果已经有完整的LIMIT子句，不添加
        if has_limit and has_offset:
            return sql

        # 如果有LIMIT但没有OFFSET，添加OFFSET
        if has_limit and not has_offset and offset > 0:
            # 简单替换，在LIMIT后添加OFFSET
            return sql + f' OFFSET {offset}'

        # 如果没有LIMIT或OFFSET，添加它们
        if not has_limit and not has_offset:
            # 如果limit不为None，添加LIMIT
            if limit is not None and limit > 0:
                if offset > 0:
                    return sql + f' LIMIT {limit} OFFSET {offset}'
                else:
                    return sql + f' LIMIT {limit}'
            elif offset > 0:
                return sql + f' OFFSET {offset}'

        return sql

    def get_total_count(self):
        """
        获取符合条件的总记录数
        优先使用优化的SQL查询逻辑
        """
        try:
            # 确保文件读取器已初始化
            if not self._file_reader:
                success, message = self.connect()
                if not success:
                    return 0

            # 构建读取参数
            read_kwargs = {}
            if self.encoding:
                read_kwargs['encoding'] = self.encoding
            if self.delimiter:
                read_kwargs['delimiter'] = self.delimiter
            if self.sheet_name:
                read_kwargs['page_name'] = self.sheet_name

            # 读取原始数据
            df = self._file_reader.get_page_content(**read_kwargs)

            if df is None or df.empty:
                return 0

            # 确定要执行的SQL查询
            target_sql = None

            # 1. 使用配置的SQL查询
            if self.sql_query and self.sql_query.strip():
                target_sql = self.sql_query.strip()
                print(f"使用配置的SQL查询计算总数: {target_sql}")

            # 2. 尝试从筛选规则构建SQL
            else:
                target_sql = self._build_sql_from_filters()
                if target_sql:
                    print(f"从筛选规则构建SQL计算总数: {target_sql}")

            # 执行查询并计算总数
            if target_sql:
                # 尝试将查询转换为COUNT查询
                if target_sql.strip().upper().startswith('SELECT'):
                    # 找到FROM位置
                    from_pos = target_sql.upper().find(' FROM ')
                    if from_pos != -1:
                        count_sql = 'SELECT COUNT(*) as total' + target_sql[from_pos:]
                        # 移除ORDER BY和LIMIT
                        order_pos = count_sql.upper().find(' ORDER BY ')
                        if order_pos != -1:
                            count_sql = count_sql[:order_pos]
                        limit_pos = count_sql.upper().find(' LIMIT ')
                        if limit_pos != -1:
                            count_sql = count_sql[:limit_pos]

                        try:
                            count_df = self._apply_sql_query(df, count_sql)
                            if not count_df.empty and 'total' in count_df.columns:
                                return int(count_df.iloc[0]['total'])
                        except Exception as e:
                            print(f"COUNT查询失败，使用原查询: {e}")

                # 如果COUNT转换失败，执行原查询并计数
                try:
                    result_df = self._apply_sql_query(df, target_sql)
                    return len(result_df)
                except Exception as e:
                    print(f"SQL查询失败，使用pandas筛选: {e}")

            # 如果没有SQL查询，使用pandas筛选并计数
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
                'total': total_count,
                'pagination': False if self.sql_query else True
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