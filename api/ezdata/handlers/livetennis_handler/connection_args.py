"""Connection settings for shared live match snapshots."""

from collections import OrderedDict

from ezdata.handlers.const import ARG_TYPE

connection_args: 'OrderedDict[str, dict]' = OrderedDict(
    api_key={
        'type': ARG_TYPE.PWD,
        'label': 'API key',
        'description': 'A Live Tennis API key. The free plan supports live match snapshots.',
        'required': True,
        'secret': True,
    },
    cache_dir={
        'type': ARG_TYPE.PATH,
        'label': 'Cache directory',
        'description': 'Private persistent directory. Sources using the same key must share this directory.',
    },
    refresh_interval={
        'type': ARG_TYPE.INT,
        'label': 'Refresh interval in seconds',
        'description': 'Default 900 seconds. Values below 900 are clamped to 900.',
    },
    timeout={
        'type': ARG_TYPE.INT,
        'label': 'Request timeout in seconds',
        'description': 'Positive timeout for the single snapshot request. Default 30 seconds.',
    },
)

connection_args_example: 'OrderedDict[str, dict]' = OrderedDict(refresh_interval=900, timeout=30)
