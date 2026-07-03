"""OpenSearch 连接参数。"""

from collections import OrderedDict

from ezdata.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    hosts={'type': ARG_TYPE.STR, 'description': '节点地址,多个逗号分隔。', 'required': True, 'label': 'Hosts'},
    user={'type': ARG_TYPE.STR, 'description': '用户名。', 'required': False, 'label': 'User'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': False, 'label': 'Password', 'secret': True},
    verify_certs={'type': ARG_TYPE.BOOL, 'description': '校验证书。', 'required': False, 'label': 'Verify Certs'},
)

connection_args_example = OrderedDict(hosts='https://127.0.0.1:9200', user='admin', password='admin')
