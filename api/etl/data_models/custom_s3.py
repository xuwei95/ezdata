# -*- coding: utf-8 -*-
"""
自定义S3兼容存储数据模型
支持连接MinIO、DigitalOcean Spaces、阿里云OSS等S3兼容存储服务
使用host:port配置方式，简化配置参数
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from etl.data_models import DataModel
from etl.utils.mindsdb_client import IntegrationsClient, StandaloneHandler
from utils.common_utils import gen_json_response, df_to_list
from .custom_s3_handler import CustomS3Handler
import logging

logger = logging.getLogger(__name__)


class CustomS3Model(DataModel):
    """
    自定义S3兼容存储模型
    支持MinIO、DigitalOcean Spaces、阿里云OSS等S3兼容存储服务
    使用host:port方式配置，无需AWS前缀
    """

    name = "custom_s3"

    def __init__(self, model_info):
        super().__init__(model_info)
        self.db_type = self._source.get('type', 'custom_s3')
        self.conn_conf = self._source.get('conn_conf', {})
        model_conf = self._model.get('model_conf', {})
        self.table_name = model_conf.get('name', '')
        self.auth_types = model_conf.get('auth_type', '').split(',')

        # 记录配置信息
        logger.info(f"Custom S3 模型初始化 - 表名: '{self.table_name}', model_conf: {model_conf}")

        # S3连接配置
        self.host = self.conn_conf.get('host', '')
        self.port = self.conn_conf.get('port', 9000)
        self.access_key = self.conn_conf.get('access_key', '')
        self.secret_key = self.conn_conf.get('secret_key', '')
        self.bucket_name = self.conn_conf.get('bucket_name', '')
        self.region = self.conn_conf.get('region', 'us-east-1')
        self.use_ssl = self.conn_conf.get('use_ssl', False)
        self.verify_ssl = self.conn_conf.get('verify_ssl', True)

        # 构建endpoint_url
        protocol = 'https' if self.use_ssl else 'http'
        self.endpoint_url = f"{protocol}://{self.host}:{self.port}"

        # 初始化客户端（启用缓存）
        self.client = IntegrationsClient(enable_cache=True, cache_ttl=300)
        self.handler = None
        self.standalone_handler = None
        self.table_columns = []
        # SQL查询相关
        self.sql_query = ''
        self.default_sql = f'select * from s3_datasource.`{self.table_name}`'

    @classmethod
    def get_form_config(cls):
        '''
        获取自定义S3模型的配置表单schema
        '''
        return [
            {
                'label': '表名/对象名',
                'field': 'name',
                'required': True,
                'component': 'Input',
                'default': '',
                'componentProps': {
                    'placeholder': '例如: my-data-table 或 folder/file.csv'
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
                        {'label': '数据抽取', 'value': 'extract'}
                    ]
                }
            }
        ]

    @staticmethod
    def get_connection_args():
        """
        获取连接参数定义
        """
        return {
            'host': {
                'type': 'string',
                'required': True,
                'description': 'S3兼容服务的主机地址',
                'placeholder': '例如: localhost (MinIO), s3.amazonaws.com (AWS S3), spaces.digitalocean.com (DO Spaces)'
            },
            'port': {
                'type': 'number',
                'required': True,
                'description': '端口号',
                'default': 9000,
                'componentProps': {
                    'min': 1,
                    'max': 65535
                }
            },
            'access_key': {
                'type': 'string',
                'required': True,
                'description': '访问密钥（Access Key）',
                'placeholder': '输入access_key'
            },
            'secret_key': {
                'type': 'string',
                'required': True,
                'description': '秘密密钥（Secret Key）',
                'placeholder': '输入secret_key'
            },
            'bucket_name': {
                'type': 'string',
                'required': True,
                'description': '存储桶名称',
                'placeholder': '输入bucket名称'
            },
            'region': {
                'type': 'string',
                'required': False,
                'description': '区域（可选）',
                'default': 'us-east-1',
                'placeholder': '例如: us-east-1, ap-northeast-1'
            },
            'use_ssl': {
                'type': 'boolean',
                'required': False,
                'description': '是否使用SSL',
                'default': False
            },
            'verify_ssl': {
                'type': 'boolean',
                'required': False,
                'description': '是否验证SSL证书',
                'default': True
            }
        }

    def _get_handler_cache_key(self, connection_data):
        """
        生成 handler 的缓存键
        """
        import hashlib
        import json

        # 将连接数据转换为 JSON 字符串并计算哈希
        conn_str = json.dumps(connection_data, sort_keys=True)
        conn_hash = hashlib.md5(conn_str.encode()).hexdigest()

        cache_key = f"custom_s3:{conn_hash}"
        logger.debug(f"生成缓存键: {cache_key}, connection_data: {connection_data}")
        return cache_key

    def connect(self):
        try:
            # 验证必需参数
            if not self.host:
                return False, "host不能为空"
            if not self.access_key:
                return False, "access_key不能为空"
            if not self.secret_key:
                return False, "secret_key不能为空"
            if not self.bucket_name:
                return False, "bucket_name不能为空"

            # 构建连接配置
            connection_data = {
                'endpoint_url': self.endpoint_url,
                'access_key': self.access_key,
                'secret_key': self.secret_key,
                'bucket': self.bucket_name,
                'region': self.region,
                'verify_ssl': self.verify_ssl
            }

            # 优先从缓存获取 handler
            if self.client.enable_cache and IntegrationsClient._handlers_cache is not None:
                cache_key = self._get_handler_cache_key(connection_data)
                cached_handler = IntegrationsClient._handlers_cache.get(cache_key)

                if cached_handler is not None:
                    logger.info(f"从缓存获取 custom_s3 handler: {cache_key}")
                    self.handler = cached_handler

                    # 使用缓存的 handler 创建 standalone_handler
                    self.standalone_handler = StandaloneHandler(self.handler)

                    # 获取表/对象信息
                    if self.table_name:
                        try:
                            columns_df = self.standalone_handler.get_columns(self.table_name)
                            if not columns_df.empty:
                                self.table_columns = columns_df.to_dict('records')
                                logger.info(f"成功使用缓存的 handler，缓存键: {cache_key}")
                                return True, 'success (使用缓存)'
                            return False, f'object {self.table_name} not found'
                        except Exception as e:
                            # 缓存的连接可能已失效，清除缓存并重新创建
                            logger.warning(f"使用缓存的 handler 失败: {str(e)}，清除缓存并重新创建")
                            IntegrationsClient._handlers_cache.delete(cache_key)
                            # 继续下面的流程创建新的 handler
                    else:
                        logger.info(f"成功使用缓存的 handler，缓存键: {cache_key}")
                        return True, 'success (使用缓存)'

            # 缓存未命中或未启用缓存，创建新的 handler
            logger.info(f"创建新的 custom_s3 handler")
            self.handler = CustomS3Handler(
                name='custom_s3_handler',
                connection_data=connection_data
            )

            self.standalone_handler = StandaloneHandler(self.handler)
            status = self.standalone_handler.check_connection()
            if not status.get('success'):
                return False, status.get('error_message', 'connect failed')

            # 获取表/对象信息
            if self.table_name:
                # 验证表名是否包含文件扩展名
                if '.' not in self.table_name:
                    logger.warning(f"表名 '{self.table_name}' 可能缺少文件扩展名。建议使用完整文件名，如 'data.csv'")

                # 验证文件扩展名是否支持
                extension = self.table_name.split(".")[-1] if "." in self.table_name else ""
                supported_formats = ["csv", "tsv", "json", "parquet"]
                if extension and extension not in supported_formats:
                    return False, f"不支持的文件格式 '{extension}'。支持的格式: {', '.join(supported_formats)}"

                try:
                    columns_df = self.standalone_handler.get_columns(self.table_name)
                    if not columns_df.empty:
                        self.table_columns = columns_df.to_dict('records')
                    else:
                        return False, f'object {self.table_name} not found in bucket {self.bucket_name}'
                except Exception as e:
                    error_msg = f'获取对象 {self.table_name} 的列信息失败: {str(e)}'
                    logger.error(error_msg)
                    logger.error(f'提示: 1) 确保文件名包含扩展名（如 data.csv）; 2) 确保文件存在于 bucket {self.bucket_name} 中')
                    return False, error_msg

            # 如果启用了缓存，将新创建的 handler 放入缓存
            if self.client.enable_cache and IntegrationsClient._handlers_cache is not None:
                cache_key = self._get_handler_cache_key(connection_data)
                logger.info(f"准备将 handler 放入缓存，缓存键: {cache_key}")
                original_name = self.handler.name
                self.handler.name = cache_key
                logger.info(f"设置 handler.name 为缓存键: {cache_key}, thread_safe: {getattr(self.handler, 'thread_safe', True)}")
                IntegrationsClient._handlers_cache.set(self.handler)
                self.handler.name = original_name  # 恢复原始名称
                logger.info(f"已将 custom_s3 handler 放入缓存: {cache_key}")
                logger.info(f"缓存设置后，缓存中的所有键: {list(IntegrationsClient._handlers_cache.handlers.keys())}")

            return True, 'success'

        except Exception as e:
            return False, str(e)

    def get_info_prompt(self, model_prompt=''):
        """
        获取使用提示及存储服务元数据信息
        """
        if not self.standalone_handler:
            self.connect()
        try:
            info_prompt = f"""
