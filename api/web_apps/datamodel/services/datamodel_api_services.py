'''
数据模型管理api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid, parse_json
from web_apps.datamodel.db_models import DataModel
from web_apps.datasource.db_models import DataSource
from web_apps.datamodel.services.datamodel_service import gen_extract_info
from utils.etl_utils import get_reader_model
from utils.web_utils import validate_params
import pandas as pd
import io
import logging
from etl.registry import get_registry
from utils.common_utils import import_class

logger = logging.getLogger(__name__)
registry = get_registry()

def serialize_datamodel_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'name', 'datasource_id', 'type', 'status', 'can_interface', 'model_conf', 'ext_params', 'create_by', 'create_time', 'update_by', 'update_time', 'del_flag', 'sort_no', 'description', 'depart_list']:
            if k in ['model_conf', 'ext_params', 'depart_list']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in ['model_conf', 'depart_list']:
            dic[k] = json.loads(dic[k])
    elif ser_type == 'all_list':
        res = {}
        for k in ['id', 'name', 'datasource_id', 'type']:
            if k in ['model_conf', 'ext_params']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'tree':
        res = {
            "type": 'datamodel',
            "icon": '',
            "isLeaf": True,
            "key": str(obj.id),
            "label": str(obj.name),
            "title": str(obj.name),
            "slotTitle": str(obj.name),
            "value": str(obj.id),
        }
        return res
    return dic


def get_datamodel_tree(obj_list):
    '''
    获取数据模型树
    '''
    datasource_ids = list(set([i.datasource_id for i in obj_list]))
    datasource_objs = get_base_query(DataSource).filter(DataSource.id.in_(datasource_ids)).all()
    tree_data = []
    for datasource_obj in datasource_objs:
        dic = {
            "type": 'datasource',
            "icon": '',
            "isLeaf": False,
            "key": str(datasource_obj.id),
            "label": str(datasource_obj.name),
            "title": str(datasource_obj.name),
            "slotTitle": str(datasource_obj.name),
            "value": str(datasource_obj.id)
        }
        child_models = [i for i in obj_list if i.datasource_id == datasource_obj.id]
        dic['children'] = [serialize_datamodel_model(obj, ser_type='tree') for obj in child_models]
        tree_data.append(dic)
    return tree_data


class DataModelApiService(object):
    def __init__(self):
        pass

    def get_obj_tree(self, req_dict):
        '''
        获取数据模型树
        '''
        user_info = get_auth_token_info()
        keyWord = req_dict.get('keyWord', '')
        query = get_base_query(DataModel, sort_create_time=False).filter(DataModel.can_interface == 1, DataModel.status == 1)
        if user_info['username'] != 'admin':
            org_code = user_info.get('org_code')
            query = query.filter(DataModel.depart_list.like(f'%"{org_code}"%'))
        if keyWord != '':
            query = query.filter(DataModel.name.like(f'%"{keyWord}"%'))
        obj_list = query.all()
        res_data = get_datamodel_tree(obj_list)
        return gen_json_response(data=res_data)

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(DataModel)
        
        # 名称 查询逻辑
        name = req_dict.get('name', '')
        if name != '':
            query = query.filter(DataModel.name.like("%" + name + "%"))
        # 所属数据源 查询逻辑
        datasource_id = req_dict.get('datasource_id', '')
        if datasource_id != '':
            query = query.filter(DataModel.datasource_id == datasource_id)
        # 类型 查询逻辑
        _type = req_dict.get('type', '')
        if _type != '':
            query = query.filter(DataModel.type == _type)
        # 是否同步 查询逻辑
        is_sync = req_dict.get('is_sync', '')
        if is_sync != '':
            query = query.filter(DataModel.is_sync == is_sync)
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_datamodel_model(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)
    
    def get_obj_all_list(self, req_dict):
        '''
        获取全量列表
        '''
        auth_type = req_dict.get('auth_type', '')
        query = get_base_query(DataModel)
        obj_list = query.all()
        if auth_type != '':
            obj_list = [obj for obj in obj_list if auth_type in parse_json(obj.model_conf, {}).get('auth_type', '').split(',')]
        result = []
        for obj in obj_list:
            dic = serialize_datamodel_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(DataModel).filter(
            DataModel.id == obj_id,
            DataModel.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_datamodel_model(obj, ser_type='detail')
        return gen_json_response(data=dic)

    def add_obj(self, req_dict):
        '''
        添加
        '''
        # 名称 判重逻辑
        name = req_dict.get('name', '')
        if name != '':
            exist_obj = db.session.query(DataModel).filter(
                DataModel.datasource_id == req_dict.get('datasource_id', ''),
                DataModel.name == name,
                DataModel.del_flag == 0).first()
            if exist_obj:
                return gen_json_response(code=400, msg='字段"名称"已存在')
        obj = DataModel()
        for key in req_dict:
            if key in ['model_conf']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'depart_list':
                li = req_dict.get(key, "").split(',')
                if li == ['']:
                    li = []
                setattr(obj, key, json.dumps(li))
            elif key == 'ext_params':
                try:
                    json_value = json.loads(req_dict[key])
                    obj.ext_params = json.dumps(json_value, ensure_ascii=False, indent=2)
                except Exception as e:
                    return gen_json_response(code=400, msg='额外参数必须是json格式')
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        # 创建后检查一次状态
        try:
            flag, extract_info = gen_extract_info({
                'model_id': obj.id,
            })
            if not flag:
                return gen_json_response(code=400, msg='未找到查询配置')
            flag, reader = get_reader_model(extract_info)
            if not flag:
                return gen_json_response(code=400, msg=reader)
            flag, res = reader.connect()
            if flag:
                obj.status = 1
            else:
                obj.status = 0
                print(res)
        except Exception as e:
            print(e)
            obj.status = 0
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='添加成功', extends={'success': True})
    
    def edit_obj(self, req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        # 判重逻辑
        exist_query = db.session.query(DataModel).filter(DataModel.id != obj_id, DataModel.del_flag == 0)
        name = req_dict.get('name', '')
        if name != '':
            exist_query = exist_query.filter(DataModel.datasource_id == req_dict.get('datasource_id', ''), DataModel.name == name)
        exist_obj = exist_query.first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在')
        obj = db.session.query(DataModel).filter(DataModel.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key in ['model_conf']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'depart_list':
                li = req_dict.get(key, "").split(',')
                if li == ['']:
                    li = []
                setattr(obj, key, json.dumps(li))
            elif key == 'ext_params':
                try:
                    json_value = json.loads(req_dict[key])
                    obj.ext_params = json.dumps(json_value, ensure_ascii=False, indent=2)
                except Exception as e:
                    return gen_json_response(code=400, msg='额外参数必须是json格式')
            else:
                setattr(obj, key, req_dict[key])
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='编辑成功', extends={'success': True})
    
    def delete_obj(self, req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(DataModel).filter(DataModel.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        del_obj.del_flag = 1
        set_update_user(del_obj)
        db.session.add(del_obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    def delete_batch(self, req_dict):
        '''
        批量删除
        '''
        del_ids = req_dict.get('ids')
        if isinstance(del_ids, str):
            del_ids = del_ids.split(',')
        del_objs = db.session.query(DataModel).filter(DataModel.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    def importExcel(self, file):
        '''
        excel导入
        '''
        try:
            df = pd.read_excel(file, dtype=object)
            df.fillna("", inplace=True)
            # 校验上传字段
            data_li = []
            n = 2
            for k, row in df.iterrows():
                row = row.to_dict()
                verify_dict = {
                    "name": {
                        "name": "名称",
                        "required": True
                    },
                    "is_sync": {
                        "name": "是否同步",
                        "required": True
                    }
                }
                not_valid = validate_params(row, verify_dict)
                if not_valid:
                    not_valid = {
                        'code': 400,
                        'msg': f'第{n}行{not_valid}'
                    }
                    return not_valid
                data_li.append(row)
                n += 1
            # 名称 判重逻辑
            name_list = [row.get('name', '') for row in data_li]
            if name_list != []:
                exist_obj = db.session.query(DataModel).filter(
                    DataModel.name.in_(name_list),
                    DataModel.del_flag == 0).first()
                if exist_obj:
                    return gen_json_response(code=400, msg='字段"名称"已存在')
            # 循环导入
            for row in data_li:
                obj = DataModel()
                for key in row:
                    if key in ['model_conf', 'ext_params']:
                        setattr(obj, key, json.dumps(row[key], ensure_ascii=False, indent=2))
                    else:
                        setattr(obj, key, row[key])
                obj.id = gen_uuid(res_type='base')
                set_insert_user(obj)
                db.session.add(obj)
                db.session.commit()
                db.session.flush()
            return gen_json_response(code=200, msg='导入成功', extends={'success': True})
        except Exception as e:
            return gen_json_response(code=500, msg=f'导入错误{e}')
    
    def exportXls(self, req_dict):
        '''
        导出excel
        '''
        selections = req_dict.get('selections', '')
        ids = selections.split(',')
        obj_list = db.session.query(DataModel).filter(DataModel.id.in_(ids)).all()
        result = []
        for obj in obj_list:
            dic = serialize_datamodel_model(obj, ser_type='list')
            result.append(dic)
        df = pd.DataFrame(result)
        # 使用字节流存储
        output = io.BytesIO()
        # 保存文件
        df.to_excel(output, index=False)
        # 文件seek位置，从头(0)开始
        output.seek(0)
        return output

    def get_model_types(self, req_dict):
        '''
        根据数据源ID获取可用的数据模型类型列表
        '''
        datasource_id = req_dict.get('datasource_id')

        if not datasource_id:
            return gen_json_response(code=400, msg='数据源ID不能为空')

        # 获取数据源信息
        datasource = db.session.query(DataSource).filter(
            DataSource.id == datasource_id,
            DataSource.del_flag == 0).first()

        if not datasource:
            return gen_json_response(code=400, msg='数据源不存在')

        datasource_type = datasource.type
        try:
            reader_map = registry.get_reader_map()

            # 筛选出该数据源类型支持的模型类型
            model_types = []
            for key in reader_map.keys():
                source_type, model_type = key.split(':', 1)
                if source_type == datasource_type and model_type != 'None':
                    # 检查是否是自定义 handler（不在标准 MindsDB handlers 中的）
                    label = self._generate_model_type_label(model_type)
                    model_types.append({
                        'label': label,
                        'value': model_type
                    })
            return gen_json_response(data=model_types)
        except Exception as e:
            logger.error(f"获取数据模型类型失败: {e}")
            return gen_json_response(code=500, msg=f'获取数据模型类型失败: {str(e)}')

    def get_model_config(self, req_dict):
        '''
        获取模型配置表单
        通过调用模型类的get_form_config方法获取配置
        '''
        model_key = req_dict.get('model_key')
        if not model_key:
            return gen_json_response(code=400, msg='model_key不能为空')

        try:
            reader_map = registry.get_reader_map()

            model_class = None
            for key, handler_class_path in reader_map.items():
                if key == model_key:
                    model_class = import_class(handler_class_path)
                    logger.info(f"匹配找到模型类: {key} -> {handler_class_path}")
                    break
            # 调用模型类的get_form_config方法获取配置
            if model_class and hasattr(model_class, 'get_form_config'):
                config = model_class.get_form_config()
                logger.info(f"获取模型类型 {model_key}的配置成功: {config}")
                return gen_json_response(data=config)
            else:
                return gen_json_response(data={})

        except Exception as e:
            logger.error(f"获取数据模型配置失败: {e}", exc_info=True)
            return gen_json_response(code=500, msg=f'获取数据模型配置失败: {str(e)}')

    def _generate_model_type_label(self, model_type):
        '''
        生成模型类型的友好标签
        '''
        # 模型类型标签映射
        label_map = {
            'sql': 'SQL',
            'table': 'Table',
            'mysql_binlog': 'MySQL Binlog',
            'kafka_topic': 'Kafka Topic',
            'akshare_api': 'AkShare api',
            'ccxt_api': 'CCXT api'
        }
        if 'table' in model_type:
            return 'table'
        base_label = label_map.get(model_type, model_type)
        return base_label
