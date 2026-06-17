"""连接参数定义(扳自 MindsDB oracle_handler)。"""

from collections import OrderedDict

from module_data.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    dsn={'type': ARG_TYPE.STR, 'description': '数据源名(DSN),给定时优先。', 'required': False, 'label': 'DSN'},
    host={'type': ARG_TYPE.STR, 'description': '主机。', 'required': False, 'label': 'Host'},
    port={'type': ARG_TYPE.INT, 'description': '端口。', 'required': False, 'label': 'Port'},
    sid={'type': ARG_TYPE.STR, 'description': 'Oracle SID。', 'required': False, 'label': 'SID'},
    service_name={'type': ARG_TYPE.STR, 'description': 'Service Name。', 'required': False, 'label': 'Service Name'},
    user={'type': ARG_TYPE.STR, 'description': '用户名。', 'required': True, 'label': 'User'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': True, 'label': 'Password', 'secret': True},
    thick_mode={'type': ARG_TYPE.BOOL, 'description': '是否启用 thick 模式。', 'required': False, 'label': 'Thick Mode'},
)

connection_args_example = OrderedDict(host='127.0.0.1', port=1521, user='admin', password='password', sid='ORCL')
