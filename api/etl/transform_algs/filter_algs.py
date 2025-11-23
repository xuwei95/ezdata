'''
数据清洗过滤类转换算法
'''
import pandas as pd
from etl.utils.common_utils import trans_rule_value, parse_to_list


def empty_to_null(source_data={}, rule_dict={}, context={}):
    '''
    空字符串转null
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [{
        "name": "处理字段列表",
        "value": "fields",
        "form_type": "select_fields",
        "required": true,
        "default": "",
        "tips": ""
    }]
    :return:
    '''
    fields = parse_to_list(rule_dict.get('fields', ''))
    if isinstance(source_data, list):
        for i in range(len(source_data)):
            if isinstance(source_data[i], dict):
               if fields == []:
                   fields = source_data[i].keys()
               for k in fields:
                   if k in source_data[i] and source_data[i][k] == '':
                       source_data[i][k] = None
    elif isinstance(source_data, dict):
        if fields == []:
            fields = source_data.keys()
        for k in fields:
            if k in source_data and source_data[k] == '':
                source_data[k] = None
    else:
        # dataframe处理
        if fields == []:
            fields = source_data.columns
        for k in fields:
            source_data[k] = source_data[k].apply(lambda x: None if x == '' else x)
    return True, source_data


def clean_empty(source_data={}, rule_dict={}, context={}):
    '''
    清除空字符串和null
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [{
        "name": "处理字段列表",
        "value": "fields",
        "form_type": "select_fields",
        "required": true,
        "default": "",
        "tips": ""
    }]
    :return:
    '''
    fields = parse_to_list(rule_dict.get('fields', ''))
    if isinstance(source_data, list):
        for i in range(len(source_data)):
            if isinstance(source_data[i], dict):
               if fields == []:
                   fields = source_data[i].keys()
               for k in fields:
                   if k in source_data[i] and (source_data[i][k] == '' or source_data[i][k] is None):
                       source_data[i].pop(k)
    elif isinstance(source_data, dict):
        if fields == []:
            fields = source_data.keys()
        for k in fields:
            if k in source_data and (source_data[k] == '' or source_data[k] is None):
                source_data.pop(k)
    else:
        return False, '本算法对dataframe类型无效！'
    return True, source_data


def filter_by_rules(source_data={}, rule_dict={}, context={}):
    '''
    根据条件过滤
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [{
        "name": "过滤条件",
        "value": "filter_rules",
        "form_type": "filter_rules",
        "type": "list",
        "must": true,
        "default": [],
        "tips": ""
    }]
    :return:
    '''
    # dataframe处理
    filter_rules = rule_dict.get('filter_rules', [])
    if filter_rules == []:
        return False, '筛选条件不能为空'
    if isinstance(source_data, list):
        df = pd.DataFrame(source_data)
    elif isinstance(source_data, dict):
        df = pd.DataFrame([source_data])
    else:
        df = source_data
    for i in filter_rules:
        print(i)
        field = i.get('field')
        rule = i.get('rule')
        value = i.get('value')
        value = trans_rule_value(value)
        if field and value:
            if rule == 'equal':
                df = df[df[field] == value]
            elif rule == 'f_equal':
                df = df[df[field] != value]
            elif rule == 'gt':
                df = df[df[field] > value]
            elif rule == 'gte':
                df = df[df[field] >= value]
            elif rule == 'lt':
                df = df[df[field] < value]
            elif rule == 'lte':
                df = df[df[field] <= value]
    return True, df
