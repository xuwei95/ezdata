'''
ES 创建，删除，更新索引等操作封装函数
'''


def get_mapping(data_fields):
    '''
    根据字段组成es mapping
    :return:
    '''
    mapping = {}
    mapping['properties'] = {}
    for field in data_fields:
        mapping['properties'][field.field_value] = {}
        mapping['properties'][field.field_value]['type'] = field.field_type
        if field.field_type == 'date':
            mapping['properties'][field.field_value]['format'] = "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
    return mapping


def set_mapping_field(index_name, field, es=None):
    '''
    根据字段设置es mapping
    :param data_id:
    :return:
    '''
    if es is None:
        raise ValueError('缺少es client')
    mapping = {}
    mapping['properties'] = {}
    mapping['properties'][field.field_value] = {}
    mapping['properties'][field.field_value]['type'] = field.field_type
    if field.field_type == 'date':
        mapping['properties'][field.field_value]['format'] = "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
    try:
        print(mapping)
        es.create_mapping(index_name, mapping)
    except Exception as e:
        print(e)


def get_index_mapping(index_name, es=None):
    '''
    获取es mapping
    :param data_id:
    :return:
    '''
    if es is None:
        raise ValueError('缺少es client')
    try:
        mapping = es.get_mapping(index_name)
        return mapping
    except Exception as e:
        print(e)
        return None


def clean_index(index_name, es=None):
    '''
    清空索引
    :return:
    '''
    if es is None:
        raise ValueError('缺少es client')
    if index_name is None:
        res_data = {
            'code': 400,
            'msg': '未找到索引',
        }
        return res_data
    # 删除索引，重建mapping
    res = es.delete_index(index_name)
    print(res, index_name)
    res_data = {
        'code': 200,
        'msg': '清空成功',
    }
    return res_data


def trans_es_field(field, db_type='mysql'):
    '''
    将es字段类型转化为其他数据库字段类型
    :param field:
    :param db_type:
    :return:
    '''
    if db_type == 'mysql':
        if field['type'] in ['keyword', 'text', 'nested']:
            field['type'] = 'text'
        if field['type'] == 'integer':
            field['type'] = 'int'
        if field['type'] == 'date':
            field['type'] = 'datatime'
    return field


def filter_es_api_field(dic):
    '''
    过滤掉接口带的es字段
    :return:
    '''
    dic['_id'] = dic['id']
    dic.pop('id')
    dic.pop('_index')
    dic.pop('_score')
    dic.pop('_type')
    return dic

