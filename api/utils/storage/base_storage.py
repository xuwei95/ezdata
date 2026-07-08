"""文件存储后端的抽象接口。"""

from abc import ABC, abstractmethod
from collections.abc import Generator


class BaseStorage(ABC):
    """文件存储接口。"""

    def __init__(self, app_config: dict):
        # app_config 为普通字典（由 storage_utils 从 StorageConfig 构建），键为大写
        self.app_config = app_config

    @abstractmethod
    def save(self, filename, data):
        raise NotImplementedError

    @abstractmethod
    def load_once(self, filename: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def load_stream(self, filename: str) -> Generator:
        raise NotImplementedError

    @abstractmethod
    def download(self, filename, target_filepath):
        raise NotImplementedError

    @abstractmethod
    def exists(self, filename):
        raise NotImplementedError

    @abstractmethod
    def delete(self, filename):
        raise NotImplementedError
