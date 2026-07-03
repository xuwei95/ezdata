"""ezdata:纯数据访问 SDK(零 db / web / config / exec / crypto)。

三组:
  handlers/   —— 88 连接器(懒加载注册表 + 实例缓存),统一 Connector 契约;
  services/   —— 数据访问门面(facade) + 提示词(prompts) + 密钥注入(secrets);
  utils/      —— 纯工具(etl_util 只读护栏/JSON 清洗/序列化、query 过滤 DSL 适配)。

供三类入口共用:web 服务(委托:先查库拿配置+解密 secrets 再调 services)、CLI、MCP/skill。
入参一律是"数据源描述"(source_type + config + 明文 secrets dict),不认数据库/加密/租户;
若需传密文 secrets,调 ezdata.services.secrets.set_decryptor(...) 注入解密器。
"""

from ezdata import errors, services, utils
from ezdata.errors import (
    CapabilityError,
    ConnectionFailed,
    DependencyError,
    EzDataError,
    QueryError,
    ReadOnlyViolation,
    UnknownSourceError,
)
from ezdata.handlers import (
    Capability,
    Column,
    Connector,
    ConnectResult,
    connection_schema,
    create_handler,
    get_handler_cls,
    handler_icon,
    list_source_types,
)
from ezdata.services import prompts, secrets
from ezdata.utils import etl_util, query

__all__ = [
    'Capability',
    'CapabilityError',
    'Column',
    'ConnectResult',
    'ConnectionFailed',
    'Connector',
    'DependencyError',
    'EzDataError',
    'QueryError',
    'ReadOnlyViolation',
    'UnknownSourceError',
    'connection_schema',
    'create_handler',
    'errors',
    'etl_util',
    'get_handler_cls',
    'handler_icon',
    'list_source_types',
    'prompts',
    'query',
    'secrets',
    'services',
    'utils',
]
