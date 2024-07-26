#-*- coding:utf-8 -*-
from ezetl.utils.common_utils import import_class, trans_dict_to_rules
from ezetl import reader_map, writer_map


def get_reader(model_info, extend_model_dict={}):
    '''
    获取reader对象
    :return:
    '''
    if model_info.get('extract_info') and isinstance(model_info['extract_info'].get('extract_rules'), dict):
        # 若抽取规则为dict形式的，转为列表形式，如{'equal[a]': 1} -> [{{'field': 'a', 'rule': 'equal', 'value': 1}]
        model_info['extract_info']['extract_rules'] = trans_dict_to_rules(model_info['extract_info'].get('extract_rules'))
    source_type = model_info['source'].get('type')
    model_type = model_info['model'].get('type')
    key = f"{source_type}:{model_type}"
    if extend_model_dict != {}:
        for k, v in extend_model_dict.items():
            reader_map[k] = v
    model_class = reader_map.get(key)
    if model_class is None:
        return False, '未找到对应模型'
    try:
        DataModel = import_class(model_class)
        data_model = DataModel(model_info)
        return True, data_model
    except Exception as e:
        return False, str(e)


def get_writer(model_info, extend_model_dict={}):
    '''
    获取writer对象
    :return:
    '''
    source_type = model_info['source'].get('type')
    model_type = model_info['model'].get('type')
    key = f"{source_type}:{model_type}"
    if extend_model_dict != {}:
        for k, v in extend_model_dict.items():
            reader_map[k] = v
    model_class = writer_map.get(key)
    if model_class is None:
        return False, '未找到对应模型'
    try:
        DataModel = import_class(model_class)
        data_model = DataModel(model_info)
        return True, data_model
    except Exception as e:
        return False, str(e)


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

