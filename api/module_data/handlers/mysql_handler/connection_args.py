"""连接参数定义(扳自 MindsDB mysql_handler，ARG_TYPE 改为本地 const)。"""

from collections import OrderedDict

from module_data.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    url={
        'type': ARG_TYPE.URL,
        'description': 'URI 形式连接串。提供时覆盖其它连接参数。',
        'required': False,
        'label': 'URL',
    },
    user={
        'type': ARG_TYPE.STR,
        'description': '用户名。',
        'required': True,
        'label': 'User',
    },
    password={
        'type': ARG_TYPE.PWD,
        'description': '密码。',
        'required': True,
        'label': 'Password',
        'secret': True,
    },
    database={
        'type': ARG_TYPE.STR,
        'description': '数据库名。',
        'required': True,
        'label': 'Database',
    },
    host={
        'type': ARG_TYPE.STR,
        'description': "主机名或 IP。Docker 部署:连平台内置库用服务名(如 'ezdata-mysql'),连宿主机的库用 'host.docker.internal';**切勿填 127.0.0.1/localhost**(那是容器自身,取数在沙箱/worker 里执行会连不上)。仅非容器的本机部署才用 127.0.0.1。",
        'required': True,
        'label': 'Host',
    },
    port={
        'type': ARG_TYPE.INT,
        'description': 'TCP/IP 端口,整数。',
        'required': True,
        'label': 'Port',
    },
    ssl={'type': ARG_TYPE.BOOL, 'description': '是否启用 ssl。', 'required': False, 'label': 'ssl'},
    ssl_ca={'type': ARG_TYPE.PATH, 'description': 'CA 证书路径/URL。', 'required': False, 'label': 'ssl_ca'},
    ssl_cert={'type': ARG_TYPE.PATH, 'description': '服务端公钥证书路径/URL。', 'required': False, 'label': 'ssl_cert'},
    ssl_key={'type': ARG_TYPE.PATH, 'description': '服务端私钥路径/URL。', 'required': False, 'label': 'ssl_key'},
)

connection_args_example = OrderedDict(
    host='127.0.0.1', port=3306, user='root', password='password', database='database',
)
