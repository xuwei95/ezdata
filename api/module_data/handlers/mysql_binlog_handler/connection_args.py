"""MySQL Binlog(CDC)连接参数。"""

from collections import OrderedDict

from module_data.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    host={'type': ARG_TYPE.STR, 'description': '主机。', 'required': True, 'label': 'Host'},
    port={'type': ARG_TYPE.INT, 'description': '端口。', 'required': True, 'label': 'Port'},
    user={'type': ARG_TYPE.STR, 'description': '用户名(需 REPLICATION SLAVE/CLIENT 权限)。',
          'required': True, 'label': 'User'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': True, 'label': 'Password', 'secret': True},
    database={'type': ARG_TYPE.STR, 'description': '监听的数据库。', 'required': False, 'label': 'Database'},
    server_id={'type': ARG_TYPE.INT, 'description': '从库标识(唯一,留空随机)。', 'required': False, 'label': 'Server ID'},
)

connection_args_example = OrderedDict(host='127.0.0.1', port=3306, user='root', password='password', database='ezdata')
