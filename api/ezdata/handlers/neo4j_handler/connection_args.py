"""Neo4j 连接参数。"""

from collections import OrderedDict

from ezdata.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    uri={
        'type': ARG_TYPE.STR,
        'description': 'Bolt URI,如 bolt://host:7687 或 neo4j://host:7687。',
        'required': True,
        'label': 'URI',
    },
    username={'type': ARG_TYPE.STR, 'description': '用户名。', 'required': True, 'label': 'User'},
    password={'type': ARG_TYPE.PWD, 'description': '密码。', 'required': True, 'label': 'Password', 'secret': True},
    database={'type': ARG_TYPE.STR, 'description': '数据库名。', 'required': False, 'label': 'Database'},
)

connection_args_example = OrderedDict(
    uri='bolt://127.0.0.1:7687', username='neo4j', password='password', database='neo4j'
)
