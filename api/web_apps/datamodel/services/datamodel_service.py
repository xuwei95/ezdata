'''
数据源管理服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from web_apps.datasource.db_models import DataSource
from web_apps.datamodel.db_models import DataModel, DataModelField


def gen_datasource_conf(datasource_obj):
    '''
    组合数据源配置
    :return:
    '''
    if isinstance(datasource_obj, str):
        datasource_obj = db.session.query(DataSource).filter(DataSource.id == datasource_obj).first()
        if datasource_obj is None:
            return None
    conf = {
        'name': datasource_obj.name,
        'type': datasource_obj.type,
        'conn_conf': json.loads(datasource_obj.conn_conf),
        'ext_params': json.loads(datasource_obj.ext_params),
    }
    return conf


def gen_datamodel_conf(data_model_obj):
    '''
    组合数据模型配置
    :return:
    '''
    if isinstance(data_model_obj, str):
        data_model_obj = get_base_query(DataModel).filter(DataModel.id == data_model_obj).first()
        if data_model_obj is None:
            return None
    model_conf = {
        'id': data_model_obj.id,
        'datasource_id': data_model_obj.datasource_id,
        'can_interface': data_model_obj.can_interface,
        "name": data_model_obj.name,
        "type": data_model_obj.type,
        "model_conf": json.loads(data_model_obj.model_conf),
        "ext_params": json.loads(data_model_obj.ext_params),
        'depart_list': json.loads(data_model_obj.depart_list),
    }
    field_objs = get_base_query(DataModelField).filter(DataModelField.datamodel_id == data_model_obj.id).all()
    fields = []
    for i in field_objs:
        dic = {
            'field_name': i.field_name,
            'field_value': i.field_value,
            **json.loads(i.ext_params)
        }
        fields.append(dic)
    model_conf['fields'] = fields
    return model_conf


def gen_datasource_model_info(datasource_id):
    '''
    根据单数据源组合数据模型配置
    :return:
    '''
    datasource_obj = db.session.query(DataSource).filter(DataSource.id == datasource_id).first()
    _source = gen_datasource_conf(datasource_obj)
    model_info = {
        'source': _source,
        'model': {},
        'extract_info': {
            'batch_size': 1,
            'extract_rules': []
        }
    }
    return True, model_info


def gen_extract_info(extract_info):
    '''
    生成数据抽取配置
    :param extract_info:
    :return:
    '''
    if 'model_id' in extract_info:
        # todo: redis缓存
        datamodel_obj = db.session.query(DataModel).filter(DataModel.id == extract_info['model_id']).first()
        if datamodel_obj:
            _source = gen_datasource_conf(datamodel_obj.datasource_id)
            _model = gen_datamodel_conf(datamodel_obj)
            extract_rules = extract_info.get('extract_rules', [])
            # 将高级查询加入抽取规则
            search_text = extract_info.get('search_text', '')
            search_type = extract_info.get('search_type', '')
            if search_type != '' and search_text != '':
                extract_rules.append({'field': 'search_text', 'rule': search_type, 'value': search_text})
            model_info = {
                'source': _source,
                'model': _model,
                'extract_info': {
                    'batch_size': extract_info.get('batch_size', 1000),
                    'extract_rules': extract_rules
                }
            }
            return True, model_info
        else:
            return False, '未找到对应数据模型'
    return False, None


def gen_load_info(load_info):
    '''
    生成数据装载配置
    :param load_info:
    :return:
    '''
    if 'model_id' in load_info:
        # todo: redis缓存
        datamodel_obj = db.session.query(DataModel).filter(DataModel.id == load_info['model_id']).first()
        if datamodel_obj:
            _source = gen_datasource_conf(datamodel_obj.datasource_id)
            _model = gen_datamodel_conf(datamodel_obj)
            model_info = {
                'source': _source,
                'model': _model,
                'load_info': {
                    'load_type': load_info.get('load_type', 'insert'),
                    'only_fields': load_info.get('only_fields')
                }
            }
            return True, model_info
        else:
            return False, '未找到对应数据模型'
    return False, None
