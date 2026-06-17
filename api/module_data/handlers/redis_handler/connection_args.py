"""Redis 连接参数。"""

from collections import OrderedDict

from module_data.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    host={'type': ARG_TYPE.STR, 'description': '主机。', 'required': True, 'label': 'Host'},
    port={'type': ARG_TYPE.INT, 'description': '端口。', 'required': True, 'label': 'Port'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': False, 'label': 'Password', 'secret': True},
    db={'type': ARG_TYPE.INT, 'description': '库号(0-15)。', 'required': False, 'label': 'DB'},
)

connection_args_example = OrderedDict(host='127.0.0.1', port=6379, db=0)
