"""Trino 连接参数。"""

from collections import OrderedDict

from module_data.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    host={'type': ARG_TYPE.STR, 'description': '主机。', 'required': True, 'label': 'Host'},
    port={'type': ARG_TYPE.INT, 'description': '端口。', 'required': True, 'label': 'Port'},
    user={'type': ARG_TYPE.STR, 'description': '用户名。', 'required': True, 'label': 'User'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': False, 'label': 'Password', 'secret': True},
    catalog={'type': ARG_TYPE.STR, 'description': 'Catalog。', 'required': False, 'label': 'Catalog'},
    schema={'type': ARG_TYPE.STR, 'description': 'Schema。', 'required': False, 'label': 'Schema'},
)

connection_args_example = OrderedDict(host='127.0.0.1', port=8080, user='admin', catalog='hive', schema='default')
