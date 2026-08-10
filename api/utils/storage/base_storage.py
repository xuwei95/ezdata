"""文件存储后端的抽象接口。"""

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import BinaryIO


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

    # 以下三个方法供文件管理(Range 下载/流式落盘/取大小)使用。为不破坏既有云后端
    # (aliyun/azure/google/tencent/oci 尚未实现),这里给非抽象默认实现;local/s3 覆写。
    def save_fileobj(self, filename: str, fileobj: BinaryIO) -> None:
        """从二进制文件对象流式写入（避免整文件读入内存）。fileobj 需已定位到起始位置。"""
        raise NotImplementedError(f'{type(self).__name__} 暂不支持 save_fileobj')

    def load_range(self, filename: str, start: int = 0, length: int | None = None) -> Generator:
        """按字节范围流式读取（用于 Range 断点下载）。length=None 读到末尾。"""
        raise NotImplementedError(f'{type(self).__name__} 暂不支持 load_range')

    def stat(self, filename: str) -> int:
        """返回对象字节大小；对象不存在时抛 FileNotFoundError。"""
        raise NotImplementedError(f'{type(self).__name__} 暂不支持 stat')

    @abstractmethod
    def download(self, filename, target_filepath):
        raise NotImplementedError

    @abstractmethod
    def exists(self, filename):
        raise NotImplementedError

    @abstractmethod
    def delete(self, filename):
        raise NotImplementedError
