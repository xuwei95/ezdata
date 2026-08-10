"""S3 兼容对象存储实现（AWS S3 / MinIO 等，MinIO 走 S3 协议）。

注：boto3 在本模块顶部导入；storage_utils 仅在 STORAGE_TYPE=s3 时才导入本模块，
因此 local 部署无需安装 boto3。
"""

from collections.abc import Generator
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from utils.storage.base_storage import BaseStorage


class S3Storage(BaseStorage):
    """S3 存储实现。"""

    def __init__(self, app_config: dict):
        super().__init__(app_config)
        self.bucket_name = app_config.get('S3_BUCKET_NAME')
        if app_config.get('S3_USE_AWS_MANAGED_IAM'):
            session = boto3.Session()
            self.client = session.client('s3')
        else:
            self.client = boto3.client(
                's3',
                aws_secret_access_key=app_config.get('S3_SECRET_KEY'),
                aws_access_key_id=app_config.get('S3_ACCESS_KEY'),
                endpoint_url=app_config.get('S3_ENDPOINT'),
                region_name=app_config.get('S3_REGION'),
                config=Config(s3={'addressing_style': app_config.get('S3_ADDRESS_STYLE')}),
            )

    def save(self, filename, data):
        self.client.put_object(Bucket=self.bucket_name, Key=filename, Body=data)

    def save_fileobj(self, filename: str, fileobj: BinaryIO) -> None:
        # upload_fileobj 支持自动分片上传，内存占用恒定
        self.client.upload_fileobj(fileobj, self.bucket_name, filename)

    def load_once(self, filename: str) -> bytes:
        # 注意:self.client 为共享单例,不能 closing() 关闭,否则后续操作需重连(偶发变慢/报错)
        try:
            return self.client.get_object(Bucket=self.bucket_name, Key=filename)['Body'].read()
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError('File not found')
            raise

    def load_stream(self, filename: str) -> Generator:
        def generate(filename: str = filename) -> Generator:
            try:
                response = self.client.get_object(Bucket=self.bucket_name, Key=filename)
                yield from response['Body'].iter_chunks()
            except ClientError as ex:
                if ex.response['Error']['Code'] == 'NoSuchKey':
                    raise FileNotFoundError('File not found')
                raise

        return generate()

    def load_range(self, filename: str, start: int = 0, length: int | None = None) -> Generator:
        if start < 0 or (length is not None and length < 0):
            raise ValueError('文件读取范围不合法')
        if length is None:
            byte_range = f'bytes={start}-'
        elif length == 0:

            def _empty() -> Generator:
                return
                yield  # pragma: no cover

            return _empty()
        else:
            byte_range = f'bytes={start}-{start + length - 1}'

        def generate(byte_range: str = byte_range) -> Generator:
            try:
                response = self.client.get_object(Bucket=self.bucket_name, Key=filename, Range=byte_range)
            except ClientError as ex:
                if ex.response['Error']['Code'] in {'NoSuchKey', '404'}:
                    raise FileNotFoundError('File not found') from ex
                raise
            yield from response['Body'].iter_chunks()

        return generate()

    def stat(self, filename: str) -> int:
        try:
            return self.client.head_object(Bucket=self.bucket_name, Key=filename)['ContentLength']
        except ClientError as ex:
            if ex.response['Error']['Code'] in {'NoSuchKey', '404'}:
                raise FileNotFoundError('File not found') from ex
            raise

    def download(self, filename, target_filepath):
        self.client.download_file(self.bucket_name, filename, target_filepath)

    def exists(self, filename):
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=filename)
            return True
        except Exception:
            return False

    def delete(self, filename):
        self.client.delete_object(Bucket=self.bucket_name, Key=filename)
