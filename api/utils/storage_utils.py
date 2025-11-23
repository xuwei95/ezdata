from collections.abc import Generator
from typing import Union
# from utils.storage.aliyun_storage import AliyunStorage
# from utils.storage.azure_storage import AzureStorage
# from utils.storage.google_storage import GoogleStorage
from utils.storage.local_storage import LocalStorage
# from utils.storage.oci_storage import OCIStorage
from utils.storage.s3_storage import S3Storage
# from utils.storage.tencent_storage import TencentStorage
from config import SYS_CONF


class Storage:
    def __init__(self):
        self.storage_type = SYS_CONF.get('STORAGE_TYPE', 'local')
        if self.storage_type == 's3':
            self.storage_runner = S3Storage(SYS_CONF)
        # elif storage_type == 'azure-blob':
        #     self.storage_runner = AzureStorage(
        #         app=app
        #     )
        # elif storage_type == 'aliyun-oss':
        #     self.storage_runner = AliyunStorage(
        #         app=app
        #     )
        # elif storage_type == 'google-storage':
        #     self.storage_runner = GoogleStorage(
        #         app=app
        #     )
        # elif storage_type == 'tencent-cos':
        #     self.storage_runner = TencentStorage(
        #         app=app
        #     )
        # elif storage_type == 'oci-storage':
        #     self.storage_runner = OCIStorage(
        #         app=app
        #     )
        else:
            self.storage_runner = LocalStorage(SYS_CONF)

    def save(self, filename, data):
        self.storage_runner.save(filename, data)

    def load(self, filename: str, stream: bool = False) -> Union[bytes, Generator]:
        if stream:
            return self.load_stream(filename)
        else:
            return self.load_once(filename)

    def load_once(self, filename: str) -> bytes:
        return self.storage_runner.load_once(filename)

    def load_stream(self, filename: str) -> Generator:
        return self.storage_runner.load_stream(filename)

    def download(self, filename, target_filepath):
        self.storage_runner.download(filename, target_filepath)

    def get_download_url(self, filename):
        if self.storage_type == 's3':
            url = f"{SYS_CONF.get('STORAGE_PUBLIC_ENDPOINT') if 'STORAGE_PUBLIC_ENDPOINT' in SYS_CONF else SYS_CONF.get('S3_ENDPOINT')}/{SYS_CONF.get('S3_BUCKET_NAME')}/{filename}"
        else:
            url = f"{SYS_CONF.get('STORAGE_PUBLIC_ENDPOINT') if 'STORAGE_PUBLIC_ENDPOINT' in SYS_CONF else '/api'}/static/{filename}"
        return url

    def exists(self, filename):
        return self.storage_runner.exists(filename)

    def delete(self, filename):
        return self.storage_runner.delete(filename)


storage = Storage()
