"""连接参数定义(扳自 MindsDB clickhouse_handler)。"""

from collections import OrderedDict

from module_data.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    protocol={'type': ARG_TYPE.STR, 'description': '协议 native/http/https。', 'required': False, 'label': 'Protocol'},
    user={'type': ARG_TYPE.STR, 'description': '用户名。', 'required': True, 'label': 'User'},
    database={'type': ARG_TYPE.STR, 'description': '数据库名。', 'required': True, 'label': 'Database name'},
    host={'type': ARG_TYPE.STR, 'description': '主机。', 'required': True, 'label': 'Host'},
    port={'type': ARG_TYPE.INT, 'description': '端口。', 'required': True, 'label': 'Port'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': True, 'label': 'Password', 'secret': True},
    verify={'type': ARG_TYPE.BOOL, 'description': 'SSL 校验。', 'required': False, 'label': 'SSL Verification'},
)

connection_args_example = OrderedDict(
    protocol='native', host='127.0.0.1', port=9000, user='default', password='password', database='default',
)
