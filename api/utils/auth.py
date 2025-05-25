from flask import request, jsonify
from functools import wraps
import datetime
import jwt
import json
import time
from config import SECRET_KEY, USE_TOKEN_REFRESH, TOKEN_EXP_TIME
from utils.cache_utils import set_key_exp, get_key_value
from utils.web_utils import get_user_ip, get_user_agent, get_req_para
from utils.common_utils import md5
from models import Role
from web_apps import db


def get_role_permissions(role_ids):
    '''
    根据用户角色获取用户权限列表
    '''
    role_objs = db.session.query(Role).filter(Role.id.in_(role_ids), Role.delete_tag == 0).all()
    permissions = []
    for role_obj in role_objs:
        if role_obj.role_name == '超级管理员':
            permissions.append('*')
        permissions.extend([i for i in json.loads(role_obj.permissions)])
    permissions = sorted(list(set(permissions)))
    return permissions


def set_insert_user(model, user_name=None, set_tenant=True):
    '''
    创建记录时设置创建人
    '''
    if user_name is None:
        user_info = get_auth_token_info()
        user_name = user_info.get('username')
        tenant_id = user_info.get('tenant_id')
        if set_tenant:
            # 创建记录时带上该用户所属租户
            model.tenant_id = tenant_id
    model.create_by = user_name
    return model


def set_update_user(model, user_name=None):
    '''
    修改记录时设置修改人
    '''
    if user_name is None:
        user_info = get_auth_token_info()
        user_name = user_info.get('username')
    model.update_by = user_name
    return model


def gen_user_feature(token=''):
    '''
    获取客户端ip，ua，mac地址等,拼接后hash作为客户端特征值
    :param requests:
    :return:
    '''
    ip = get_user_ip()
    ua = get_user_agent()
    feature = md5(f"{ip}_{ua}_{token}")
    return feature


def encode_interface_auth_token(info, exp_time):
    """
    生成接口认证Token
    :param user_id: int
    :return: string
    """
    try:
        payload = {
            'exp': exp_time,  # 设置有效期
            'iat': datetime.datetime.utcnow(),
            'iss': 'ken',
            'data': info
        }
        auth_token = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        ).decode()
        return auth_token
    except Exception as e:
        print(e)


def encode_auth_token(user, timeout=TOKEN_EXP_TIME, extends={}):
    """
    生成认证Token
    :return: string
    """
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=timeout),  # 设置登录状态有效期
            'iat': datetime.datetime.utcnow(),
            'iss': 'ken',
            'data': {
                'id': user.id,
                'userId': user.id,
                'username': user.username,
                'nickname': user.nickname,
                'avatar': user.avatar,
                'birthday': str(user.birthday)[:19],
                'sex': user.sex,
                'email': user.email,
                'phone': user.phone,
                'desc': user.description,
                'user_identity': user.user_identity,
                'org_code': user.org_code,
                'tenant_id': user.tenant_id,
                **extends
            }
        }
        auth_token = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        ).decode()
        # 若开启刷新token机制，将客户端特征写入redis并设置过期时间
        if USE_TOKEN_REFRESH:
            feature_key = gen_user_feature(auth_token)
            print(feature_key)
            now_time = int(time.time())
            set_key_exp(feature_key, now_time, TOKEN_EXP_TIME)
        return auth_token
    except Exception as e:
        print(e)


def decode_auth_token(auth_token):
    """
    验证Token
    :param auth_token:
    :return: integer|string
    """
    try:
        # 过期时间验证,若开启token刷新机制则不验证，改为从redis直接判断
        payload = jwt.decode(auth_token, SECRET_KEY, options={'verify_exp': not USE_TOKEN_REFRESH})
        if 'data' in payload and 'userId' in payload['data']:
            return payload
        else:
            raise jwt.InvalidTokenError
    except jwt.ExpiredSignatureError:
        return '用户验证token已过期！'
    except jwt.InvalidTokenError:
        return '无效用户验证token！'


def get_auth_token():
    '''
    获取用户认证token
    '''
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_tokenArr = auth_header.split(" ")
        if not auth_tokenArr or auth_tokenArr[0] != 'JWT' or len(auth_tokenArr) != 2:
            return None
        else:
            return auth_tokenArr[1]
    else:
        return None


def get_auth_token_info():
    '''
    解析token获取用户信息
    :return:
    '''
    auth_token = get_auth_token()
    payload = decode_auth_token(auth_token)
    if not isinstance(payload, str):
        return payload['data']
    else:
        return None


def get_access_info():
    '''
    获取接口访问信息
    '''
    req_dict = get_req_para(request)
    api_path = request.path
    user_info = get_auth_token_info()
    if user_info is None:
        return {}
    operate_user = user_info['username'] if user_info else ''
    user_id = user_info['userId'] if user_info else ''
    tenant_id = user_info.get('tenant_id')
    ip = get_user_ip()
    info = {
        'api_path': api_path,
        'parameter': json.dumps(req_dict),
        'user_id': user_id,
        'tenant_id': tenant_id,
        'user_name': operate_user,  # 用户名
        'ip': ip,  # 访问ip
    }
    return info


def check_auth_token(auth_token, f, *args, **kws):
    '''
    校验jwt token, 检测用户登录状态
    '''
    payload = decode_auth_token(auth_token)
    if not isinstance(payload, str):
        # 若启用刷新有效期机制，在redis中判断用户token有效期
        if USE_TOKEN_REFRESH:
            feature_key = gen_user_feature(auth_token)
            feature_value = get_key_value(feature_key)
            if not feature_value:
                print('用户验证token已过期')
                result = jsonify({'msg': '用户验证token已过期', 'code': 403})
            else:
                result = f(*args, **kws)
                now_time = int(time.time())
                refresh_time = int(feature_value)
                print(now_time, refresh_time, now_time - refresh_time, TOKEN_EXP_TIME)
                # 若剩余有效期低于默认有效期的一半时重新刷新token有效期
                if (now_time - refresh_time) > (TOKEN_EXP_TIME / 2):
                    set_key_exp(feature_key, now_time, TOKEN_EXP_TIME)
        else:
            result = f(*args, **kws)
    else:
        result = jsonify({'msg': payload, 'code': 403})
    return result


def validate_user(f):
    '''
    装饰器，对需要登录才能操作的api请求校验jwt, 返回相应结果
    '''
    @wraps(f)
    def decorated_function(*args, **kws):
        auth_token = get_auth_token()
        if auth_token:
            result = check_auth_token(auth_token, f, *args, **kws)
        else:
            result = jsonify({'msg': '用户验证失败', 'code': 403})
        return result
    decorated_function.__name__ = f.__name__
    return decorated_function


def validate_permissions(permissions):
    '''
    装饰器，对需要有权限才能操作的api请求校验权限, 返回相应结果
    '''
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kws):
            auth_info = get_auth_token_info()
            auth_permissions = auth_info['permissions']
            valid_permissions = [i for i in auth_permissions if i in permissions]
            if permissions != [] and valid_permissions == [] and '*' not in auth_permissions:
                result = jsonify({'msg': '用户无权限进行此操作', 'code': 400})
            else:
                result = f(*args, **kws)
            return result
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator
