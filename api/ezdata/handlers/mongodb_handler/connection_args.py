"""连接参数定义(扳自 MindsDB mongodb_handler)。"""

from collections import OrderedDict

from ezdata.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    username={'type': ARG_TYPE.STR, 'description': '用户名。', 'required': True, 'label': 'User'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': True, 'label': 'Password', 'secret': True},
    database={'type': ARG_TYPE.STR, 'description': '数据库名。', 'required': False, 'label': 'Database'},
    host={'type': ARG_TYPE.STR, 'description': "主机名或 IP(本机用 '127.0.0.1')。", 'required': True, 'label': 'Host'},
    port={'type': ARG_TYPE.INT, 'description': 'TCP/IP 端口。', 'required': True, 'label': 'Port'},
)

connection_args_example = OrderedDict(
    host='127.0.0.1',
    port=27017,
    username='mongo',
    password='password',
    database='database',
)
