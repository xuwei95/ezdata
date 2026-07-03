"""Kafka 连接参数。"""

from collections import OrderedDict

from ezdata.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    bootstrap_servers={'type': ARG_TYPE.STR, 'description': 'broker 地址,多个逗号分隔,如 h1:9092,h2:9092。',
                       'required': True, 'label': 'Bootstrap Servers'},
    group_id={'type': ARG_TYPE.STR, 'description': '消费组 ID(消费时用)。', 'required': False, 'label': 'Group ID'},
    security_protocol={'type': ARG_TYPE.STR, 'description': 'PLAINTEXT/SASL_PLAINTEXT/SASL_SSL。',
                       'required': False, 'label': 'Security Protocol'},
    sasl_mechanism={'type': ARG_TYPE.STR, 'description': 'PLAIN/SCRAM-SHA-256 等。', 'required': False,
                    'label': 'SASL Mechanism'},
    sasl_plain_username={'type': ARG_TYPE.STR, 'description': 'SASL 用户名。', 'required': False, 'label': 'SASL User'},
    sasl_plain_password={'type': ARG_TYPE.PWD, 'description': 'SASL 密码。', 'required': False,
                         'label': 'SASL Password', 'secret': True},
)

connection_args_example = OrderedDict(bootstrap_servers='127.0.0.1:9092', group_id='ezdata')
