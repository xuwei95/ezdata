"""统一存储入口。

按 StorageConfig.storage_type 选择后端（local / s3），对外暴露 save/load/download/exists/delete
及 get_download_url。模块加载时实例化单例 `storage` 供业务层使用。

旧 ezdata 的多后端（aliyun/azure/google/tencent/oci）实现可按需补充到 utils/storage/ 后在此分发。
"""
from collections.abc import Generator
from typing import Union

from config.env import StorageConfig, UploadConfig
from utils.storage.local_storage import LocalStorage


def _build_conf() -> dict:
    """从 pydantic StorageConfig 构建后端所需的大写键配置字典。"""
    return {
        'STORAGE_TYPE': StorageConfig.storage_type,
        'STORAGE_LOCAL_PATH': StorageConfig.storage_local_path,
        'STORAGE_PUBLIC_ENDPOINT': StorageConfig.storage_public_endpoint,
        'S3_ENDPOINT': StorageConfig.s3_endpoint,
        'S3_BUCKET_NAME': StorageConfig.s3_bucket_name,
        'S3_ACCESS_KEY': StorageConfig.s3_access_key,
        'S3_SECRET_KEY': StorageConfig.s3_secret_key,
        'S3_REGION': StorageConfig.s3_region,
        'S3_ADDRESS_STYLE': StorageConfig.s3_address_style,
        'S3_USE_AWS_MANAGED_IAM': StorageConfig.s3_use_aws_managed_iam,
    }


class Storage:
    def __init__(self):
        self.conf = _build_conf()
        self.storage_type = self.conf.get('STORAGE_TYPE', 'local')
        if self.storage_type == 's3':
            # 延迟导入：未启用 s3 时无需安装 boto3
            from utils.storage.s3_storage import S3Storage

            self.storage_runner = S3Storage(self.conf)
        else:
            self.storage_runner = LocalStorage(self.conf)

    def save(self, filename, data):
        self.storage_runner.save(filename, data)

    def load(self, filename: str, stream: bool = False) -> Union[bytes, Generator]:
        if stream:
            return self.load_stream(filename)
        return self.load_once(filename)

    def load_once(self, filename: str) -> bytes:
        return self.storage_runner.load_once(filename)

    def load_stream(self, filename: str) -> Generator:
        return self.storage_runner.load_stream(filename)

    def download(self, filename, target_filepath):
        self.storage_runner.download(filename, target_filepath)

    def get_download_url(self, filename: str) -> str:
        public = self.conf.get('STORAGE_PUBLIC_ENDPOINT')
        if self.storage_type == 's3':
            base = public or self.conf.get('S3_ENDPOINT')
            return f"{base}/{self.conf.get('S3_BUCKET_NAME')}/{filename}"
        base = public or UploadConfig.UPLOAD_PREFIX
        return f'{base}/{filename}'

    def exists(self, filename):
        return self.storage_runner.exists(filename)

    def delete(self, filename):
        return self.storage_runner.delete(filename)


# 模块级单例
storage = Storage()
