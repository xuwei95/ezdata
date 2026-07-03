"""ezdata.services —— 数据访问门面 + 提示词 + 密钥注入 + 依赖管理。

- facade:无状态数据访问(元信息/连接/结构/取数/写入),门面函数在本包顶层直接可用;
- prompts:跨源查询/转换提示词构造(NL→查询);
- secrets:密文解密器注入点;
- dependencies:连接器依赖诊断(只读)+ 安装(跑 pip、动态生效,唯一带副作用的能力)。
"""

from ezdata.services import dependencies
from ezdata.services.dependencies import install as install_dependencies
from ezdata.services.dependencies import status as dependency_status
from ezdata.services.facade import (
    connection_schema,
    get_columns,
    get_handler,
    list_source_types,
    list_tables,
    operators,
    query,
    source_type_icon,
    test_connection,
    write,
)

__all__ = [
    'connection_schema',
    'dependencies',
    'dependency_status',
    'get_columns',
    'get_handler',
    'install_dependencies',
    'list_source_types',
    'list_tables',
    'operators',
    'query',
    'source_type_icon',
    'test_connection',
    'write',
]
