'''
映射类转换算法，字段映射，值映射
'''
from etl.utils.common_utils import format_date, md5, trans_rule_value, parse_json, parse_to_list, trans_value_type


def map_field_names(source_data={}, rule_dict={}, context={}):
    '''
    字段映射
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [{
        "name": "字段映射",
        "value": "field_map",
        "form_type": "field_map",
        "required": true,
        "default": "{}",
        "tips": ""
    }]
    :return:
    '''
    field_map = parse_json(rule_dict.get('field_map'))
    if not field_map:
        return False, '缺少必填参数：字段映射'
    if isinstance(source_data, list):
        for i in range(len(source_data)):
            if isinstance(source_data[i], dict):
                for k in field_map:
                    if k in source_data[i] and field_map[k] and field_map[k] != k:
                        source_data[i][field_map[k]] = source_data[i][k]
                        source_data[i].pop(k)
    elif isinstance(source_data, dict):
        for k in field_map:
            if k in source_data and field_map[k] and field_map[k] != k:
                source_data[field_map[k]] = source_data[k]
                source_data.pop(k)
    else:
        # dataframe处理
        source_data = source_data.rename(columns=field_map)
    return True, source_data


def map_values(source_data={}, rule_dict={}, context={}):
    '''
    字段值映射
    :param source_data: 原始数据
    :param rule_dict: 配置信息
     [{
        "name": "处理字段",
        "value": "fields",
        "form_type": "select_fields",
        "required": true,
        "default": "",
        "tips": ""
    }, {
        "name": "映射字典",
        "value": "value_map",
        "form_type": "codeEditor",
        "required": true,
        "default": "{}",
        "tips": ""
    }, {
        "name": "处理错误时",
        "value": "if_error",
        "form_type": "RadioGroup",
        "required": true,
        "default": "original",
        "options": [{
            "label": "原始值",
            "value": "original"
        }, {
            "label": "置空",
            "value": "empty"
        }],
        "tips": ""
    }]
    :return:
    '''
    fields = parse_to_list(rule_dict.get('fields'))
    if not fields:
        return False, '缺少必填参数：处理字段'
    value_map = parse_json(rule_dict.get('value_map'))
    if not value_map:
        return False, '缺少必填参数：映射字典'
    if_error = rule_dict.get('if_error', 'original')
    if isinstance(source_data, list):
        for i in range(len(source_data)):
            if isinstance(source_data[i], dict):
                for field in fields:
                    if field in source_data[i]:
                        try:
                            source_data[i][field] = value_map.get('%s' % source_data[i][field], source_data[i][field])
                        except Exception as e:
                            print(e)
    elif isinstance(source_data, dict):
        for field in fields:
            if field in source_data:
                try:
                    source_data[field] = value_map.get('%s' % source_data[field], source_data[field])
                except Exception as e:
                    print(e)
    else:
        # dataframe处理
        for field in fields:
            if field in source_data.columns:
                try:
                    source_data[field] = source_data[field].apply(lambda x: value_map.get(x, x))
                except Exception as e:
                    return False, str(e)[:500]
    return True, source_data


def trans_time_format(source_data={}, rule_dict={}, context={}):
    '''
    转换时间格式
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [
      {
        "name": "处理字段",
        "value": "fields",
        "form_type": "select_fields",
        "required": true,
        "default": "",
        "tips": ""
      },
      {
        "name": "日期格式",
        "value": "format",
        "form_type": "input",
        "required": true,
        "default": "%Y-%m-%d %H:%M:%S",
        "tips": ""
      }
    ]
    :return:
    '''
    fields = parse_to_list(rule_dict.get('fields', ''))
    time_format = rule_dict.get('format', '%Y-%m-%d %H:%M:%S')
    if not fields:
        return False, '缺少必填参数：处理字段'
    if isinstance(source_data, list):
        for i in range(len(source_data)):
            if isinstance(source_data[i], dict):
                for field in fields:
                    if field in source_data[i]:
                        try:
                            source_data[i][field] = format_date(source_data[i][field], format=time_format)
                        except Exception as e:
                            print(e)
    elif isinstance(source_data, dict):
        for field in fields:
            if field in source_data:
                try:
                    source_data[field] = format_date(source_data[field], format=time_format)
                except Exception as e:
                    print(e)
    else:
        # dataframe处理
        for field in fields:
            if field in source_data.columns:
                try:
                    source_data[field] = source_data[field].apply(lambda x: format_date(x, format=time_format))
                except Exception as e:
                    return False, str(e)[:500]
    return True, source_data


