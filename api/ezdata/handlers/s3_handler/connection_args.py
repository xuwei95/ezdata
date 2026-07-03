"""连接参数定义(扳自 MindsDB s3_handler,增加 endpoint_url 兼容 MinIO/OSS)。"""

from collections import OrderedDict

from ezdata.handlers.const import ARG_TYPE

connection_args = OrderedDict(
    aws_access_key_id={'type': ARG_TYPE.STR, 'description': 'AWS Access Key。', 'required': True,
                       'label': 'AWS Access Key'},
    aws_secret_access_key={'type': ARG_TYPE.PWD, 'description': 'AWS Secret Key。', 'required': True,
                           'label': 'AWS Secret Access Key', 'secret': True},
    bucket={'type': ARG_TYPE.STR, 'description': 'Bucket 名。', 'required': True, 'label': 'Bucket'},
    region_name={'type': ARG_TYPE.STR, 'description': '区域,默认 us-east-1。', 'required': False, 'label': 'Region'},
    aws_session_token={'type': ARG_TYPE.PWD, 'description': '临时凭证 Session Token。', 'required': False,
                       'label': 'Session Token', 'secret': True},
    endpoint_url={'type': ARG_TYPE.STR, 'description': '自定义 endpoint(MinIO/OSS 兼容)。', 'required': False,
                  'label': 'Endpoint URL'},
)

connection_args_example = OrderedDict(
    aws_access_key_id='AKIA...', aws_secret_access_key='****', bucket='my-bucket', region_name='us-east-1',
)
