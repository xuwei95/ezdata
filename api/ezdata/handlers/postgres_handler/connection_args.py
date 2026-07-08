"""连接参数定义(扳自 MindsDB postgres_handler)。"""

from collections import OrderedDict

from ezdata.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    user={'type': ARG_TYPE.STR, 'description': '用户名。', 'required': True, 'label': 'User'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': True, 'label': 'Password', 'secret': True},
    database={'type': ARG_TYPE.STR, 'description': '数据库名。', 'required': True, 'label': 'Database'},
    host={'type': ARG_TYPE.STR, 'description': "主机名或 IP(本机用 '127.0.0.1')。", 'required': True, 'label': 'Host'},
    port={'type': ARG_TYPE.INT, 'description': 'TCP/IP 端口。', 'required': True, 'label': 'Port'},
    schema={'type': ARG_TYPE.STR, 'description': '默认优先搜索的 schema。', 'required': False, 'label': 'Schema'},
    sslmode={'type': ARG_TYPE.STR, 'description': '连接 sslmode。', 'required': False, 'label': 'sslmode'},
    connection_parameters={
        'type': ARG_TYPE.DICT,
        'description': '额外连接串参数。',
        'required': False,
        'label': 'connection_parameters',
    },
)

connection_args_example = OrderedDict(
    host='127.0.0.1',
    port=5432,
    user='root',
    schema='public',
    password='password',
    database='database',
)
