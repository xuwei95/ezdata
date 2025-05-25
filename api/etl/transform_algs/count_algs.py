'''
统计类转换算法
'''
import pandas as pd
from etl.utils.common_utils import parse_to_list


def group_agg_count(source_data={}, rule_dict={}, context={}):
    '''
    分组聚合统计
    :param source_data: 原始数据
    :param rule_dict: 配置信息
    :param context: 上下文信息
    [{
        "name": "统计字段",
        "value": "count_field",
        "form_type": "select_field",
        "required": true,
        "default": "",
        "tips": ""
    }, {
        "name": "分组字段列表",
        "value": "group_fields",
        "form_type": "select_fields",
        "required": true,
        "default": "",
        "tips": ""
    }, {
        "name": "统计类型",
        "value": "count_type",
        "form_type": "select",
        "required": true,
        "default": "sum",
        "options": [
            {"label": "数量", "value": "count"},
            {"label": "数值总和", "value": "sum"},
            {"label": "平均值", "value": "mean"},
            {"label": "算数平均值", "value": "median"},
            {"label": "标准差", "value": "std"},
            {"label": "方差", "value": "var"},
            {"label": "最小值", "value": "min"},
            {"label": "最大值", "value": "max"},
            {"label": "积", "value": "prod"},
            {"label": "第一个值", "value": "first"},
            {"label": "最后一个值", "value": "last"}
        ],
        "tips": ""
    }]
    :return:
    '''
    count_field = rule_dict.get('count_field')
    count_type = rule_dict.get('count_type', 'sum')
    group_fields = parse_to_list(rule_dict.get('group_fields', ''))
    if group_fields == []:
        return False, '分组字段列表不能为空'
    if not count_field:
        return False, '统计字段不能为空'
    try:
        if isinstance(source_data, list):
            df = pd.DataFrame(source_data)
        elif isinstance(source_data, dict):
            df = pd.DataFrame([source_data])
        else:
            df = source_data
        # dataframe处理
        group_keys = [i for i in group_fields if i in df.columns]
        agg_df = df.groupby(group_keys, as_index=False).agg({count_field: count_type})
        return True, agg_df
    except Exception as e:
        return False, str(e)[:500]


