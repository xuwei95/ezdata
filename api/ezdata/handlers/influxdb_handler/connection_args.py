"""InfluxDB(3.x)连接参数。"""

from collections import OrderedDict

from ezdata.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    host={'type': ARG_TYPE.STR, 'description': '主机 URL,如 https://host:8181。', 'required': True, 'label': 'Host'},
    token={'type': ARG_TYPE.PWD, 'description': 'API Token。', 'required': True, 'label': 'Token', 'secret': True},
    database={'type': ARG_TYPE.STR, 'description': 'database / bucket 名。', 'required': True, 'label': 'Database'},
    org={'type': ARG_TYPE.STR, 'description': '组织(可选)。', 'required': False, 'label': 'Org'},
)

connection_args_example = OrderedDict(host='http://127.0.0.1:8181', token='****', database='mydb')
