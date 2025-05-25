# coding: utf-8
'''
数据大屏服务
'''
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid
from utils.cache_utils import set_key_exp, get_key_value
from .db_models import ScreenProject
import json
from sqlalchemy import or_


def serialize_screen(obj, ser_type='list'):
    '''
    序列化大屏数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = {
        'createTime': str(obj.create_time),
        'createUser': obj.create_by,
        'id': obj.id,
        'indexImage': obj.index_image,
        'isDelete': obj.del_flag,
        'projectName': obj.project_name,
        'remarks': obj.remarks,
        'state': obj.state
    }
    if ser_type == 'list':
        return dic
    elif ser_type == 'detail':
        dic['content'] = obj.content
    return dic


class ScreenService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = req_dict.get('page', 1)
        limit = req_dict.get('limit', 12)
        user_info = get_auth_token_info()
        username = user_info['username']
        query = get_base_query(ScreenProject)
        if username != 'admin':
            query = query.filter(ScreenProject.create_by == username)
        total = query.count()
        page = int(page)
        pagesize = int(limit)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_screen(obj, ser_type='list')
            result.append(dic)
        return gen_json_response(data=result, extends={'count': total})

    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('projectId')
        obj = db.session.query(ScreenProject).filter(
            ScreenProject.id == obj_id,
            ScreenProject.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_screen(obj, ser_type='detail')
        return gen_json_response(data=dic)

    def add_obj(self, req_dict):
        '''
        添加
        '''
        projectName = req_dict.get('projectName')
        exist_obj = db.session.query(ScreenProject).filter(
            ScreenProject.project_name == projectName,
            ScreenProject.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在！')
        obj = ScreenProject()
        obj.id = gen_uuid(res_type='base')
        obj.project_name = req_dict.get('projectName')
        obj.remarks = req_dict.get('remarks', '')
        obj.index_image = req_dict.get('indexImage', '')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        res_data = serialize_screen(obj, ser_type='list')
        return gen_json_response(data=res_data, msg='添加成功。')

    def update_obj(self, req_dict):
        '''
        更新
        '''
        obj_id = req_dict.get('id')
        projectName = req_dict.get('projectName')
        exist_obj = db.session.query(ScreenProject).filter(
            ScreenProject.id != obj_id,
            ScreenProject.project_name == projectName,
            ScreenProject.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在！')
        obj = db.session.query(ScreenProject).filter(ScreenProject.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='找不到该对象！')
        project_name = req_dict.get('projectName')
        if project_name:
            obj.project_name = project_name
        obj.remarks = req_dict.get('remarks', '')
        index_image = req_dict.get('indexImage', '')
        if index_image != '':
            obj.index_image = index_image
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='更新成功。')

    def save_obj_data(self, req_dict):
        '''
        更新数据
        '''
        obj_id = req_dict.get('projectId')
        obj = db.session.query(ScreenProject).filter(ScreenProject.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='找不到该对象！')
        obj.content = req_dict.get('content')
        project_name = req_dict.get('projectName')
        if project_name:
            obj.project_name = project_name
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='更新成功。')

    def handle_publish_obj(self, req_dict):
        '''
        发布
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(ScreenProject).filter(ScreenProject.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='找不到该对象！')
        obj.state = req_dict.get('state')
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='更新成功。')

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
        del_objs = db.session.query(ScreenProject).filter(ScreenProject.id.in_(del_ids)).all()
        print(del_objs)
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功。')
