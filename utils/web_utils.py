'''
web 处理相关函数
'''
from flask import request, make_response, send_file
import json


def get_user_ip():
    '''
    获取登录用户ip
    :return:
    '''
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For']
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def get_user_agent():
    '''
    获取ua
    :return:
    '''
    return request.headers.get('User-Agent')


def get_req_para(req=request):
    '''
    获取http请求的参数
    '''
    if req.method in ['GET']:
        args = request.args
        return args.to_dict()
    else:
        res = req.get_data()
        try:
            the_para = json.loads(res)
            return the_para
        except Exception:
            try:
                return req.form
            except Exception:
                raise ValueError


def is_empty(value):
    '''
    校验是否为空
    :param value:
    :return:
    '''
    if isinstance(value, list):
        return value == []
    if isinstance(value, dict):
        return value == {}
    if isinstance(value, str):
        return value == ''
    return value is None


def validate_params(req_dict, verify_dict):
    '''
    校验请求参数
    :return:
    '''
    for key, check in verify_dict.items():
        param = req_dict.get(key)
        name = check['name']
        for k in check:
            if k in ['not_empty', 'required'] and is_empty(param):
                return f"{name}不能为空"
            if k == 'length':
                len_li = check['length']
                if param:
                    if len(str(param)) < len_li[0]:
                        return f"{name}长度低于限制"
                    elif len(str(param)) > len_li[1]:
                        return f"{name}长度超出限制"
            if k == 'equals':
                equals = check['equals']
                if param not in equals:
                    return f"{name}非法字符"
            if k == 'funcs':
                funcs = check['funcs']
                for func in funcs:
                    print(func)
                    res = func(param)
                    print(res)
                    if res:
                        return f"{name}{res}"
    return False


def generate_download_file(output_file, filename):
    '''
    生成文件导出到前端
    :return:
    '''
    # as_attachment：是否在headers中添加Content-Disposition
    # attachment_filename：下载时使用的文件名
    # conditional: 是否支持断点续传
    fv = send_file(output_file, as_attachment=True, download_name=filename, conditional=True)
    fv.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    fv.headers['Content-Disposition'] += "; filename*=utf-8''{}".format(filename)
    fv.headers["Cache-Control"] = "no_store"
    fv.headers["max-age"] = 1
    return make_response(fv)


if __name__ == '__main__':
    pass
