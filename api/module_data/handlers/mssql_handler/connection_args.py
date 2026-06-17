"""连接参数定义(扳自 MindsDB mssql_handler)。"""

from collections import OrderedDict

from module_data.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    user={'type': ARG_TYPE.STR, 'description': '用户名。', 'required': True, 'label': 'User'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': True, 'label': 'Password', 'secret': True},
    database={'type': ARG_TYPE.STR, 'description': '数据库名。', 'required': True, 'label': 'Database'},
    host={'type': ARG_TYPE.STR, 'description': '主机。', 'required': True, 'label': 'Host'},
    port={'type': ARG_TYPE.INT, 'description': '端口。', 'required': False, 'label': 'Port'},
    server={'type': ARG_TYPE.STR, 'description': '实例名(可选)。', 'required': False, 'label': 'Server'},
    schema={'type': ARG_TYPE.STR, 'description': '默认 schema。', 'required': False, 'label': 'Schema'},
)

connection_args_example = OrderedDict(
    host='127.0.0.1', port=1433, user='sa', password='password', database='master', schema='dbo',
)
