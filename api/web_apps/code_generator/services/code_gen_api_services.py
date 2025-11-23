# coding: utf-8
'''
代码生成api服务
'''
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid
from ..db_models import CodeGenModel
import json
from web_apps.code_generator.services.code_gen_service import CodeGenerator, export_codes_zip, gen_codes_file_list, export_single_file


def serialize_code_gen_model(obj, ser_type='list', field=''):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    if ser_type == 'list':
        dic = obj.to_dict()
        for k in ['query_params', 'buttons', 'fields']:
            dic.pop(k)
    elif ser_type == 'detail':
        dic = obj.to_dict()
        for k in ['query_params', 'buttons', 'fields']:
            dic[k] = json.loads(dic[k])
        if field != '':
            dic = dic.get(field)
    else:
        dic = obj.to_dict()
    return dic


class CodeGenApiService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        user_info = get_auth_token_info()
        username = user_info['username']
        query = get_base_query(CodeGenModel)
        if username != 'admin':
            query = query.filter(CodeGenModel.create_by == username)
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_code_gen_model(obj, ser_type='list')
            result.append(dic)
        return gen_json_response(data=result, extends={'count': total})

    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        field = req_dict.get('field', '')
        obj = db.session.query(CodeGenModel).filter(
            CodeGenModel.id == obj_id,
            CodeGenModel.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_code_gen_model(obj, ser_type='detail', field=field)
        return gen_json_response(data=dic)

    def add_obj(self, req_dict):
        '''
        添加
        '''
        obj = CodeGenModel()
        for key in req_dict.keys():
            if key in ['fields', 'buttons', 'query_params']:
                if isinstance(req_dict[key], list):
                    setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        res_data = serialize_code_gen_model(obj, ser_type='list')
        return gen_json_response(data=res_data, msg='添加成功')

    def edit_obj(self, req_dict):
        '''
        更新
        '''
        obj_id = req_dict.get('id')
        # exist_obj = db.session.query(CodeGenModel).filter(
        #     CodeGenModel.id != obj_id,
        #     CodeGenModel.titole != obj_id,
        #     CodeGenModel.del_flag == 0).first()
        # if exist_obj:
        #     return gen_json_response(code=400, msg='数据已存在')
        obj = db.session.query(CodeGenModel).filter(CodeGenModel.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict.keys():
            if key in req_dict:
                if key in ['fields', 'buttons', 'query_params']:
                    if isinstance(req_dict[key], list):
                        setattr(obj, key, json.dumps(req_dict[key]))
                else:
                    setattr(obj, key, req_dict[key])
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='更新成功')

    def delete_obj(self, req_dict):
        '''
        删除
        '''
        if 'id' in req_dict:
            del_ids = [req_dict['id']]
        elif 'ids' in req_dict:
            del_ids = str(req_dict['ids']).split(',')
        else:
            del_ids = req_dict
        del_objs = db.session.query(CodeGenModel).filter(CodeGenModel.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功')

    def generate_code(self, req_dict):
        '''
        生成代码
        :return:
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(CodeGenModel).filter(CodeGenModel.id == obj_id).first()
        params = obj.to_dict()
        params['fields'] = json.loads(params['fields'])
        params['query_params'] = json.loads(params['query_params'])
        params['buttons'] = json.loads(params['buttons'])
        code_gen = CodeGenerator(params)
        try:
            res_dic = code_gen.generate_all_codes()
            return gen_json_response(data=res_dic)
        except Exception as e:
            return gen_json_response(code=500, msg=str(e))

    def export_code(self, req_dict):
        '''
        导出代码
        :return:
        '''
        output_type = req_dict.get('type')
        data = req_dict.get('data')
        if output_type == 'file':
            output_file = export_single_file(data)
            file_name = data['key']
            return output_file, file_name
        else:
            data_li = data
            print(data_li)
            file_list = gen_codes_file_list(data_li)
            output_file = export_codes_zip(file_list)
            file_name = f"{data_li[0]['key']}.zip"
            return output_file, file_name
