"""统一存储入口。

按 StorageConfig.storage_type 选择后端，对外暴露 save/load/download/exists/delete 及 get_download_url。
支持的后端：local / s3 / oci-storage / aliyun-oss / azure-blob / google-storage / tencent-cos。
云后端的 SDK 仅在选用对应 storage_type 时才会被导入（见 requirements-storage.txt），local/s3 部署无需安装。
模块加载时实例化单例 `storage` 供业务层使用。
"""

from collections.abc import Generator

from config.env import StorageConfig, UploadConfig
from utils.storage.local_storage import LocalStorage


def _build_conf() -> dict:
    """从 pydantic StorageConfig 构建后端所需的大写键配置字典。"""
    c = StorageConfig
    return {
        'STORAGE_TYPE': c.storage_type,
        'STORAGE_LOCAL_PATH': c.storage_local_path,
        'STORAGE_PUBLIC_ENDPOINT': c.storage_public_endpoint,
        # s3 / minio
        'S3_ENDPOINT': c.s3_endpoint,
        'S3_BUCKET_NAME': c.s3_bucket_name,
        'S3_ACCESS_KEY': c.s3_access_key,
        'S3_SECRET_KEY': c.s3_secret_key,
        'S3_REGION': c.s3_region,
        'S3_ADDRESS_STYLE': c.s3_address_style,
        'S3_USE_AWS_MANAGED_IAM': c.s3_use_aws_managed_iam,
        # oracle oci（s3 兼容）
        'OCI_ENDPOINT': c.oci_endpoint,
        'OCI_BUCKET_NAME': c.oci_bucket_name,
        'OCI_ACCESS_KEY': c.oci_access_key,
        'OCI_SECRET_KEY': c.oci_secret_key,
        'OCI_REGION': c.oci_region,
        # aliyun oss
        'ALIYUN_OSS_ENDPOINT': c.aliyun_oss_endpoint,
        'ALIYUN_OSS_BUCKET_NAME': c.aliyun_oss_bucket_name,
        'ALIYUN_OSS_ACCESS_KEY': c.aliyun_oss_access_key,
        'ALIYUN_OSS_SECRET_KEY': c.aliyun_oss_secret_key,
        'ALIYUN_OSS_REGION': c.aliyun_oss_region,
        'ALIYUN_OSS_AUTH_VERSION': c.aliyun_oss_auth_version,
        # azure blob
        'AZURE_BLOB_ACCOUNT_URL': c.azure_blob_account_url,
        'AZURE_BLOB_CONTAINER_NAME': c.azure_blob_container_name,
        'AZURE_BLOB_ACCOUNT_NAME': c.azure_blob_account_name,
        'AZURE_BLOB_ACCOUNT_KEY': c.azure_blob_account_key,
        # google storage
        'GOOGLE_STORAGE_BUCKET_NAME': c.google_storage_bucket_name,
        'GOOGLE_STORAGE_SERVICE_ACCOUNT_JSON_BASE64': c.google_storage_service_account_json_base64,
        # tencent cos
        'TENCENT_COS_BUCKET_NAME': c.tencent_cos_bucket_name,
        'TENCENT_COS_REGION': c.tencent_cos_region,
        'TENCENT_COS_SECRET_ID': c.tencent_cos_secret_id,
        'TENCENT_COS_SECRET_KEY': c.tencent_cos_secret_key,
        'TENCENT_COS_SCHEME': c.tencent_cos_scheme,
    }


def _build_runner(storage_type: str, conf: dict):
    """按 storage_type 惰性导入并实例化后端（未选用的云后端无需安装其 SDK）。"""
    if storage_type == 's3':
        from utils.storage.s3_storage import S3Storage

        return S3Storage(conf)
    if storage_type == 'oci-storage':
        from utils.storage.oci_storage import OCIStorage

        return OCIStorage(conf)
    if storage_type == 'aliyun-oss':
        from utils.storage.aliyun_storage import AliyunStorage

        return AliyunStorage(conf)
    if storage_type == 'azure-blob':
        from utils.storage.azure_storage import AzureStorage

        return AzureStorage(conf)
    if storage_type == 'google-storage':
        from utils.storage.google_storage import GoogleStorage

        return GoogleStorage(conf)
    if storage_type == 'tencent-cos':
        from utils.storage.tencent_storage import TencentStorage

        return TencentStorage(conf)
    return LocalStorage(conf)


class Storage:
    def __init__(self):
        self.conf = _build_conf()
        self.storage_type = self.conf.get('STORAGE_TYPE', 'local')
        self.storage_runner = _build_runner(self.storage_type, self.conf)

    def save(self, filename, data):
        self.storage_runner.save(filename, data)

    def load(self, filename: str, stream: bool = False) -> bytes | Generator:
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
        """返回对象的可访问 URL。

        优先使用 STORAGE_PUBLIC_ENDPOINT（用户提供的、浏览器可达的完整前缀）；
        未设置时按各后端给出最佳推断地址。
        """
        c = self.conf
        public = c.get('STORAGE_PUBLIC_ENDPOINT')
        if public:
            return f'{public.rstrip("/")}/{filename}'

        t = self.storage_type
        if t == 's3':
            return f'{c.get("S3_ENDPOINT")}/{c.get("S3_BUCKET_NAME")}/{filename}'
        if t == 'oci-storage':
            return f'{c.get("OCI_ENDPOINT")}/{c.get("OCI_BUCKET_NAME")}/{filename}'
        if t == 'aliyun-oss':
            # endpoint 形如 oss-cn-hangzhou.aliyuncs.com（不含 scheme）
            return f'https://{c.get("ALIYUN_OSS_BUCKET_NAME")}.{c.get("ALIYUN_OSS_ENDPOINT")}/{filename}'
        if t == 'azure-blob':
            return f'{str(c.get("AZURE_BLOB_ACCOUNT_URL")).rstrip("/")}/{c.get("AZURE_BLOB_CONTAINER_NAME")}/{filename}'
        if t == 'google-storage':
            return f'https://storage.googleapis.com/{c.get("GOOGLE_STORAGE_BUCKET_NAME")}/{filename}'
        if t == 'tencent-cos':
            return (
                f'https://{c.get("TENCENT_COS_BUCKET_NAME")}.cos.{c.get("TENCENT_COS_REGION")}.myqcloud.com/{filename}'
            )
        # local
        return f'{UploadConfig.UPLOAD_PREFIX}/{filename}'

    def exists(self, filename):
        return self.storage_runner.exists(filename)

    def delete(self, filename):
        return self.storage_runner.delete(filename)


# 模块级单例
storage = Storage()
