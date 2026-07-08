"""本地磁盘存储实现。

路径基于当前工作目录(cwd)解析，与模板的 /profile 静态服务、UploadConfig.UPLOAD_PATH 对齐：
默认 STORAGE_LOCAL_PATH = 'vf_admin/upload_path'，因此 local 后端与模板原有行为完全一致。
"""

import os
import shutil
from collections.abc import Generator

from utils.storage.base_storage import BaseStorage


class LocalStorage(BaseStorage):
    def __init__(self, app_config: dict):
        super().__init__(app_config)
        # 相对路径基于 cwd（不重定位到本文件所在目录），保证与 /profile 静态服务一致
        self.folder = app_config.get('STORAGE_LOCAL_PATH', 'vf_admin/upload_path')

    def _full(self, filename: str) -> str:
        return os.path.join(self.folder, filename)

    def save(self, filename, data):
        filepath = self._full(filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(data)

    def load_once(self, filename: str) -> bytes:
        filepath = self._full(filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError('File not found')
        with open(filepath, 'rb') as f:
            return f.read()

    def load_stream(self, filename: str) -> Generator:
        def generate(filepath: str = self._full(filename)) -> Generator:
            if not os.path.exists(filepath):
                raise FileNotFoundError('File not found')
            with open(filepath, 'rb') as f:
                while chunk := f.read(4096):  # 4KB 分块读取
                    yield chunk

        return generate()

    def download(self, filename, target_filepath):
        filepath = self._full(filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError('File not found')
        shutil.copyfile(filepath, target_filepath)

    def exists(self, filename):
        return os.path.exists(self._full(filename))

    def delete(self, filename):
        filepath = self._full(filename)
        if os.path.exists(filepath):
            os.remove(filepath)
