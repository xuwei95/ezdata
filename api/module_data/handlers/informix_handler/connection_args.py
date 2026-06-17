"""通用 SQL 连接参数(自动补)。"""

from collections import OrderedDict

from module_data.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    host={'type': ARG_TYPE.STR, 'description': '主机。', 'required': True, 'label': 'Host'},
    port={'type': ARG_TYPE.INT, 'description': '端口。', 'required': True, 'label': 'Port'},
    user={'type': ARG_TYPE.STR, 'description': '用户名。', 'required': True, 'label': 'User'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': True, 'label': 'Password', 'secret': True},
    database={'type': ARG_TYPE.STR, 'description': '数据库名。', 'required': True, 'label': 'Database'},
)

connection_args_example = OrderedDict(host='127.0.0.1', port=9088, user='root', password='password', database='db')
