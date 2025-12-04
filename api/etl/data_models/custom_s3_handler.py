# -*- coding: utf-8 -*-
"""
自定义S3兼容存储Handler
支持MinIO、DigitalOcean Spaces、阿里云OSS等S3兼容存储服务
使用自定义endpoint和连接参数
"""

from typing import List, Dict, Optional, Text
from contextlib import contextmanager

import boto3
import duckdb
from duckdb import HTTPException
from mindsdb_sql_parser import parse_sql
import pandas as pd
from botocore.client import Config
from botocore.exceptions import ClientError

from mindsdb_sql_parser.ast.base import ASTNode
from mindsdb_sql_parser.ast import Select, Identifier, Insert, Star, Constant

from mindsdb.utilities import log
from mindsdb.integrations.libs.response import (
    HandlerStatusResponse as StatusResponse,
    HandlerResponse as Response,
    RESPONSE_TYPE,
)

from mindsdb.integrations.libs.api_handler import APIResource, APIHandler
from mindsdb.integrations.utilities.sql_utils import FilterCondition, FilterOperator

logger = log.getLogger(__name__)


class ListFilesTable(APIResource):
    def list(
        self, targets: List[str] = None, conditions: List[FilterCondition] = None, limit: int = None, *args, **kwargs
    ) -> pd.DataFrame:
        buckets = None
        for condition in conditions:
            if condition.column == "bucket":
                if condition.op == FilterOperator.IN:
                    buckets = condition.value
                elif condition.op == FilterOperator.EQUAL:
                    buckets = [condition.value]
                condition.applied = True

        data = []
        for obj in self.handler.get_objects(limit=limit, buckets=buckets):
            path = obj["Key"]
            path = path.replace("`", "")
            item = {
                "path": path,
                "bucket": obj["Bucket"],
                "name": path[path.rfind("/") + 1 :],
                "extension": path[path.rfind(".") + 1 :],
            }

            if targets and "public_url" in targets:
                item["public_url"] = self.handler.generate_sas_url(path, obj["Bucket"])

            data.append(item)

        return pd.DataFrame(data=data, columns=self.get_columns())

    def get_columns(self) -> List[str]:
        return ["path", "name", "extension", "bucket", "content", "public_url"]


class FileTable(APIResource):
    def list(self, targets: List[str] = None, table_name=None, *args, **kwargs) -> pd.DataFrame:
        return self.handler.read_as_table(table_name)

    def add(self, data, table_name=None):
        df = pd.DataFrame(data)
        return self.handler.add_data_to_table(table_name, df)


