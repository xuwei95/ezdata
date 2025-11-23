'''
数据模型字段api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid, parse_json
from web_apps.datamodel.db_models import DataModelField
from utils.web_utils import validate_params
import pandas as pd
import io
from web_apps.datamodel.services.datamodel_service import gen_extract_info
from utils.etl_utils import get_reader_model


def serialize_datamodel_field_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'datamodel_id', 'field_name', 'field_value', 'ext_params', 'is_sync', 'create_by', 'create_time', 'update_by', 'update_time', 'del_flag', 'sort_no', 'description']:
            if k in ['ext_params']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in ['ext_params']:
            dic[k] = json.loads(dic[k])
        for k in []:
            dic.pop(k)
    elif ser_type == 'all_list':
        res = {}
        for k in ['id', 'datamodel_id', 'field_name', 'field_value']:
            if k in ['ext_params']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
        
    return dic

    
class DataModelFieldApiService(object):
    def __init__(self):
        pass

    def sync_fields(self, req_dict):
        '''
        从模型拉取字段
        '''
        user_info = get_auth_token_info()
        model_id = req_dict.get('id')
        extract_info = {
            'model_id': model_id,
            'extract_rules': parse_json(req_dict.get('extract_rules', [])),
            'search_text': req_dict.get('search_text', ''),
            'search_type': req_dict.get('search_type', '')
        }
        flag, extract_info = gen_extract_info(extract_info)
        if not flag:
            return gen_json_response(code=400, msg='未找到查询配置')
        if user_info['username'] != 'admin':
            model_conf = extract_info['model']
            depart_list = model_conf.get('depart_list')
            org_code = user_info.get('org_code')
            if org_code not in depart_list:
                return gen_json_response(code=400, msg='无权限访问此数据模型')
        flag, reader = get_reader_model(extract_info)
        if not flag:
            return gen_json_response(code=400, msg=reader)
        fields = reader.get_res_fields()
        if fields:
            for field in fields:
                field_obj = get_base_query(DataModelField).filter(DataModelField.datamodel_id == model_id, DataModelField.field_value == field['field_value']).first()
                if field_obj is None:
                    field_obj = DataModelField(
                        id=gen_uuid(),
                        datamodel_id=model_id,
                        field_value=field['field_value']
                    )
                    field_obj.id = gen_uuid(res_type='base')
                    set_insert_user(field_obj)
                else:
                    set_update_user(field_obj)
                field_obj.field_name = field['field_name']
                field_obj.ext_params = json.dumps(parse_json(field.get('ext_params', {}), {}))
                field_obj.is_sync = 1
                db.session.add(field_obj)
                db.session.commit()
                db.session.flush()
        return gen_json_response(msg='同步成功！', extends={'success': True})

    def sync_field(self, req_dict):
        '''
        字段同步到模型
        '''
        user_info = get_auth_token_info()
        field_id = req_dict.get('id')
        field_obj = get_base_query(DataModelField).filter(DataModelField.id == field_id).first()
        if field_obj is None:
            return gen_json_response(code=400, msg='未找到字段')
        model_id = field_obj.datamodel_id
        extract_info = {
            'model_id': model_id,
            'extract_rules': parse_json(req_dict.get('extract_rules', [])),
            'search_text': req_dict.get('search_text', ''),
            'search_type': req_dict.get('search_type', '')
        }
        flag, extract_info = gen_extract_info(extract_info)
        if not flag:
            return gen_json_response(code=400, msg='未找到查询配置')
        if user_info['username'] != 'admin':
            model_conf = extract_info['model']
            depart_list = model_conf.get('depart_list')
            org_code = user_info.get('org_code')
            if org_code not in depart_list:
                return gen_json_response(code=400, msg='无权限访问此数据模型')
        flag, reader = get_reader_model(extract_info)
        if not flag:
            return gen_json_response(code=400, msg=reader)
        try:
            field_dic = {
                'field_name': field_obj.field_name,
                'field_value': field_obj.field_value,
                **json.loads(field_obj.ext_params)
            }
            flag, res = reader.set_field(field_dic)
            if flag:
                return gen_json_response(msg='同步成功！', extends={'success': True})
            else:
                return gen_json_response(code=500, msg=res)
        except Exception as e:
            return gen_json_response(code=500, msg=str(e))

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(DataModelField)
        # datamodel_id 查询逻辑
        datamodel_id = req_dict.get('datamodel_id', '')
        if datamodel_id != '':
            query = query.filter(DataModelField.datamodel_id == datamodel_id)
        # 字段名 查询逻辑
        field_name = req_dict.get('field_name', '')
        if field_name != '':
            query = query.filter(DataModelField.field_name.like("%" + field_name + "%"))
        # 字段值 查询逻辑
        field_value = req_dict.get('field_value', '')
        if field_value != '':
            query = query.filter(DataModelField.field_value.like("%" + field_value + "%"))
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_datamodel_field_model(obj, ser_type='list')
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
        query = get_base_query(DataModelField)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_datamodel_field_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(DataModelField).filter(
            DataModelField.id == obj_id,
            DataModelField.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_datamodel_field_model(obj, ser_type='detail')
        return gen_json_response(data=dic)
    
    def add_obj(self, req_dict):
        '''
        添加
        '''
        datamodel_id = req_dict.get('datamodel_id')
        # 字段名 判重逻辑
        field_name = req_dict.get('field_name', '')
        if field_name != '':
            exist_obj = db.session.query(DataModelField).filter(
                DataModelField.datamodel_id == datamodel_id,
                DataModelField.field_name == field_name,
                DataModelField.del_flag == 0).first()
            if exist_obj:
                return gen_json_response(code=400, msg='字段"字段名"已存在')
        # 字段值 判重逻辑
        field_value = req_dict.get('field_value', '')
        if field_value != '':
            exist_obj = db.session.query(DataModelField).filter(
                DataModelField.datamodel_id == datamodel_id,
                DataModelField.field_value == field_value,
                DataModelField.del_flag == 0).first()
            if exist_obj:
                return gen_json_response(code=400, msg='字段"字段值"已存在')
        obj = DataModelField()
        for key in req_dict:
            if key in ['ext_params']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
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
        datamodel_id = req_dict.get('datamodel_id')
        exist_query = db.session.query(DataModelField).filter(DataModelField.id != obj_id, DataModelField.datamodel_id == datamodel_id,)
        field_name = req_dict.get('field_name', '')
        if field_name != '':
            exist_query = exist_query.filter(DataModelField.field_name == field_name)

        field_value = req_dict.get('field_value', '')
        if field_value != '':
            exist_query = exist_query.filter(DataModelField.field_value == field_value)
        exist_obj = exist_query.first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在')
        obj = db.session.query(DataModelField).filter(DataModelField.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key in ['ext_params']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
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
        del_obj = db.session.query(DataModelField).filter(DataModelField.id == obj_id).first()
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
        del_objs = db.session.query(DataModelField).filter(DataModelField.id.in_(del_ids)).all()
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
            # 字段名 判重逻辑
            field_name_list = [row.get('field_name', '') for row in data_li]
            if field_name_list != []:
                exist_obj = db.session.query(DataModelField).filter(
                    DataModelField.field_name.in_(field_name_list),
                    DataModelField.del_flag == 0).first()
                if exist_obj:
                    return gen_json_response(code=400, msg='字段"字段名"已存在')
            # 字段值 判重逻辑
            field_value_list = [row.get('field_value', '') for row in data_li]
            if field_value_list != []:
                exist_obj = db.session.query(DataModelField).filter(
                    DataModelField.field_value.in_(field_value_list),
                    DataModelField.del_flag == 0).first()
                if exist_obj:
                    return gen_json_response(code=400, msg='字段"字段值"已存在')
            # 循环导入
            for row in data_li:
                obj = DataModelField()
                for key in row:
                    if key in ['ext_params']:
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
        obj_list = db.session.query(DataModelField).filter(DataModelField.id.in_(ids)).all()
        result = []
        for obj in obj_list:
            dic = serialize_datamodel_field_model(obj, ser_type='list')
            result.append(dic)
        df = pd.DataFrame(result)
        # 使用字节流存储
        output = io.BytesIO()
        # 保存文件
        df.to_excel(output, index=False)
        # 文件seek位置，从头(0)开始
        output.seek(0)
        return output