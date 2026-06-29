import base64
import hashlib

from cryptography.fernet import Fernet, MultiFernet

from config.env import JwtConfig, SecurityConfig
from exceptions.exception import ServiceException


class CryptoUtil:
    """
    加解密工具类(库内数据源/AI 凭据的静态加密)

    密钥与 JWT 签名密钥分离:
    - 主密钥:SecurityConfig.data_encrypt_key(标准 Fernet key);配置后所有新密文用它加密。
    - 兼容密钥:由 JwtConfig.jwt_secret_key 派生(旧实现 = sha256(jwt_secret_key))。
    用 MultiFernet([主, 旧])解密:存量(旧密钥加密的)密文仍可解,下次保存即用主密钥重写,
    实现零迁移平滑切换。未配置 data_encrypt_key 时主密钥即旧派生密钥,行为与改造前一致。
    """

    _cipher_suite: MultiFernet | None = None

    @classmethod
    def _legacy_key(cls) -> bytes:
        """由 JWT secret 派生的旧 Fernet key(向后兼容)。"""
        return base64.urlsafe_b64encode(hashlib.sha256(JwtConfig.jwt_secret_key.encode()).digest())

    @classmethod
    def _get_cipher_suite(cls) -> MultiFernet:
        if cls._cipher_suite is None:
            legacy = Fernet(cls._legacy_key())
            data_key = (SecurityConfig.data_encrypt_key or '').strip()
            if data_key:
                # 主密钥独立于 JWT;旧密钥仅用于解开存量密文
                try:
                    primary = Fernet(data_key.encode('utf-8'))
                except Exception as e:
                    raise ServiceException('DATA_ENCRYPT_KEY 不是合法的 Fernet 密钥') from e
                cls._cipher_suite = MultiFernet([primary, legacy])
            else:
                # 未单独配置:沿用 JWT 派生密钥(与改造前等价)
                cls._cipher_suite = MultiFernet([legacy])
        return cls._cipher_suite

    @classmethod
    def encrypt(cls, data: str) -> str:
        """
        加密字符串(始终用主密钥,即 MultiFernet 的第一个 key)

        :param data: 明文
        :return: 密文
        """
        if not data:
            return data
        try:
            cipher_suite = cls._get_cipher_suite()
            encrypted_bytes = cipher_suite.encrypt(data.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ServiceException('加密失败') from e

    @classmethod
    def decrypt(cls, token: str) -> str:
        """
        解密字符串(主密钥失败时自动回退兼容密钥)

        :param token: 密文
        :return: 明文
        """
        if not token:
            return token
        try:
            cipher_suite = cls._get_cipher_suite()
            decrypted_bytes = cipher_suite.decrypt(token.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ServiceException('解密失败') from e
