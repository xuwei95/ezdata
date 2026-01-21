'''
公共工具类，函数
'''
import hashlib
import os.path
import re
import time
import json
import requests
from dateutil.relativedelta import relativedelta
from dateutil import parser
import datetime
from pypinyin import lazy_pinyin
import functools
import io
import uuid
import pandas as pd
import importlib


class Singleton(type):
    '''
    单例模式
    '''
    def __init__(cls, *args, **kwargs):
        cls.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
        return cls.__instance


def import_class(class_path):
    '''
    导入模块
    :param class_path:
    :return:
    '''
    module_name, class_name = class_path.rsplit('.', 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def gen_json_response(data=None, code=200, msg='ok', msg_key='msg', code_key='code', data_key='data', extends={}):
    '''
    生成web接口返回json格式数据
    :param data:
    :param code:
    :param msg:
    :return:
    '''
    res_data = {
        code_key: code,
        msg_key: msg,
        **extends
    }
    if data is not None:
        res_data[data_key] = data
    return res_data


def gen_uuid(res_type='source'):
    '''
    生成uuid唯一号
    :return:
    '''
    uid = str(uuid.uuid4())
    if res_type == 'base':
        return uid.replace('-', '')
    return uid


def gen_dict_hash_key(dic):
    '''
    对字典生成 hash key
    '''
    # 按字典序将key排序
    sorted_tag_keys = sorted(list(dic.keys()))
    new_dic = {k: dic[k] for k in sorted_tag_keys}
    return md5(str(new_dic))


def get_now_time(res_type='int'):
    '''
    返回当前时间
    '''
    t = time.time()
    if res_type == 'int':
        return int(t)
    if res_type == 'ms':
        return int(t * 1000)
    if res_type == 'ns':
        return int(t * 1000000000)
    if res_type == 'datetime':
        # t = timestamp_to_date(t)
        # t = format_date(int(t), res_type='datetime')
        return timestamp_to_date(t)
    return t

def trans_value_type(value, trans_type='str'):
    '''
    转换值类型
    :param value:
    :param trans_type:
    :return:
    '''
    if trans_type == 'str':
        value = str(value)
    elif trans_type == 'int':
        try:
            value = int(value)
        except Exception as e:
            print(e)
    elif trans_type == 'float':
        try:
            value = float(value)
        except Exception as e:
            print(e)
    elif trans_type in ['date', 'datetime', 'timestamp']:
        try:
            value = format_date(value, res_type=trans_type)
        except Exception as e:
            print(e)
    return value

def print_run_time(func):
    '''
    打印函数运行时间装饰器
    :param func:
    :return:
    '''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        r = func(*args, **kwargs)
        cost = time.time() - start
        cost = round(cost, 3)
        print(f"{func.__name__}函数执行了{cost}s")
        return r
    return wrapper


def parse_json(source, default=None):
    '''
    转为python对象
    :param source:
    :return:
    '''
    if isinstance(source, bytes):
        source = source.decode()
    if isinstance(source, str):
        try:
            source = json.loads(source)
        except Exception as e:
            print(e)
            source = None
    if source is None:
        return default
    return source


def gen_json_to_dict_code(dic, indent=2):
    '''
    将json字符串转为字典代码字符串
    :param dic:
    :param indent:
    :return:
    '''
    dict_code = json.dumps(dic, indent=indent, ensure_ascii=False)
    dict_code = '\n'.join(['{'] + [' ' * indent + i for i in dict_code.split('\n')[1:-1]] + [' ' * indent + '}'])
    dict_code = dict_code.replace(': true', ': True').replace(': false', ': False').replace(': null', ': None')
    return dict_code


def flatten_dict(dic, key, if_exist='replace'):
    '''
    对字典嵌套字典字段摊平到上级字典，如{'field': {'a': 1, 'b': 'hehe'}, 'c': 2020} -> {'a': 1, 'b': 'hehe', 'c': 2020}
    '''
    dic2 = dic.get(key, {})
    for k in dic2:
        if k not in dic or (k in dic and if_exist == 'replace'):
            dic[k] = dic2[k]
    dic.pop(key)
    return dic


def get_json_value(val):
    '''
    将python变量转为json变量
    :param val:
    :return:
    '''
    value = f"'{val}'" if isinstance(val, str) else val
    if value == True:
        value = 'true'
    elif value == False:
        value = 'false'
    elif value is None:
        value = 'null'
    return value


def parse_data_to_excel(data):
    '''
    将数据转为excel文件
    :param data:
    :return:
    '''
    df = pd.DataFrame(data)
    print(df)
    # 使用字节流存储
    output = io.BytesIO()
    # 保存文件
    df.to_excel(output, index=False)
    # 文件seek位置，从头(0)开始
    output.seek(0)
    return output


def request_url(url, method='get', params={}, headers={}, data={}, json={}, timeout=30, retry=3, proxy=None):
    '''
    请求url
    :param url:
    :param retry:
    :return:
    '''
    req_times = 0
    while req_times < retry:
        try:
            res = requests.request(method, url, headers=headers, params=params, data=data, json=json, stream=True, timeout=timeout, proxies=proxy)
            return res
        except Exception as e:
            print(e)
            req_times += 1
    res = requests.request(method, url, headers=headers, params=params, data=data, stream=True, timeout=timeout)
    return res


def trans_rule_value(value):
    '''
    转换条件筛选时的值
    :param value:
    :return:
    '''
    if not isinstance(value, str):
        return value
    print(value)
    time_dict = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 86400 * 7,
        'M': 86400 * 30,
        'Y': 86400 * 365
    }
    #  以timestamp:开头的，转换时间，如&gt[date]=timestamp:-1d 取date大于当前时间往前倒1天的时间戳
    if value.startswith('timestamp:'):
        t = value[-1]
        now = get_now_time()
        try:
            value = int(value[10:-1].strip())
            value = now + value * time_dict[t]
            return value
        except Exception as e:
            print(e)
    elif value.startswith('timestamp_ms:'):
        t = value[-1]
        now = get_now_time()
        try:
            value = int(value[13:-1].strip())
            value = (now + value * time_dict[t]) * 1000
            return value
        except Exception as e:
            print(e)
    #  以time:开头的，转换时间
    #  如&gt[date]=time:-300s 取date大于当前时间往前倒300秒的数据
    elif value.startswith('time:'):
        t = value[-1]
        now = get_now_time()
        try:
            value = int(value[5:-1].strip())
            value = now + value * time_dict[t]
            value = timestamp_to_date(value)
        except Exception as e:
            print(e)
    #  以date:开头的，转换日期时间
    #  如时间2022-02-08 22:10:50 date: %Y-%m-%d %H 将时间转为当前时间格式后转回时间:2022-02-08 22:01:01
    elif value.startswith('date:'):
        now = datetime.datetime.now()
        try:
            value = format_date(now, value[5:].strip())
            value = format_date(value)
        except Exception as e:
            print(e)
    # 以int: 开头的转为整数
    elif value.startswith('int:'):
        try:
            value = int(value[4:])
        except Exception as e:
            print(e)
    # 以float: 开头的转为整数
    elif value.startswith('int:'):
        try:
            value = int(value[6:])
        except Exception as e:
            print(e)
    return value


