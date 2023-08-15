'''
orm查询相关函数封装
'''
from web_apps import db
from sqlalchemy import not_
from utils.common_utils import trans_rule_value


def get_base_query(model, filter_delete=True, sort_no=True, sort_id=False, sort_create_time=True):
    '''
    获取基础查询query
    :param model:orm模型
    :param filter_delete:是否过滤已被软删除的
    :param sort_no:是否按照sort_no降序进行排序
    :param sort_id:是否按照id降序进行排序
    :return:
    '''
    query = db.session.query(model)
    if filter_delete:
        query = query.filter(model.del_flag == 0)
    if sort_no:
        query = query.order_by(model.sort_no.desc())
    if sort_id:
        query = query.order_by(model.id.desc())
    if sort_create_time:
        query = query.order_by(model.create_time.desc())
    return query


def gen_filter_rules(query, model, filter_rules):
    '''
    根据筛选条件组成查询
    '''
    for i in filter_rules:
        field = i.get('field')
        rule = i.get('rule')
        value = i.get('value')
        value = trans_rule_value(value)
        if field and value:
            column = getattr(model, field)
            if rule == 'equal':
                query = query.filter(column == value)
            elif rule == 'f_equal':
                query = query.filter(column != value)
            elif rule == 'gt':
                query = query.filter(column > value)
            elif rule == 'lt':
                query = query.filter(column < value)
            elif rule == 'gte':
                query = query.filter(column >= value)
            elif rule == 'lte':
                query = query.filter(column <= value)
            elif rule == 'contain':
                text = f"%{value}%"
                query = query.filter(column.like(text))
            elif rule == 'f_contain':
                text = f"%{value}%"
                query = query.filter(not_(column.like(text)))
            if rule == 'sort_asc':
                query = query.order_by(column)
            elif rule == 'sort_desc':
                query = query.order_by(column.desc())
    return query
