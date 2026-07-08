"""连接参数定义(扳自 MindsDB elasticsearch_handler)。"""

from collections import OrderedDict

from ezdata.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    hosts={
        'type': ARG_TYPE.STR,
        'description': '节点地址,多个用逗号分隔,如 host1:9200,host2:9200。',
        'required': False,
        'label': 'Hosts',
    },
    cloud_id={
        'type': ARG_TYPE.STR,
        'description': 'Elastic Cloud ID(与 hosts 二选一)。',
        'required': False,
        'label': 'Cloud ID',
    },
    user={'type': ARG_TYPE.STR, 'description': '用户名。', 'required': False, 'label': 'User'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': False, 'label': 'Password', 'secret': True},
    api_key={'type': ARG_TYPE.STR, 'description': 'API Key。', 'required': False, 'label': 'API Key', 'secret': True},
)

connection_args_example = OrderedDict(hosts='localhost:9200', user='elastic', password='password')