def trans_field_type(source_data={}, rule_dict={}, context={}):
    '''
    转换字段格式
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [
      {
        "name": "处理字段",
        "value": "fields",
        "form_type": "select_fields",
        "required": true,
        "default": "",
        "tips": ""
      },{
        "name": "转换类型类型",
        "value": "trans_type",
        "form_type": "select",
        "required": true,
        "default": "sum",
        "options": [
            {"label": "字符串", "value": "str"},
            {"label": "整数", "value": "int"},
            {"label": "浮点数", "value": "float"},
            {"label": "日期字符串", "value": "date"},
            {"label": "日期时间", "value": "datetime"},
            {"label": "时间戳", "value": "timestamp"}
        ],
        "tips": ""
    }
    ]
    :return:
    '''
    fields = parse_to_list(rule_dict.get('fields', ''))
    trans_type = rule_dict.get('trans_type', 'string')
    if not fields:
        return False, '缺少必填参数：处理字段'
    if isinstance(source_data, list):
        for i in range(len(source_data)):
            if isinstance(source_data[i], dict):
                for field in fields:
                    if field in source_data[i]:
                        try:
                            source_data[i][field] = trans_value_type(source_data[i][field], trans_type)
                        except Exception as e:
                            print(e)
    elif isinstance(source_data, dict):
        for field in fields:
            if field in source_data:
                try:
                    source_data[field] = trans_value_type(source_data[field], trans_type)
                except Exception as e:
                    print(e)
    else:
        # dataframe处理
        for field in fields:
            if field in source_data.columns:
                try:
                    source_data[field] = source_data[field].apply(lambda x: trans_value_type(x, trans_type))
                except Exception as e:
                    return False, str(e)[:500]
    return True, source_data


def gen_only_id(source_data={}, rule_dict={}, context={}):
    '''
    生成唯一id
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [{
        "name": "唯一字段列表",
        "value": "only_fields",
        "form_type": "select_fields",
        "required": true,
        "default": "",
        "tips": ""
    },{
        "name": "唯一号字段",
        "value": "output_field",
        "form_type": "input",
        "required": true,
        "default": "_id",
        "tips": ""
    }]
    :return:
    '''
    only_fields = parse_to_list(rule_dict.get('only_fields', ''))
    output_field = rule_dict.get('output_field')
    if only_fields == []:
        return False, '唯一字段列表不能为空'
    if not output_field:
        return False, '输出字段不能为空'

    if isinstance(source_data, list):
        for i in range(len(source_data)):
            if isinstance(source_data[i], dict):
                s = ''
                for field in only_fields:
                    s += str(source_data[i].get(field))
                only_id = md5(s)
                source_data[i][output_field] = only_id
    elif isinstance(source_data, dict):
        s = ''
        for field in only_fields:
            s += str(source_data.get(field))
        only_id = md5(s)
        source_data[output_field] = only_id
    else:
        # dataframe处理
        try:
            source_data[output_field] = ''
            for field in only_fields:
                if field in source_data.columns:
                    source_data[output_field] += source_data[field].apply(lambda x: str(x))
            source_data[output_field] = source_data[output_field].apply(lambda x: md5(x))
        except Exception as e:
            return False, str(e)[:500]
    return True, source_data


def add_field(source_data={}, rule_dict={}, context={}):
    '''
    添加字段
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [{
        "name": "字段值",
        "value": "field",
        "form_type": "input",
        "required": true,
        "default": "",
        "tips": ""
    },{
        "name": "默认值",
        "value": "default",
        "form_type": "input",
        "required": true,
        "default": "",
        "tips": ""
    }]
    :return:
    '''
    field = rule_dict.get('field')
    default = trans_rule_value(rule_dict.get('default', ''))
    if not field:
        return False, '字段值不能为空'
    if isinstance(source_data, list):
        for i in range(len(source_data)):
            if isinstance(source_data[i], dict):
               if field not in source_data[i]:
                   source_data[i][field] = default
    elif isinstance(source_data, dict):
        if field not in source_data:
            source_data[field] = default
    else:
        # dataframe处理
        if field not in source_data.columns:
            source_data[field] = default
    return True, source_data
