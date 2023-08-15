# coding: utf-8
'''
职务模块服务
'''
import json
from web_apps import db
from models import User, Position, PerMission
from utils.auth import encode_auth_token, set_insert_user, set_update_user
from utils.web_utils import get_user_ip
from utils.common_utils import get_now_time, gen_json_response
from utils.query_utils import get_base_query
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_


class PositionService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        query = get_base_query(Position)
        name = req_dict.get('name', '')
        if name != '':
            search_text = f"%{name}%"
            query = query.filter(Position.name.like(search_text))
        total = query.count()
        page = int(page)
        pagesize = int(pagesize)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = obj.to_dict()
            dic['id'] = str(dic['id'])
            dic['post_rank'] = str(dic['post_rank'])
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(res_data)

    def get_obj_info(self, req_dict):
        '''
        获取信息
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Position).filter(Position.id == obj_id).first()
        dic = obj.to_dict()
        dic['post_rank'] = str(dic['post_rank'])
        return gen_json_response(dic)

    def add_obj(self, req_dict):
        '''
        添加
        '''
        code = req_dict.get('code', '')
        exist_obj = db.session.query(Position).filter(Position.code == code, Position.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='职务编码已存在！')
        obj = Position()
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
        code = req_dict.get('code', '')
        exist_obj = db.session.query(Position).filter(Position.id != obj_id,
                                                      Position.code == code,
                                                      Position.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='职务编码已存在！')
        obj = db.session.query(Position).filter(Position.id == obj_id).first()
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
        del_objs = db.session.query(Position).filter(Position.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.flush()
        return gen_json_response(msg='删除成功。', extends={'success': True})

