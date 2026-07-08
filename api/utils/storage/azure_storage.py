"""Azure Blob 存储实现（storage_type=azure-blob）。依赖：azure-storage-blob

说明：原 ezdata 用 redis 缓存 SAS token；本模板存储层为同步调用，这里改为每次构建客户端时
生成 SAS token（generate_account_sas 为本地计算，开销很小），去除对 redis 的依赖。
"""

from collections.abc import Generator
from datetime import datetime, timedelta, timezone

from azure.storage.blob import AccountSasPermissions, BlobServiceClient, ResourceTypes, generate_account_sas

from utils.storage.base_storage import BaseStorage


class AzureStorage(BaseStorage):
    """Implementation for azure blob storage."""

    def __init__(self, app_config: dict):
        super().__init__(app_config)
        self.bucket_name = app_config.get('AZURE_BLOB_CONTAINER_NAME')
        self.account_url = app_config.get('AZURE_BLOB_ACCOUNT_URL')
        self.account_name = app_config.get('AZURE_BLOB_ACCOUNT_NAME')
        self.account_key = app_config.get('AZURE_BLOB_ACCOUNT_KEY')

    def save(self, filename, data):
        client = self._sync_client()
        blob_container = client.get_container_client(container=self.bucket_name)
        blob_container.upload_blob(filename, data)

    def load_once(self, filename: str) -> bytes:
        client = self._sync_client()
        blob = client.get_container_client(container=self.bucket_name)
        blob = blob.get_blob_client(blob=filename)
        return blob.download_blob().readall()

    def load_stream(self, filename: str) -> Generator:
        client = self._sync_client()

        def generate(filename: str = filename) -> Generator:
            blob = client.get_blob_client(container=self.bucket_name, blob=filename)
            blob_data = blob.download_blob()
            yield from blob_data.chunks()

        return generate(filename)

    def download(self, filename, target_filepath):
        client = self._sync_client()
        blob = client.get_blob_client(container=self.bucket_name, blob=filename)
        with open(target_filepath, 'wb') as my_blob:
            blob.download_blob().readinto(my_blob)

    def exists(self, filename):
        client = self._sync_client()
        blob = client.get_blob_client(container=self.bucket_name, blob=filename)
        return blob.exists()

    def delete(self, filename):
        client = self._sync_client()
        blob_container = client.get_container_client(container=self.bucket_name)
        blob_container.delete_blob(filename)

    def _sync_client(self) -> 'BlobServiceClient':
        sas_token = generate_account_sas(
            account_name=self.account_name,
            account_key=self.account_key,
            resource_types=ResourceTypes(service=True, container=True, object=True),
            permission=AccountSasPermissions(read=True, write=True, delete=True, list=True, add=True, create=True),
            expiry=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1),
        )
        return BlobServiceClient(account_url=self.account_url, credential=sas_token)