class CustomS3Handler(APIHandler):
    """
    自定义S3兼容存储Handler
    支持连接MinIO、DigitalOcean Spaces、阿里云OSS等S3兼容存储服务
    """

    name = "custom_s3"
    supported_file_formats = ["csv", "tsv", "json", "parquet"]

    def __init__(self, name: Text, connection_data: Optional[Dict], **kwargs):
        """
        初始化Handler

        Args:
            name (Text): Handler实例名称
            connection_data (Dict): 连接数据
                - endpoint_url: S3兼容服务URL (例如: http://localhost:9000)
                - access_key: 访问密钥
                - secret_key: 秘密密钥
                - bucket: 存储桶名称
                - region: 区域 (可选)
                - verify_ssl: 是否验证SSL (可选)
            kwargs: 其他参数
        """
        super().__init__(name)
        self.connection_data = connection_data
        self.kwargs = kwargs

        self.connection = None
        self.is_connected = False
        self.thread_safe = True
        self.bucket = self.connection_data.get("bucket")
        self.endpoint_url = self.connection_data.get("endpoint_url")
        self.region = self.connection_data.get("region", "us-east-1")
        self.verify_ssl = self.connection_data.get("verify_ssl", True)
        self._regions = {}

        self._files_table = ListFilesTable(self)

    def __del__(self):
        if self.is_connected is True:
            self.disconnect()

    def connect(self):
        """
        建立到S3兼容存储的连接

        Raises:
            ValueError: 如果缺少必需的连接参数

        Returns:
            boto3.client: S3兼容存储的客户端对象
        """
        if self.is_connected is True:
            return self.connection

        # 验证必需参数
        if not all(key in self.connection_data for key in ["access_key", "secret_key", "endpoint_url"]):
            raise ValueError("Required parameters (endpoint_url, access_key, secret_key) must be provided.")

        # 连接S3并配置必需凭证
        self.connection = self._connect_boto3()
        self.is_connected = True

        return self.connection

    @contextmanager
    def _connect_duckdb(self, bucket):
        """
        创建能够连接到S3兼容存储的临时duckdb数据库
        必须作为上下文管理器使用

        Returns:
            DuckDBPyConnection
        """
        # 通过DuckDB连接到S3
        duckdb_conn = duckdb.connect(":memory:")
        try:
            duckdb_conn.execute("INSTALL httpfs")
        except HTTPException as http_error:
            logger.debug(f"Error installing the httpfs extension, {http_error}! Forcing installation.")
            duckdb_conn.execute("FORCE INSTALL httpfs")

        duckdb_conn.execute("LOAD httpfs")

        # 配置自定义凭证参数名
        duckdb_conn.execute(f"SET s3_access_key_id='{self.connection_data['access_key']}'")
        duckdb_conn.execute(f"SET s3_secret_access_key='{self.connection_data['secret_key']}'")

        # 配置endpoint_url
        duckdb_conn.execute(f"SET s3_endpoint='{self.connection_data['endpoint_url']}'")

        # 配置region
        region = self.connection_data.get("region", "us-east-1")
        duckdb_conn.execute(f"SET s3_region='{region}'")

        # 配置SSL验证
        verify_ssl = self.connection_data.get("verify_ssl", True)
        duckdb_conn.execute(f"SET s3_url_style='path'")

        try:
            yield duckdb_conn
        finally:
            duckdb_conn.close()

    def _connect_boto3(self) -> boto3.client:
        """
        建立到S3兼容存储的连接

        Returns:
            boto3.client: S3兼容存储的客户端对象
        """
        # 配置必需凭证
        config = {
            "aws_access_key_id": self.connection_data["access_key"],
            "aws_secret_access_key": self.connection_data["secret_key"],
            "endpoint_url": self.connection_data["endpoint_url"],
        }
        # 配置可选参数
        optional_parameters = ["region_name"]
        for parameter in optional_parameters:
            if parameter in self.connection_data:
                config[parameter] = self.connection_data[parameter]
        # 创建S3客户端
        client = boto3.client("s3", **config, config=Config(signature_version="s3v4"))

        # 检查连接
        if self.bucket is not None:
            try:
                client.head_bucket(Bucket=self.bucket)
            except ClientError as e:
                logger.error(f"Error connecting to bucket {self.bucket}: {e}")
                raise
        else:
            try:
                client.list_buckets()
            except ClientError as e:
                logger.error(f"Error listing buckets: {e}")
                raise

        return client

    def disconnect(self):
        """
        关闭到S3兼容存储的连接（如果当前处于打开状态）
        """
        if not self.is_connected:
            return
        if hasattr(self.connection, 'close'):
            self.connection.close()
        self.is_connected = False

    def check_connection(self) -> StatusResponse:
        """
        检查到S3兼容存储的连接状态

        Returns:
            StatusResponse: 包含成功状态和错误消息（如果发生错误）的对象
        """
        response = StatusResponse(False)
        need_to_close = self.is_connected is False

        # 通过boto3检查连接
        try:
            self._connect_boto3()
            response.success = True
        except (ClientError, ValueError) as e:
            logger.error(f"Error connecting to S3 compatible storage with the given credentials, {e}!")
            response.error_message = str(e)

        if response.success and need_to_close:
            self.disconnect()

        elif not response.success and self.is_connected:
            self.is_connected = False

        return response

    def _get_bucket(self, key):
        if self.bucket is not None:
            return self.bucket, key

        # 从key的第一部分获取bucket
        ar = key.split("/")
        return ar[0], "/".join(ar[1:])

    def read_as_table(self, key) -> pd.DataFrame:
        """
        将对象读取为dataframe。使用duckdb
        """
        bucket, key = self._get_bucket(key)

        with self._connect_duckdb(bucket) as connection:
            # 使用自定义endpoint的s3路径
            s3_path = f"s3://{bucket}/{key}"
            cursor = connection.execute(f"SELECT * FROM '{s3_path}'")

            return cursor.fetchdf()

    def _read_as_content(self, key) -> None:
        """
        将对象读取为内容
        """
        bucket, key = self._get_bucket(key)

        client = self.connect()

        obj = client.get_object(Bucket=bucket, Key=key)
        content = obj["Body"].read()
        return content

    def add_data_to_table(self, key, df) -> None:
        """
        将表写入S3兼容存储中的文件

        Raises:
            CatalogException: 如果表在DuckDB连接中不存在
        """
        # 检查文件是否存在于S3兼容存储中
        bucket, key = self._get_bucket(key)

        try:
            client = self.connect()
            client.head_object(Bucket=bucket, Key=key)
        except ClientError as e:
            logger.error(f"Error querying the file {key} in the bucket {bucket}, {e}!")
            raise e

        with self._connect_duckdb(bucket) as connection:
            # 复制
            connection.execute(f"CREATE TABLE tmp_table AS SELECT * FROM 's3://{bucket}/{key}'")

            # 插入
            connection.execute("INSERT INTO tmp_table BY NAME SELECT * FROM df")

            # 上传
            connection.execute(f"COPY tmp_table TO 's3://{bucket}/{key}'")

    def query(self, query: ASTNode) -> Response:
        """
        执行由ASTNode表示的SQL查询并检索数据

        Args:
            query (ASTNode): 表示要执行的SQL查询的ASTNode

        Raises:
            ValueError: 如果文件格式不受支持或文件在S3兼容存储中不存在

        Returns:
            Response: 包含查询结果或错误消息的响应对象
        """
        self.connect()

        if isinstance(query, Select):
            table_name = query.from_table.parts[-1]

            if table_name == "files":
                table = self._files_table
                df = table.select(query)

                # 添加内容
                has_content = False
                for target in query.targets:
                    if isinstance(target, Identifier) and target.parts[-1].lower() == "content":
                        has_content = True
                        break
                if has_content:
                    df["content"] = df["path"].apply(self._read_as_content)
            else:
                extension = table_name.split(".")[-1]
                if extension not in self.supported_file_formats:
                    logger.error(f"The file format {extension} is not supported!")
                    raise ValueError(f"The file format {extension} is not supported!")

                table = FileTable(self, table_name=table_name)
                df = table.select(query)

            response = Response(RESPONSE_TYPE.TABLE, data_frame=df)
        elif isinstance(query, Insert):
            table_name = query.table.parts[-1]
            table = FileTable(self, table_name=table_name)
            table.insert(query)
            response = Response(RESPONSE_TYPE.OK)
        else:
            raise NotImplementedError

        return response

    def native_query(self, query: str) -> Response:
        """
        执行SQL查询并返回结果

        Args:
            query (str): 要执行的SQL查询

        Returns:
            Response: 包含查询结果或错误消息的响应对象
        """
        query_ast = parse_sql(query)
        return self.query(query_ast)

    def get_objects(self, limit=None, buckets=None) -> List[dict]:
        client = self.connect()
        if self.bucket is not None:
            add_bucket_to_name = False
            scan_buckets = [self.bucket]
        else:
            add_bucket_to_name = True
            scan_buckets = [b["Name"] for b in client.list_buckets()["Buckets"]]

        objects = []
        for bucket in scan_buckets:
            if buckets is not None and bucket not in buckets:
                continue

            try:
                resp = client.list_objects_v2(Bucket=bucket)
            except ClientError as e:
                logger.error(f"Error listing objects in bucket {bucket}: {e}")
                continue

            if "Contents" not in resp:
                continue

            for obj in resp["Contents"]:
                if obj.get("StorageClass", "STANDARD") != "STANDARD":
                    continue

                obj["Bucket"] = bucket
                if add_bucket_to_name:
                    # bucket是名称的一部分
                    obj["Key"] = f"{bucket}/{obj['Key']}"
                objects.append(obj)
            if limit is not None and len(objects) >= limit:
                break

        return objects

    def generate_sas_url(self, key: str, bucket: str) -> str:
        """
        生成用于访问S3兼容存储中对象的预签名URL

        Args:
            key (str): S3兼容存储中对象的键（路径）
            bucket (str): 存储桶的名称

        Returns:
            str: 用于访问对象的预签名URL
        """
        client = self.connect()
        url = client.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=3600)
        return url

    def get_tables(self) -> Response:
        """
        检索S3兼容存储中的表（对象）列表

        每个对象都被视为一个表。只有受支持的文件格式才被视为表。

        Returns:
            Response: 包含表和视图列表的响应对象，按照`Response`类的格式
        """
        # 仅获取受支持的文件格式
        # 用反引号包装对象名称以防止SQL语法错误
        supported_names = [
            f"`{obj['Key']}`" for obj in self.get_objects() if obj["Key"].split(".")[-1] in self.supported_file_formats
        ]

        # 带文件列表的虚拟表
        supported_names.insert(0, "files")

        response = Response(RESPONSE_TYPE.TABLE, data_frame=pd.DataFrame(supported_names, columns=["table_name"]))

        return response

    def get_columns(self, table_name: str) -> Response:
        """
        检索S3兼容存储中指定表（对象）的列详细信息

        Args:
            table_name (Text): 要检索列信息的表的名称

        Raises:
            ValueError: 如果'table_name'不是有效字符串

        Returns:
            Response: 包含列详细信息的响应对象，按照`Response`类的格式
        """
        query = Select(targets=[Star()], from_table=Identifier(parts=[table_name]), limit=Constant(1))

        result = self.query(query)

        response = Response(
            RESPONSE_TYPE.TABLE,
            data_frame=pd.DataFrame(
                {
                    "column_name": result.data_frame.columns,
                    "data_type": [
                        data_type if data_type != "object" else "string" for data_type in result.data_frame.dtypes
                    ],
                }
            ),
        )

        return response
