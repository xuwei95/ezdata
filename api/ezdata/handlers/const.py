"""
连接参数类型常量(扳自 MindsDB integrations/libs/const.py 的 HANDLER_CONNECTION_ARG_TYPE),
并提供 connection_args(OrderedDict) → JSON Schema 的转换,供前端动态渲染表单。

各源 handler 的 connection_args.py 直接 `from ..const import ARG_TYPE` 即可原样保留 MindsDB 写法。
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections import OrderedDict


class HANDLER_CONNECTION_ARG_TYPE:
    __slots__ = ()
    STR = 'str'
    INT = 'int'
    BOOL = 'bool'
    URL = 'url'
    PATH = 'path'
    DICT = 'dict'
    PWD = 'pwd'


ARG_TYPE = HANDLER_CONNECTION_ARG_TYPE()

# ARG_TYPE → JSON Schema 基础类型
_JSON_TYPE = {
    ARG_TYPE.STR: 'string',
    ARG_TYPE.URL: 'string',
    ARG_TYPE.PATH: 'string',
    ARG_TYPE.PWD: 'string',
    ARG_TYPE.INT: 'integer',
    ARG_TYPE.BOOL: 'boolean',
    ARG_TYPE.DICT: 'object',
}


def is_secret(spec: dict) -> bool:
    """密钥字段:type=pwd 或显式 secret=True。"""
    return spec.get('type') == ARG_TYPE.PWD or bool(spec.get('secret'))


def secret_fields(connection_args: 'OrderedDict[str, dict]') -> list[str]:
    return [k for k, v in (connection_args or {}).items() if is_secret(v)]


def to_json_schema(
    connection_args: 'OrderedDict[str, dict]', example: 'OrderedDict[str, Any] | dict | None' = None
) -> dict[str, Any]:
    """把 MindsDB 风格 connection_args 转成 JSON Schema(前端表单渲染用)。
    example(connection_args_example)里的值作为字段默认值带给前端预填。密钥不带默认。"""
    example = example or {}
    props: dict[str, Any] = {}
    required: list[str] = []
    for name, spec in (connection_args or {}).items():
        p: dict[str, Any] = {'type': _JSON_TYPE.get(spec.get('type'), 'string')}
        if spec.get('label'):
            p['title'] = spec['label']
        if spec.get('description'):
            p['description'] = spec['description']
        if is_secret(spec):
            p['format'] = 'password'
            p['writeOnly'] = True
        elif name in example and example[name] not in (None, ''):
            p['default'] = example[name]
        props[name] = p
        if spec.get('required'):
            required.append(name)
    schema: dict[str, Any] = {'type': 'object', 'properties': props}
    if required:
        schema['required'] = required
    return schema
