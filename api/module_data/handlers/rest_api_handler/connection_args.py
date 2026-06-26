"""通用 REST/HTTP API 连接参数:配置 base_url + 鉴权 + 命名接口,即可取任意 JSON 接口数据。"""

from collections import OrderedDict

from module_data.handlers.const import ARG_TYPE

connection_args: 'OrderedDict[str, dict]' = OrderedDict(
    base_url={'type': ARG_TYPE.URL, 'label': '接口根地址',
              'description': '如 https://api.example.com(取数路径相对它拼接)', 'required': True},
    auth_type={'type': ARG_TYPE.STR, 'label': '鉴权方式',
               'description': 'none / bearer / api_key / basic(默认 none)'},
    token={'type': ARG_TYPE.PWD, 'label': 'Token / API Key',
           'description': 'bearer 或 api_key 方式的密钥值', 'secret': True},
    api_key_header={'type': ARG_TYPE.STR, 'label': '鉴权 Header 名',
                    'description': 'api_key 方式放哪个请求头,默认 Authorization'},
    api_key_prefix={'type': ARG_TYPE.STR, 'label': 'Token 前缀',
                    'description': 'bearer 默认 "Bearer ";api_key 通常留空'},
    username={'type': ARG_TYPE.STR, 'label': '用户名', 'description': 'basic 鉴权用'},
    password={'type': ARG_TYPE.PWD, 'label': '密码', 'description': 'basic 鉴权用', 'secret': True},
    default_headers={'type': ARG_TYPE.DICT, 'label': '默认请求头',
                     'description': '附加到所有请求,如 {"Accept":"application/json"}'},
    endpoints={'type': ARG_TYPE.DICT, 'label': '命名接口',
               'description': '可选:{名:{path,method,params,data_selector,pagination}};留空则取数时直接写 path'},
    timeout={'type': ARG_TYPE.INT, 'label': '超时(秒)', 'description': '单次请求超时,默认 30'},
)

connection_args_example: 'OrderedDict[str, dict]' = OrderedDict(
    base_url='https://jsonplaceholder.typicode.com',
    auth_type='none',
)
