'''
内容获取类转换算法
'''
from utils.common_utils import trans_rule_value, parse_to_list


def code_transform(source_data=[], rule_dict={}, context={}):
    '''
    自定义代码转换数据
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [{
        "name": "语言",
        "value": "language",
        "form_type": "select",
        "required": true,
        "default": "python",
        "options": [{"label": "python", "value": "python"}],
        "tips": ""
    },{
        "name": "代码",
        "value": "code",
        "form_type": "codeEditor",
        "required": true,
        "default": "",
        "tips": ""
    }]
    :return:
    '''
    language = rule_dict.get('language', 'python')
    code = trans_rule_value(rule_dict.get('code'))
    if not code:
        return False, '代码不能为空'
    if language == 'python':
        try:
            exec(code, globals())
            # 调用动态代码中transform函数转换数据
            results = transform(source_data)
            return True, results
        except Exception as e:
            return False, str(e)
    return False, '处理失败'


def data_to_df(source_data=[], rule_dict={}, context={}):
    '''
    将数据转为dataframe
    [{
        "name": "dataframe类型",
        "value": "engine",
        "form_type": "select",
        "required": true,
        "default": "pandas",
        "options": [{"label": "pandas", "value": "pandas"},{"label": "xorbits", "value": "xorbits"}],
        "tips": ""
    }]
    '''
    engine = rule_dict.get('engine', 'pandas')
    if isinstance(source_data, dict):
        source_data = [source_data]
    if engine == 'xorbits':
        import xorbits
        xorbits_cluster = rule_dict.get('xorbits_cluster', 'local')
        if xorbits_cluster != 'local':
            xorbits.init(xorbits_cluster)
        import xorbits.pandas as pd
    else:
        import pandas as pd
    df = pd.DataFrame(source_data)
    return True, df


def df_to_data(source_data=[], rule_dict={}, context={}):
    '''
    dataframe转回原始数据
    []
    '''
    try:
        if not isinstance(source_data, list) and not isinstance(source_data, dict):
            data_li = source_data.to_dict(orient='records')
            return True, data_li
        else:
            return True, source_data
    except Exception as e:
        return False, str(e)[:500]


def gen_records_list(source_data=[], rule_dict={}, context={}):
    '''
    解析接口返回内容列表信息
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [{
        "name": "字段列表",
        "value": "fields",
        "form_type": "select_fields",
        "required": false,
        "default": "",
        "tips": ""
    }]
    :return:
    '''
    output = []
    fields = parse_to_list(rule_dict.get('fields', ''))
    if isinstance(source_data, dict):
        records = source_data['records']
        for c in records:
            if fields == []:
                dic = c
            else:
                dic = {}
                for field in fields:
                    dic[field] = c.get(field, '')
            output.append(dic)
    return True, output


def gen_contents_first(source_data=[], rule_dict={}, context={}):
    '''
    解析接口第一条数据
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [{
        "name": "字段",
        "value": "fields",
        "form_type": "select_fields",
        "required": true,
        "default": "",
        "tips": ""
    }]
    :return:
    '''
    fields = parse_to_list(rule_dict.get('fields', ''))
    if isinstance(source_data, dict):
        records = source_data.get('records')
    else:
        records = source_data
    if not records or len(records) == 0:
        return False, '获取数据失败'
    dic = {}
    for field in fields:
        dic[field] = records[0].get(field, '')
    output = [
      dic
    ]
    return True, output


def gen_contents_total(source_data=[], rule_dict={}, context={}):
    '''
    获取总数
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    []
    :return:
    '''
    if isinstance(source_data, dict):
        total_num = source_data.get('total')
    else:
        total_num = len(source_data)
    output = [
        {
            'num': total_num
        }
    ]
    return True, output


def gen_es_aggs_buckets(source_data=[], rule_dict={}, context={}):
    '''
    解析es接口返回聚合统计信息
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [{
        "name": "统计字段",
        "value": "field",
        "form_type": "select_fields",
        "required": true,
        "default": "",
        "tips": ""
    }, {
        "name": "是否包含其它",
        "value": "include_other",
        "form_type": "switch",
        "required": true,
        "default": false,
        "tips": ""
    }]
    :return:
    '''
    output = []
    field = rule_dict.get('field')
    if not field:
        return False, '缺少必填参数：统计字段'
    aggs = source_data.get('aggs', {})
    res_dic = aggs.get(field)
    if not res_dic or 'buckets' not in res_dic:
        return False, '未找到接口统计字段信息'
    for i in res_dic['buckets']:
        output.append({
            "value": i['doc_count'],
            "name": i['key']
        })
    if rule_dict.get('include_other'):
        output.append({
            "value": res_dic['sum_other_doc_count'],
            "name": '其它'
        })
    return True, output


def gen_es_aggs_value(source_data=[], rule_dict={}, context={}):
    '''
    解析聚类统计数值
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    [{
        "name": "字段",
        "value": "field",
        "form_type": "select_field",
        "required": true,
        "default": "",
        "tips": ""
    }]
    :return:
    '''
    field = rule_dict.get('field')
    if not field:
        return False, '缺少必填参数：字段'
    aggs = source_data.get('aggs')
    if not aggs or aggs == {}:
        return False, '获取数据失败'
    count_res = aggs.get(field)
    if 'value' not in count_res:
        return False, '获取数据失败'
    output = [
      {
        "value": count_res['value']
      }
    ]
    return True, output


