# coding: utf-8
'''
角色模块服务
'''
import json
from web_apps import db
from models import User, Role, PerMission
from utils.auth import encode_auth_token, set_insert_user, set_update_user
from utils.web_utils import get_user_ip
from utils.common_utils import get_now_time, gen_json_response
from utils.query_utils import get_base_query
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_


class RoleService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        query = get_base_query(Role)
        #  search_text 查询逻辑
        search_text = req_dict.get('search_text', '')
        if search_text != '':
            search_text = f"%{search_text}%"
            query = query.filter(Role.role_name.like(search_text))
        total = query.count()
        page = int(page)
        pagesize = int(pagesize)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = obj.to_dict()
            dic['permissions'] = json.loads(dic['permissions'])
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(res_data)

    def get_obj_all_list(self, req_dict):
        '''
        获取所有角色列表
        :param req_dict:
        :return:
        '''
        query = get_base_query(Role)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = {
                'id': str(obj.id),
                'role_name': obj.role_name,
                'role_code': obj.role_code
            }
            result.append(dic)
        return gen_json_response(result)

    def add_obj(self, req_dict):
        '''
        添加
        '''
        role_code = req_dict.get('role_code', '')
        exist_obj = db.session.query(Role).filter(Role.role_code == role_code, Role.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='角色编码已存在！')
        obj = Role()
        for k in req_dict:
            setattr(obj, k, req_dict[k])
        set_insert_user(obj)
        db.session.add(obj)
        db.session.flush()
        return gen_json_response(msg='添加成功。', extends={'success': True})

    def update_obj(self, req_dict):
        '''
        更新
        '''
        obj_id = req_dict.get('id')
        role_code = req_dict.get('role_code', '')
        exist_obj = db.session.query(Role).filter(Role.id != obj_id,
                                                  Role.role_code == role_code,
                                                  Role.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='角色编码已存在！')
        obj = db.session.query(Role).filter(Role.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='找不到该对象！')
        for k in req_dict:
            setattr(obj, k, req_dict[k])
        set_update_user(obj)
        db.session.add(obj)
        db.session.flush()
        return gen_json_response(msg='更新成功。', extends={'success': True})

    def delete_obj(self, req_dict):
        '''
        删除
        '''
        if 'id' in req_dict:
            del_ids = [req_dict['id']]
        elif 'ids' in req_dict:
            del_ids = req_dict['ids']
        else:
            del_ids = req_dict
        del_objs = db.session.query(Role).filter(Role.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.flush()
        return gen_json_response(msg='删除成功。', extends={'success': True})