def get_now_date():
    '''
    获取当前时间
    :return:
    '''
    return str(datetime.datetime.now)[:19]


def format_date(date, format='%Y-%m-%d %H:%M:%S', res_type='str', default=None):
    '''
    格式化日期
    :param date:
    :return:
    '''
    try:
        if isinstance(date, int):
            date = timestamp_to_date(date)
            date = parser.parse(date)
        if isinstance(date, str):
            date = parser.parse(date)
        elif not isinstance(date, datetime.datetime):
            date = str(date)
            date = parser.parse(date)
        date = date.strftime(format)
        if res_type == 'date':
            return date
        if res_type == 'datetime':
            date = datetime.datetime.strptime(date, format)
            return date
        if res_type == 'timestamp':
            return date_to_timestamp(date)
        date = str(date)
        if len(date) > 19:
            date = date[:19]
        if '.000Z' in date:
            date = date.replace('.000Z', '')
        if 'T' in date:
            date = date.replace('T', ' ')
        return date
    except Exception as e:
        print(e)
        return default


def date_to_timestamp(date, default=None):
    '''
    日期转时间戳
    :param date:
    :return:
    '''
    try:
        if not isinstance(date, str):
            date = str(date)
        if len(date) > 19:
            date = date[:19]
        if 'T' in date:
            date = date.replace('T', ' ').replace('.000Z', '')
        if len(date) == 10:
            timeArray = time.strptime(date, "%Y-%m-%d")
        else:
            timeArray = time.strptime(date, "%Y-%m-%d %H:%M:%S")
        timeStamp = int(time.mktime(timeArray))
        return timeStamp
    except Exception as e:
        print(e)
        return default


