# -*- coding: utf-8 -*-
"""
自定义S3兼容存储数据模型
支持连接MinIO、DigitalOcean Spaces、阿里云OSS等S3兼容存储服务
使用host:port配置方式，简化配置参数
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from etl2.data_models import DataModel
from etl2.utils.mindsdb_client import IntegrationsClient, StandaloneHandler
from etl2.utils.sql_rule_builder import SQLRuleBuilder
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

        self.client = IntegrationsClient()
        self.handler = None
        self.standalone_handler = None
        self.table_columns = []

        # 初始化SQL规则构建器
        self.sql_rule_builder = SQLRuleBuilder(field_type_getter=self._get_field_type)

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
            # 'use_ssl': {
            #     'type': 'boolean',
            #     'required': False,
            #     'description': '是否使用SSL',
            #     'default': False
            # },
            # 'verify_ssl': {
            #     'type': 'boolean',
            #     'required': False,
            #     'description': '是否验证SSL证书',
            #     'default': True
            # }
        }

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

            # 构建连接配置 - 使用自定义handler
            connection_data = {
                'endpoint_url': self.endpoint_url,
                'access_key': self.access_key,
                'secret_key': self.secret_key,
                'bucket': self.bucket_name,
                'region': self.region,
                'verify_ssl': self.verify_ssl
            }

            # 使用自定义s3 handler
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
                columns_df = self.standalone_handler.get_columns(self.table_name)
                if not columns_df.empty:
                    self.table_columns = columns_df.to_dict('records')
                    return True, 'success'
                return False, f'object {self.table_name} not found'
            else:
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
        if sql is None:
            where_clauses, order_clauses = self.gen_extract_rules()
            sql = f"SELECT * FROM {self.table_name if self.table_name else 's3_object'}"
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            if order_clauses:
                sql += " ORDER BY " + ", ".join(order_clauses)
        sql += f" LIMIT {limit} OFFSET {offset}"
        return self.standalone_handler.native_query(sql)

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
            count_sql = f"SELECT COUNT(*) as total FROM {self.table_name if self.table_name else 's3_object'}"
            if where_clauses:
                count_sql += " WHERE " + " AND ".join(where_clauses)

            count_df = self.standalone_handler.native_query(count_sql)
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
        获取存储对象的详细统计信息
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
                'column_count': len(self.table_columns) if self.table_columns else 0,
                'endpoint': self.endpoint_url,
                'bucket': self.bucket_name
            }
            return info
        except Exception as e:
            logger.error(f"获取表信息失败: {str(e)}")
            return None

    def disconnect(self):
        if self.standalone_handler:
            try:
                self.standalone_handler.disconnect()
            except:
                pass

    def __del__(self):
        self.disconnect()
