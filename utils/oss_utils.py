'''
对象存储相关函数
'''
from config import OSS_TYPE, OSS_HOST, OSS_PORT, OSS_KEY, OSS_SECRET, OSS_BUCKET
from minio import Minio
import io
from utils.common_utils import md5

if OSS_TYPE == 'minio':
    ossClient = Minio(f'{OSS_HOST}:{OSS_PORT}',
                      access_key=OSS_KEY,
                      secret_key=OSS_SECRET,
                      secure=False)


def get_bucket_url():
    return f'http://{OSS_HOST}:{OSS_PORT}/{OSS_BUCKET}/'


def upload_content_to_oss(content, name='', file_type='jpg'):
    '''
    上传内容到oss
    :param content: 内容
    :param name: 文件名
    :param file_type: 文件类型
    :return: 文件oss地址
    '''
    hash = md5(content)
    value_as_a_stream = io.BytesIO(content)
    save_name = '{}.{}'.format(hash, file_type) if name == '' else name
    ossClient.put_object(OSS_BUCKET, save_name, value_as_a_stream, length=len(content))
    return f'http://{OSS_HOST}:{OSS_PORT}/{OSS_BUCKET}/{save_name}'

