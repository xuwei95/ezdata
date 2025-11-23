'''
字段校验函数
'''
import json
import re


def validate_email(text):
    '''
    验证邮箱格式
    '''
    if text != '':
        if re.search(r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', text):
            return False
        else:
            return '邮箱格式错误'
    return False


def validate_head(text, head_text):
    '''
    字段变量校验，以head_text开头
    :return:
    '''
    if not text.startswith(head_text):
        return f'字段变量必须以{head_text}开头'


def validate_json(text):
    '''
    校验是否是json格式
    :return:
    '''
    try:
        if isinstance(text, str):
            text = json.loads(text)
        if isinstance(text, list) or isinstance(text, dict):
            return False
        return f'必须是列表或对象格式'
    except Exception as e:
        print(e)
        return f'必须是列表或对象格式'


def validate_username(text):
    '''
    验证用户名
    '''
    if re.search(r'^[0-9a-zA-Z_]{1,}$', text):
        return False
    else:
        return '用户名格式错误'