def timestamp_to_date(timestamp, defalut=None):
    '''
    时间戳转日期
    :param date:
    :return:
    '''
    try:
        # 将纳秒转为秒
        if timestamp > 1000000000 * 1000 * 1000:
            timestamp = timestamp / 1000 / 1000
        # 将豪秒转为秒
        if timestamp > 1000000000 * 1000:
            timestamp = timestamp / 1000
        if timestamp != '' and timestamp is not None:
            timeArray = time.localtime(timestamp)
            otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            return otherStyleTime
        else:
            return defalut
    except Exception as e:
        print(e)
        return defalut


def trans_time_length(time_length):
    '''
    转换时间长度，转为秒数
    :param time_length:
    :return:
    '''
    time_symbol_dict = {
        'Y': 86400 * 365,
        'M': 86400 * 30,
        'W': 86400 * 7,
        'd': 86400,
        'h': 3600,
        'm': 60,
        's': 1
    }
    if time_length == 'forever':
        return 86400 * 365 * 100
    else:
        symbol = time_length[-1]
        length = time_length[:-1]
        symbol_len = time_symbol_dict.get(symbol)
        return int(length) * symbol_len


def get_date_list(start_date, end_date):
    '''
    获取日期列表
    '''
    start_time = start_date
    end_time = end_date
    datestart = datetime.datetime.strptime(start_time, '%Y-%m-%d')
    dateend = datetime.datetime.strptime(end_time, '%Y-%m-%d')
    date_list = []
    date_list.append(datestart.strftime('%Y-%m-%d'))
    while datestart < dateend:
        datestart += relativedelta(days=+1)
        date_list.append(datestart.strftime('%Y-%m-%d'))
    query_list = []
    for i in range(len(date_list)):
        s = date_list[i]
        query_list.append(s)
    return query_list


def md5(content):
    '''
    将内容转为MD5值
    :return:
    '''
    md = hashlib.md5()
    if isinstance(content, bytes):
        md.update(content)
    else:
        md.update(content.encode("utf8"))
    return md.hexdigest()


def sha256(content):
    '''
    将内容转为sha256
    :param content:
    :return:
    '''
    s = hashlib.sha256()
    if isinstance(content, bytes):
        s.update(content)
    else:
        s.update(content.encode("utf8"))
    return s.hexdigest()


def parse_to_string(val):
    '''
    将字段或列表转换为json字符串
    :param val:
    :return:
    '''
    if isinstance(val, dict) or isinstance(val, list):
        return json.dumps(val)
    return val


def parse_to_int(val, default=0):
    '''
    将字段或列表转换为数字
    :param val:
    :return:
    '''
    try:
        val = int(val)
    except Exception as e:
        print(e)
        val = default
    return val


def format_str(str1='', type='lower'):
    '''
    去除特殊字符
    :param str1:
    :param type:
    :return:
    '''
    if str1:
        try:
            temp = str1.decode('utf-8', 'ignore')
        except BaseException:
            temp = str1
        xx = u"([\u4e00-\u9fa5a-zA-Z0-9]+)"
        pattern = re.compile(xx)
        results = pattern.findall(str(temp))
        if results:
            long_str = ''.join(results)
            if type == 'lower':
                return long_str.lower()
            elif type == 'upper':
                return long_str.upper()
            else:
                return long_str
        else:
            return ''
    else:
        return ''


def _lazy_pinyin(*args):
    '''
    中文转拼音
    :param args:
    :return:
    '''
    return lazy_pinyin(args[0])


