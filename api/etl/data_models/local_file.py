# -*- coding: utf-8 -*-
"""
本地文件数据模型
基于mindsdb file handler实现本地文件读取
"""

import os
import pandas as pd
from typing import List, Dict, Optional

from mindsdb.integrations.utilities.files.file_reader import FileReader
from mindsdb.integrations.handlers.file_handler.file_handler import FileHandler
from etl.data_models import DataModel
from etl.utils.mindsdb_client import IntegrationsClient
from utils.common_utils import gen_json_response, df_to_list
from mindsdb.utilities.context import context as ctx
import logging

logger = logging.getLogger(__name__)


class SimpleFileController:
    """
    简单的文件控制器，用于单个文件的管理
    """

    def __init__(self, file_path: str, sheet_name: Optional[str] = None,
                 encoding: str = 'utf-8', delimiter: Optional[str] = None):
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.encoding = encoding
        self.delimiter = delimiter
        self._file_reader = FileReader(path=file_path)
        self._cached_data = None

    def get_file_data(self, table_name: str, page_name: Optional[str] = None) -> pd.DataFrame:
        """获取文件数据"""
        # 构建读取参数
        read_kwargs = {}
        if self.encoding:
            read_kwargs['encoding'] = self.encoding
        if self.delimiter:
            read_kwargs['delimiter'] = self.delimiter

        # 使用传入的 page_name 或默认的 sheet_name
        target_page = page_name if page_name else self.sheet_name
        if target_page:
            read_kwargs['page_name'] = target_page

        # 读取文件数据
        df = self._file_reader.get_page_content(**read_kwargs)
        return df if df is not None else pd.DataFrame()

    def get_files(self) -> List[Dict]:
        """获取文件列表"""
        df = self.get_file_data('main')
        return [{
            'name': 'main',
            'row_count': len(df),
            'columns': list(df.columns) if not df.empty else []
        }]

    def get_files_names(self) -> List[str]:
        """获取文件名列表"""
        return ['main']

    def get_file_meta(self, table_name: str) -> Dict:
        """获取文件元数据"""
        df = self.get_file_data(table_name)
        return {
            'name': table_name,
            'columns': list(df.columns) if not df.empty else [],
            'row_count': len(df)
        }


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
        self.file_path = self.conn_conf.get('path')
        self.sheet_name = self.conn_conf.get('sheet_name')
        self.encoding = self.conn_conf.get('encoding') or 'utf-8'  # 默认编码
        self.delimiter = self.conn_conf.get('delimiter')

        # 从extract_info中获取批处理大小
        self.chunk_size = self._extract_info.get('batch_size', 1000)
        self.sql_query = ''
        self.default_sql = 'select * from main'
        try:
            # 初始化客户端（启用缓存）
            self.client = IntegrationsClient(enable_cache=True, cache_ttl=300)
        except Exception as e:
            # 如果无法设置 context，则禁用缓存
            raise e
            self.client = IntegrationsClient(enable_cache=False, cache_ttl=300)
        # 内部状态
        self._file_reader = None
        self._file_controller = None
        self._file_handler = None
        self._pages_list = []
        self._current_page = None
        self._total_rows = 0
        self._cached_df = None  # 缓存完整数据帧用于SQL查询

    @classmethod
    def get_form_config(cls):
        '''
        获取本地文件模型的配置表单schema
        '''
        return [
            {
                'label': '允许操作',
                'field': 'auth_type',
                'component': 'JCheckbox',
                'default': 'query,extract',
                'componentProps': {
                    'options': [
                        {'label': '查询', 'value': 'query'},
                        {'label': '数据抽取', 'value': 'extract'}
                    ]
                }
            }
        ]

    def _get_handler_cache_key(self):
        """
        生成 handler 的缓存键
        """
        import hashlib
        import json

        # 使用文件路径和相关配置生成缓存键
        cache_data = {
            'file_path': self.file_path,
            'sheet_name': self.sheet_name,
            'encoding': self.encoding,
            'delimiter': self.delimiter
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_str.encode()).hexdigest()

        return f"local_file:{cache_hash}"

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

            # 初始化文件控制器
            self._file_controller = SimpleFileController(
                file_path=self.file_path,
                sheet_name=self.sheet_name,
                encoding=self.encoding,
                delimiter=self.delimiter
            )

            # 尝试从缓存获取 FileHandler
            if self.client.enable_cache and IntegrationsClient._handlers_cache is not None:
                cache_key = self._get_handler_cache_key()
                cached_handler = IntegrationsClient._handlers_cache.get(cache_key)

                if cached_handler is not None:
                    logger.debug(f"从缓存获取 local_file handler: {cache_key}")
                    self._file_handler = cached_handler
                    # 更新 file_controller（因为可能已经改变）
                    self._file_handler.file_controller = self._file_controller
                else:
                    # 缓存中没有，创建新的 FileHandler
                    logger.debug(f"创建新的 local_file handler: {cache_key}")
                    self._file_handler = FileHandler(
                        name='file',
                        file_controller=self._file_controller
                    )
                    # 将新创建的 handler 放入缓存
                    original_name = self._file_handler.name
                    self._file_handler.name = cache_key
                    IntegrationsClient._handlers_cache.set(self._file_handler)
                    self._file_handler.name = original_name  # 恢复原始名称
            else:
                # 没有启用缓存，直接创建新的 FileHandler
                self._file_handler = FileHandler(
                    name='file',
                    file_controller=self._file_controller
                )

            return True, '连接成功'

        except Exception as e:
            print(f"连接失败: {str(e)}")
            return False, f"连接失败: {str(e)}"

    def get_info_prompt(self, model_prompt=''):
        """
        获取模型信息提示
        """
        df = self.query()
        info = f"""
本地文件数据模型
# 使用示例：
实例化此类的 reader 对象转为 dataframe：
df = reader.query()
# DataSource type:
{self.db_type}
# MetaData:
<dataframe>
{df.shape[0]}x{df.shape[1]}\n{df.head(3).to_csv()}
</dataframe>
        """
        return info

    @staticmethod
    def get_connection_args():
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

    def get_res_fields(self):
        """
        获取字段列表
        """
        try:
            # 确保文件读取器已初始化
            if not self._file_reader:
                success, message = self.connect()
                if not success:
                    return []

            # 构建读取参数
            read_kwargs = {}
            if self.encoding:
                read_kwargs['encoding'] = self.encoding
            if self.delimiter:
                read_kwargs['delimiter'] = self.delimiter
            if self.sheet_name:
                read_kwargs['page_name'] = self.sheet_name

            # 读取原始数据（只读取少量样本）
            df = self._file_reader.get_page_content(**read_kwargs)

            if df is None or df.empty:
                return []

            # 构建字段列表
            fields = []
            for col_name in df.columns:
                field_dic = {
                    'field_name': col_name,
                    'field_value': col_name,
                    'ext_params': {}
                }
                fields.append(field_dic)

            return fields

        except Exception as e:
            print(f"获取字段列表失败: {str(e)}")
            return []

    def get_extract_rules(self):
        """
        获取可筛选项 - 文件模型不支持筛选规则
        """
        return []

    def get_search_type_list(self):
        """
        获取可用高级查询类型
        """
        return [{
            'name': 'sql',
            'value': 'sql',
            "default": 'select * from main'
        }]

    def query(self, sql=None, limit=10000, offset=0):
        """
        SQL查询数据

        优先级：
        1. 如果传入SQL参数，直接执行
        2. 如果配置了self.sql_query，执行配置的SQL查询
        3. 返回所有数据（带分页）
        """
        print(f"执行查询 - 传入SQL: {sql}, 配置SQL: {self.sql_query}")

        try:
            # 确保文件读取器已初始化
            if not self._file_reader:
                print("文件读取器未初始化，正在尝试连接...")
                success, message = self.connect()
                if not success:
                    raise RuntimeError(f"连接失败: {message}")

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

            # 执行查询
            if target_sql:
                # 在SQL中添加分页逻辑（如果没有的话）
                final_sql = self._add_pagination_to_sql(target_sql, limit, offset)
                result_df = self._apply_sql_query(final_sql)
                print(f"SQL查询完成，返回 {len(result_df)} 行数据")
                return result_df
            else:
                # 没有SQL查询时，读取原始数据并应用分页
                print("没有SQL查询，读取原始数据...")

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
                    print("文件数据为空")
                    return pd.DataFrame()

                print(f"成功读取 {len(df)} 行数据")

                # 应用分页
                result_df = df.copy()
                if offset > 0:
                    result_df = result_df.iloc[offset:]
                if limit is not None:
                    result_df = result_df.head(limit)

                print(f"返回 {len(result_df)} 行数据")
                return result_df

        except Exception as e:
            raise RuntimeError(f"查询数据失败: {str(e)}")


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
        """
        try:
            # 确保文件读取器已初始化
            if not self._file_reader:
                success, message = self.connect()
                if not success:
                    return 0

            # 确定要执行的SQL查询
            target_sql = None

            # 使用配置的SQL查询
            if self.sql_query and self.sql_query.strip():
                target_sql = self.sql_query.strip()
                print(f"使用配置的SQL查询计算总数: {target_sql}")

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
                            count_df = self._apply_sql_query(count_sql)
                            if not count_df.empty and 'total' in count_df.columns:
                                return int(count_df.iloc[0]['total'])
                        except Exception as e:
                            print(f"COUNT查询失败，使用原查询: {e}")

                # 如果COUNT转换失败，执行原查询并计数
                try:
                    result_df = self._apply_sql_query(target_sql)
                    return len(result_df)
                except Exception as e:
                    print(f"SQL查询失败: {e}")

            # 如果没有SQL查询，读取所有数据并返回总行数
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

            return len(df)

        except Exception as e:
            print(f"获取总记录数失败: {str(e)}")
            return 0

    def gen_extract_rules(self):
        """
        解析SQL查询规则
        """
        sql_rules = [i for i in self.extract_rules if i['field'] == 'search_text' and i['rule'] == 'sql' and i['value']]
        if sql_rules:
            sql = sql_rules[0].get('value')
            if sql != self.default_sql:
                self.sql_query = sql

    def read_page(self, page: int = 1, pagesize: int = 20):
        """
        分页读取数据，若配置了SQL查询则禁止分页
        """
        try:
            self.gen_extract_rules()
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
        self.gen_extract_rules()
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


    def _normalize_sql_for_chinese_columns(self, sql_query: str) -> str:
        """
        处理SQL中的中文字段名，添加反引号

        Args:
            sql_query: 原始SQL查询

        Returns:
            str: 处理后的SQL查询
        """
        try:
            # 获取所有字段名
            if not self._file_controller:
                return sql_query

            meta = self._file_controller.get_file_meta('main')
            columns = meta.get('columns', [])

            if not columns:
                return sql_query

            import re

            # 对每个字段名进行处理，按长度从长到短排序（避免短字段名被先替换导致长字段名匹配失败）
            sorted_columns = sorted(columns, key=lambda x: len(str(x)), reverse=True)

            for col_name in sorted_columns:
                if not col_name:
                    continue

                # 检查字段名是否包含中文或特殊字符（需要引号保护）
                needs_quotes = (
                    re.search(r'[\u4e00-\u9fff]', col_name) or  # 中文
                    ' ' in col_name or  # 空格
                    '-' in col_name or  # 连字符
                    not col_name[0].isalpha()  # 不以字母开头
                )

                if needs_quotes:
                    # 检查字段名是否已经被引号包裹
                    if f'`{col_name}`' in sql_query or f'"{col_name}"' in sql_query or f"'{col_name}'" in sql_query:
                        continue

                    # 使用正则表达式替换未被引号包裹的字段名
                    # 匹配字段名，但不在字符串常量内（避免替换'xxx'或"xxx"内的内容）
                    escaped_col = re.escape(col_name)

                    # 构建匹配模式：
                    # 1. 前面不是引号、反引号
                    # 2. 后面是空白、逗号、比较运算符、FROM、WHERE等关键字，或字符串结尾
                    pattern = rf'(?<![`"\'])({escaped_col})(?![`"\'])(?=\s|,|=|>|<|!=|>=|<=|\s+FROM|\s+WHERE|\s+ORDER|\s+LIMIT|\s+OFFSET|$)'

                    # 替换为带反引号的字段名
                    sql_query = re.sub(pattern, rf'`{col_name}`', sql_query, flags=re.IGNORECASE)

            return sql_query

        except Exception as e:
            print(f"处理中文字段名失败: {e}")
            import traceback
            traceback.print_exc()
            return sql_query

    def _apply_sql_query(self, sql_query: str) -> pd.DataFrame:
        """
        使用 MindsDB file handler 执行 SQL 查询

        Args:
            sql_query: SQL查询语句

        Returns:
            pd.DataFrame: 查询结果
        """
        if not self._file_handler:
            print("错误: FileHandler 未初始化")
            return pd.DataFrame()

        try:
            # 处理中文字段名
            sql_query = self._normalize_sql_for_chinese_columns(sql_query)

            # 如果有 sheet_name，使用 main.sheet_name 格式
            if self.sheet_name:
                sql_query = sql_query.replace('FROM main', f'FROM main.{self.sheet_name}')

            print(f"执行 SQL 查询: {sql_query}")

            # 使用 FileHandler 的 native_query 方法（接受字符串参数）
            response = self._file_handler.native_query(sql_query)

            if response.error_message:
                print(f"查询失败: {response.error_message}")
                return pd.DataFrame()

            result_df = response.data_frame

            if result_df is None or result_df.empty:
                print("查询返回空结果")
                return pd.DataFrame()

            print(f"MindsDB FileHandler 查询成功: 返回 {len(result_df)} 行数据")
            return result_df

        except Exception as e:
            print(f"SQL查询执行失败: {sql_query}")
            print(f"错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def disconnect(self):
        """
        断开连接（由于使用了缓存，实际上不会真正断开连接）

        缓存系统会自动管理连接的生命周期，在 TTL 过期后自动断开。
        这里只是清理本地引用。
        """
        # 不要调用 disconnect()，因为连接被缓存管理
        # 只清理本地引用
        self._file_handler = None
        self._file_controller = None
        self._file_reader = None

    def __del__(self):
        # 清理引用，但不断开连接
        self._file_handler = None
        self._file_controller = None
        self._file_reader = None
