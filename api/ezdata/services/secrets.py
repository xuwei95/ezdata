"""密文 secrets 解密器注入点(让 ezdata 保持零加密实现依赖)。

ezdata 是纯数据 SDK,本身不含任何加密/密钥体系。若宿主要向 handler 传"密文串"形式的
secrets(如 web/worker 从库里取到 AES 密文),需在启动时注入一个解密函数;否则请直接传明文 dict。

- web / worker:`module_data` 包在导入时会自动注入宿主的 CryptoUtil.decrypt;
- cli / mcp / skill:自行 `set_decryptor(...)`,或干脆只传明文 dict(不触发本模块)。
"""

from collections.abc import Callable

# str(密文) -> str(明文 JSON)
_decryptor: 'Callable[[str], str] | None' = None


def set_decryptor(fn: 'Callable[[str], str] | None') -> None:
    """注入密文解密函数(幂等,后注入覆盖先注入)。传 None 可清除。"""
    global _decryptor
    _decryptor = fn


def get_decryptor() -> 'Callable[[str], str] | None':
    """取当前解密函数;未注入返回 None。"""
    return _decryptor
