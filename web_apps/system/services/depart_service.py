# coding: utf-8
'''
机构/部门模块服务
'''
import json
from web_apps import db
from models import User, Role, PerMission, Depart
from utils.auth import encode_auth_token, set_insert_user, set_update_user
from utils.web_utils import get_user_ip, validate_params
from utils.common_utils import get_now_time, gen_json_response
from utils.query_utils import get_base_query
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_


def serialize_depart(obj, ser_type='list'):
    '''
    序列化部门数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = {}
    if ser_type == 'list':
        dic = {
            'address': obj.address,
            'create_by': obj.create_by,
            'create_time': obj.create_time,
            'del_flag': obj.del_flag,
            'depart_name': obj.depart_name,
            'depart_name_abbr': obj.depart_name_abbr,
            'depart_name_en': obj.depart_name_en,
            'sort_no': obj.sort_no,
            'description': obj.description,
            'director_user_ids': None,
            'fax': obj.fax,
            'id': obj.id,
            'is_leaf': obj.is_leaf == 1,
            'key': str(obj.id),
            'memo': obj.memo,
            'mobile': obj.mobile,
            'org_category': str(obj.org_category),
            'org_code': obj.org_code,
            'org_type': obj.org_type,
            'parent_id': obj.parent_id,
            'qywx_identifier': obj.qywx_identifier,
            'status': obj.status,
            'title': obj.depart_name,
            'update_by': obj.update_by,
            'update_time': obj.update_time,
            'value': obj.id
        }
    elif ser_type == 'id':
        dic = {
            'key': str(obj.id),
            'title': obj.depart_name,
            'value': str(obj.id)
        }
    return dic


def get_depart_children(depart_obj, ser_type='list'):
    '''
    找到权限的下级权限
    '''
    children = []
    child_objs = get_base_query(Depart).filter(Depart.parent_id == depart_obj.id).all()
    if child_objs == []:
        return None
    for obj in child_objs:
        dic = serialize_depart(obj, ser_type)
        dic['children'] = get_depart_children(obj, ser_type)
        children.append(dic)
    return children


def check_valid(req_dict):
    '''
    校验部门添加/更新是否符合条件
    :param req_dict:
    :return:
    '''
    # 机构类型 1一级部门 2子部门
    org_type = req_dict.get('org_type')
    # 机构类别 1公司，2组织机构，2岗位
    org_category = req_dict.get('org_category')
    verify_dict = {
        'depart_name': {
            'name': '机构/部门名称',
            'not_empty': True
        }
    }
    # if menu_type in [0, 1]:
    #     verify_dict['url'] = {
    #         'name': '访问路径',
    #         'not_empty': True
    #     }
    #     verify_dict['component'] = {
    #         'name': '前端组件',
    #         'not_empty': True
    #     }
    # if menu_type in [1, 2]:
    #     verify_dict['parent_id'] = {
    #         'name': '上级菜单',
    #         'not_empty': True
    #     }
    #     # 同级菜单名称和url不能重复
    #     parent_id = req_dict.get('parent_id')
    #     if parent_id:
    #         child_list = get_base_query(PerMission).filter(PerMission.parent_id == parent_id).all()
    #         _id = req_dict.get('id')
    #         exist_list = [i for i in child_list if
    #                       str(i.id) != str(_id) and (i.name == req_dict.get('name') or i.url == req_dict.get('url'))]
    #         if exist_list != []:
    #             return False, '同级菜单名称或路径已存在'
    # if menu_type == 2:
    #     verify_dict['name'] = {
    #         'name': '菜单/权限',
    #         'not_empty': True
    #     }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return False, not_valid
    return True, None


class DepartService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        查询部门树
        :param req_dict:
        :return:
        '''
        pid = req_dict.get('pid')
        obj_list = get_base_query(Depart).filter(Depart.parent_id == pid).all()
        result = []
        for obj in obj_list:
            dic = serialize_depart(obj, 'list')
            result.append(dic)
        return gen_json_response(data=result)

    def query_user_depart_tree(self, user_info):
        '''
        查询用户部门树
        :param req_dict:
        :return:
        '''
        obj_list = []
        user_identity = user_info.get('user_identity')
        if user_identity == 2:
            obj_list = get_base_query(Depart).filter(Depart.parent_id == None).all()
        else:
            org_code = user_info.get('org_code')
            depart_obj = get_base_query(Depart).filter(Depart.org_code == org_code).first()
            if depart_obj is not None:
                obj_list = [depart_obj]
        result = []
        for obj in obj_list:
            dic = serialize_depart(obj, 'list')
            dic['children'] = get_depart_children(obj, ser_type='list')
            result.append(dic)
        return gen_json_response(data=result, msg=str(user_identity))

    def query_depart_tree(self, req_dict):
        '''
        查询部门树
        :param req_dict:
        :return:
        '''
        obj_list = get_base_query(Depart).filter(Depart.parent_id == None).all()
        result = []
        for obj in obj_list:
            dic = serialize_depart(obj, 'list')
            dic['children'] = get_depart_children(obj, ser_type='list')
            result.append(dic)
        return gen_json_response(data=result)

    def query_depart_id_tree(self, req_dict):
        '''
        查询部门id树
        :param req_dict:
        :return:
        '''
        obj_list = get_base_query(Depart).filter(Depart.parent_id == None).all()
        result = []
        for obj in obj_list:
            dic = serialize_depart(obj, 'id')
            dic['children'] = get_depart_children(obj, ser_type='id')
            result.append(dic)
        return gen_json_response(data=result)

    def query_depart_all_list(self, req_dict):
        '''
        查询所有部门列表
        :param req_dict:
        :return:
        '''
        obj_list = get_base_query(Depart).all()
        result = []
        for obj in obj_list:
            dic = {
                'id': str(obj.id),
                'depart_name': obj.depart_name,
                'org_code': obj.org_code
            }
            result.append(dic)
        return gen_json_response(data=result)

    def add_obj(self, req_dict):
        '''
        添加
        '''
        flag, not_valid = check_valid(req_dict)
        if not flag:
            return gen_json_response(code=400, msg=not_valid)
        obj = Depart()
        for k in req_dict:
            setattr(obj, k, req_dict[k])
        set_insert_user(obj)
        db.session.add(obj)
        db.session.flush()
        if 'depart_code' not in req_dict:
            obj.org_code = f"org_{obj.id}"
        db.session.add(obj)
        db.session.flush()
        return gen_json_response(msg='添加成功!', extends={'success': True})

    def update_obj(self, req_dict):
        '''
        更新
        '''
        flag, not_valid = check_valid(req_dict)
        if not flag:
            return gen_json_response(code=400, msg=not_valid)
        obj_id = req_dict.get('id')
        obj = db.session.query(Depart).filter(Depart.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='找不到该对象！')
        for k in ['depart_name', 'org_type', 'sort_no', 'mobile', 'fax', 'address', 'memo']:
            setattr(obj, k, req_dict[k])
        child_objs = get_base_query(Depart).filter(Depart.parent_id == obj.id).all()
        obj.is_leaf = 1 if child_objs == [] else 0
        set_update_user(obj)
        db.session.add(obj)
        db.session.flush()
        return gen_json_response(msg='更新成功!', extends={'success': True})

    def delete_obj(self, req_dict):
        '''
        删除
        '''
        if 'id' in req_dict:
            del_ids = [req_dict['id']]
        elif 'ids' in req_dict:
            del_ids = req_dict['ids'].split(',')
        else:
            del_ids = req_dict
        del_objs = db.session.query(Depart).filter(Depart.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.flush()
        return gen_json_response(msg='删除成功。', extends={'success': True})