一个基于 MindsDB S3 Handler 的自定义S3兼容存储模型
支持连接MinIO、DigitalOcean Spaces、阿里云OSS等S3兼容存储服务

# 使用示例：
实例化此类的 reader 对象，查询 SQL 转为 dataframe：
df = reader.query(sql)

# 字段信息：
{self.table_columns}
            """
            return info_prompt
        except Exception as e:
            logger.error(f"获取元数据信息失败: {e}")
            return f"Custom S3 Compatible Storage Model for {self.endpoint_url}"

    def get_res_fields(self):
        if not self.table_columns:
            flag, msg = self.connect()
            if not flag:
                return []
        fields = []
        for col in self.table_columns:
            col_name = col.get('COLUMN_NAME') or col.get('column_name') or col.get('name')
            if col_name:
                fields.append({'field_name': col_name, 'field_value': col_name})
        return fields

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
            "default": f'select * from s3_datasource.`{self.table_name}`'
        }]

    def gen_extract_rules(self):
        """
        解析筛选规则，优先使用SQL查询，否则使用统一的SQL规则构建器
        """
        # 首先检查是否有SQL查询规则
        sql_rules = [i for i in self.extract_rules if i['field'] == 'search_text' and i['rule'] == 'sql' and i['value']]
        if sql_rules:
            sql = sql_rules[0].get('value')
            if sql != self.default_sql:
                self.sql_query = sql
                logger.info(f"使用自定义SQL查询: {self.sql_query}")

    def query(self, sql=None, limit=1000, offset=0):
        """
        SQL查询数据

        优先级：
        1. 如果传入SQL参数，直接执行
        2. 如果配置了self.sql_query，执行配置的SQL查询
        3. 构建默认查询（带筛选条件和分页）
        """
        logger.info(f"执行查询 - 传入SQL: {sql}, 配置SQL: {self.sql_query}")

        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                raise RuntimeError(f'connect failed: {msg}')
        try:
            # 确定要执行的SQL查询
            target_sql = None

            # 1. 优先使用传入的SQL参数
            if sql and sql.strip():
                target_sql = sql.strip()
                logger.info(f"使用传入的SQL查询: {target_sql}")

            # 2. 使用配置的SQL查询
            elif self.sql_query and self.sql_query.strip():
                target_sql = self.sql_query.strip()
                logger.info(f"使用配置的SQL查询: {target_sql}")

            # 执行查询
            if target_sql:
                # 在SQL中添加分页逻辑（如果没有的话）
                final_sql = self._add_pagination_to_sql(target_sql, limit, offset)
                result_df = self._apply_sql_query(final_sql)
                logger.info(f"SQL查询完成，返回 {len(result_df)} 行数据")
                return result_df
            else:
                # 没有SQL查询时，构建默认查询
                logger.info("没有SQL查询，构建默认查询...")

                # 使用配置的表名（应该是完整的文件名，如 data.csv）
                table_name_for_query = self.table_name if self.table_name else 's3_object'
                logger.info(f"Custom S3 查询使用的表名: '{table_name_for_query}'")

                # 验证表名是否包含扩展名
                if self.table_name and '.' not in self.table_name:
                    error_msg = f"表名 '{self.table_name}' 缺少文件扩展名。请在数据源配置中将表名设置为完整文件名，如 'data.csv'"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                default_sql = f"SELECT * FROM s3_datasource.`{table_name_for_query}`"
                # 添加分页
                default_sql += f" LIMIT {limit} OFFSET {offset}"
                logger.info(f"执行默认查询: {default_sql}")
                return self.standalone_handler.native_query(default_sql)

        except Exception as e:
            logger.error(f"查询数据失败: {str(e)}")
            raise RuntimeError(f"查询数据失败: {str(e)}")

    def _add_pagination_to_sql(self, sql: str, limit: int, offset: int) -> str:
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
            return sql + f' OFFSET {offset}'

        # 如果没有LIMIT或OFFSET，添加它们
        if not has_limit and not has_offset:
            if limit is not None and limit > 0:
                if offset > 0:
                    return sql + f' LIMIT {limit} OFFSET {offset}'
                else:
                    return sql + f' LIMIT {limit}'
            elif offset > 0:
                return sql + f' OFFSET {offset}'

        return sql

    def _apply_sql_query(self, sql_query: str):
        """
        执行SQL查询并返回结果

        Args:
            sql_query: SQL查询语句

        Returns:
            pd.DataFrame: 查询结果
        """
        if not self.standalone_handler:
            logger.error("错误: StandaloneHandler 未初始化")
            raise RuntimeError("StandaloneHandler 未初始化")

        try:
            logger.info(f"执行 SQL 查询: {sql_query}")
            result_df = self.standalone_handler.native_query(sql_query)
            logger.info(f"SQL查询成功: 返回 {len(result_df)} 行数据")
            return result_df
        except Exception as e:
            logger.error(f"SQL查询执行失败: {sql_query}")
            logger.error(f"错误: {str(e)}")
            raise RuntimeError(f"SQL查询执行失败: {str(e)}")

    def read_page(self, page=1, pagesize=20):
        self.gen_extract_rules()
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                return False, msg
        try:
            # 查询数据
            df = self.query()
            data_li = df_to_list(df)

            # 获取总记录数
            total_count = len(data_li)

            res_data = {
                'records': data_li,
                'total': total_count,
                'pagination': False  # 禁用分页
            }
            return True, gen_json_response(data=res_data)
        except Exception as e:
            logger.error(f"读取分页数据失败: {str(e)}")
            return False, str(e)

    def read_batch(self):
        self.gen_extract_rules()
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                yield False, msg
                return
        try:
            df = self.query()
            data_li = df_to_list(df)
            total = len(data_li)

            res_data = {
                'records': data_li,
                'total': total
            }
            yield True, gen_json_response(data=res_data)

        except Exception as e:
            logger.error(f"批量读取数据失败: {str(e)}")
            yield False, str(e)

    def get_table_info(self):
        """
        获取存储对象的详细统计信息
        """
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                return None

        try:
            info = {
                'table_name': self.table_name,
                'columns': self.table_columns,
                'column_count': len(self.table_columns) if self.table_columns else 0,
            }
            return info
        except Exception as e:
            logger.error(f"获取表信息失败: {str(e)}")
            return None

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