def _change_to_lower(*args):
    '''
    转小写
    :param args:
    :return:
    '''
    return str(args[0]).lower()


def _change_to_upper(*args):
    '''
    转大写
    :param args:
    :return:
    '''
    return str(args[0]).upper()


def read_file(file):
    '''
    读取文件转为文件对象
    '''
    file_obj = None
    if isinstance(file, str):
        if file.startswith('http:'):
            try:
                res = request_url(file)
                file_obj = io.BytesIO(res.content)
            except Exception as e:
                print(e)
        else:
            try:
                file_obj = open(file, 'rb')
            except Exception as e:
                print(e)
    return file_obj


def read_file_path(file):
    '''
    读取文件转为文件路径，网络文件生成临时文件
    '''
    if not isinstance(file, str):
        file = str(file)
    if file.startswith('http:'):
        try:
            suffix = file.split('.')[-1]
            res = request_url(file)
            if res.status_code == 200:
                tmp_path = f'{gen_uuid()}.{suffix}'
                tmp_file = open(tmp_path, 'wb')
                tmp_file.write(res.content)
                return True, True, tmp_path
            else:
                return False, False, f'请求网络文件错误:{res.text}'
        except Exception as e:
            return False, False, f'请求网络文件错误:{e}'
    else:
        if os.path.exists(file):
            return True, False, file
        else:
            return False, False, '文件未找到'


def trans_dict_to_rules(api_form):
    '''
    对dict类型数据转换为筛选规则
    '''
    params_list = []
    for k in api_form:
        params_list.append((k, [api_form[k]]))
    extract_rules = []
    for k, values in params_list:
        field = ''
        fields = re.findall('\[(.*?)\]', k)
        if fields != ['']:
            field = '.'.join(fields)
        if '[' in k:
            rule = re.findall('(.*?)\[', k)[0]
        else:
            rule = k
        for value in values:
            extract_rules.append({'field': field, 'rule': rule, 'value': value})
    print(extract_rules)
    return extract_rules

def get_res_fields(res_data):
    '''
    获取返回字段列表
    '''
    res_fields = []
    if isinstance(res_data, list) and res_data != []:
        dic = res_data[0]
        if isinstance(dic, dict):
            res_fields = list(dic.keys())
    if isinstance(res_data, dict):
        if 'records' in res_data:
            if res_data['records'] != []:
                res_fields = list(res_data['records'][0].keys())
            else:
                res_fields = []
        else:
            if 'code' in res_data and res_data['code'] != 200:
                return []
            res_fields = list(res_data.keys())
    return list(set(res_fields))

def parse_to_list(s, split_text=','):
    '''
    将字符串数据转换为列表
    :param s:
    :param split_text:
    :return:
    '''
    if s is None:
        return []
    if isinstance(s, str):
        if s == '':
            return []
        else:
            s = s.split(split_text)
    return s

def convert_to_json_serializable(value):
    """
    将值转换为 JSON 可序列化的格式。
    """
    if isinstance(value, (pd.Timestamp, pd.Period)):
        return str(value)
    elif isinstance(value, (list, dict)):
        try:
            json.dumps(value)
            return value
        except TypeError:
            return str(value)
    elif pd.isna(value):
        return ""
    else:
        return value

def df_to_list(df):
    if isinstance(df, pd.DataFrame):
        # 将所有 datetime 类型的列转换为字符串
        for col in df.select_dtypes(include=['datetime']).columns:
            df[col] = df[col].astype(str)
        # 填充 NaN 值
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(0, inplace=True)
            else:
                df[col].fillna("", inplace=True)
        # 将 DataFrame 转换为字典列表
        data_li = df.to_dict(orient='records')
    elif isinstance(df, list):
        data_li = df
    else:
        data_li = [df]
    # 确保所有值都是 JSON 可序列化的
    for record in data_li:
        for key, value in record.items():
            record[key] = convert_to_json_serializable(value)
    return data_li

if __name__ == '__main__':
    print(md5('faad49866e9498fc1719f5289e7a0269'))
    # a = format_date('2021-01-01 01:01:01')
    # print(a)
    # print(trans_rule_value('date: %Y-%m-01'))
    # print(get_now_time(res_type='datetime'))

