# coding: utf-8
'''
User模块服务
'''
import json
from web_apps import db
from models import User, Role, PerMission, Depart
from utils.auth import encode_auth_token, set_insert_user, set_update_user, get_auth_token_info
from utils.web_utils import get_user_ip, validate_params
from utils.common_utils import get_now_time, gen_json_response
from utils.query_utils import get_base_query
from config import SYS_CONF
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_


def serialize_permission(obj, ser_type='list'):
    '''
    序列化数据
    :param obj:
    :return:
    '''
    dic = {}
    if ser_type == 'list':
        dic = {
            "id": obj.id,
            "key": str(obj.id),
            "title": obj.name,
            "parent_id": obj.parent_id,
            "name": obj.name,
            "perms": obj.perms,
            "perms_type": obj.perms_type,
            "icon": obj.icon,
            "component": obj.component,
            "component_name": obj.component_name,
            "url": obj.url,
            "redirect": obj.redirect,
            "sort_no": obj.sort_no,
            "menu_type": obj.menu_type,
            "is_leaf": obj.is_leaf == 1,
            "route": obj.is_route == 1,
            "keep_alive": obj.keep_alive == 1,
            "description": obj.description,
            "del_flag": obj.del_flag,
            "create_by": obj.create_by,
            "create_time": obj.create_time,
            "update_by": obj.update_by,
            "update_time": obj.update_time,
            "always_show": obj.always_show == 1,
            "hidden": obj.hidden == 1,
            "hide_tab": obj.hide_tab == 1,
            "status": obj.status,
            "internal_or_external": obj.internal_or_external == 1,
            "leaf": obj.is_leaf == 1,
        }
    elif ser_type == 'menu':
        dic = {
            'component': obj.component,
            'id': str(obj.id),
            'meta': {
                'componentName': obj.component_name,
                'icon': obj.icon,
                'internalOrExternal': obj.internal_or_external == 1,
                'keepAlive': obj.keep_alive == 1,
                'hideMenu': obj.hidden == 1,
                'title': obj.name,
            },
            'hidden': obj.hidden == 1,
            'name': obj.name,
            'path': obj.url,
            'redirect': obj.redirect,
            'route': obj.is_route
        }
    elif ser_type == 'auth':
        dic = {
            "action": obj.perms,
            "describe": obj.description,
            "type": str(obj.perms_type),
            "status": str(obj.status)
        }
    elif ser_type == 'tree':
        dic = {
            "icon": obj.icon,
            "isLeaf": obj.is_leaf == 1,
            "key": str(obj.id),
            "label": None,
            "parentId": str(obj.parent_id) if obj.parent_id else None,
            "ruleFlag": obj.rule_flag,
            "scopedSlots": {
                "title": "hasDatarule"
            },
            "slotTitle": obj.name,
            "title": None,
            "value": str(obj.id)
        }
    return dic


def check_valid(req_dict):
    '''
    校验菜单添加/更新是否符合条件
    :param req_dict:
    :return:
    '''
    menu_type = req_dict.get('menu_type')
    verify_dict = {}
    # 菜单类型(0: 一级菜单;1: 子菜单:2: 按钮权限)
    if menu_type in [0, 1]:
        verify_dict['name'] = {
            'name': '菜单名称',
            'not_empty': True
        }
        verify_dict['url'] = {
            'name': '访问路径',
            'not_empty': True
        }
        verify_dict['component'] = {
            'name': '前端组件',
            'not_empty': True
        }
    if menu_type in [1, 2]:
        verify_dict['parent_id'] = {
            'name': '上级菜单',
            'not_empty': True
        }
        # 同级菜单名称和url不能重复
        parent_id = req_dict.get('parent_id')
        if parent_id:
            child_list = get_base_query(PerMission, filter_tenant=False).filter(PerMission.parent_id == parent_id).all()
            _id = req_dict.get('id')
            exist_list = [i for i in child_list if str(i.id) != str(_id) and (i.name == req_dict.get('name') or i.url == req_dict.get('url'))]
            if exist_list != []:
                return False, '同级菜单名称或路径已存在'
    if menu_type == 2:
        verify_dict['name'] = {
            'name': '菜单/权限',
            'not_empty': True
        }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return False, not_valid
    return True, None


def get_permission_children(permission_obj, obj_list, ser_type='list'):
    '''
    找到权限的下级权限
    '''
    if permission_obj.menu_type not in [0, 1]:
        return None
    children = []
    child_objs = [i for i in obj_list if i.parent_id == permission_obj.id]
    for obj in child_objs:
        dic = serialize_permission(obj, ser_type)
        # 根据是否开启es日志，过滤日志菜单
        if obj.url == '/ops/log' and SYS_CONF.get('LOGGER_TYPE') != "es":
            continue
        child = get_permission_children(obj, obj_list, ser_type)
        if child:
            dic['children'] = child
        children.append(dic)
    return children


class PerMissionService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        parent_id = req_dict.get('parent_id', '')
        search_text = req_dict.get('search_text', '')
        query = get_base_query(PerMission, filter_tenant=False)
        show_children = True
        if parent_id != '':
            query = get_base_query(PerMission, filter_tenant=False).filter(or_(PerMission.id == parent_id, PerMission.parent_id == parent_id))
        if search_text != '':
            search_text = f"%{search_text}%"
            query = query.filter(PerMission.name.like(search_text))
            show_children = False
        obj_list = query.all()
        result = []
        if show_children:
            parent_objs = [obj for obj in obj_list if obj.parent_id is None]
            for obj in parent_objs:
                dic = serialize_permission(obj, 'list')
                if show_children:
                    children = get_permission_children(obj, obj_list, 'list')
                    if children:
                        dic['children'] = children
                result.append(dic)
        else:
            for obj in obj_list:
                dic = serialize_permission(obj, 'list')
                result.append(dic)
        return gen_json_response(data=result)

    def get_user_prem_ids(self, user_info):
        '''
        获取用户权限id列表
        根据绑定角色和当前登录部门组合生成权限列表
        :return:
        '''
        prem_id_list = []
        role_code_list = user_info.get('roles', [])
        org_code = user_info.get('org_code')
        role_obj_list = get_base_query(Role).filter(Role.role_code.in_(role_code_list)).all()
        for role_obj in role_obj_list:
            premissions = json.loads(role_obj.permissions)
            prem_id_list.extend(premissions)
        depart_obj = get_base_query(Depart).filter(Depart.org_code == org_code).first()
        if depart_obj:
            premissions = json.loads(depart_obj.permissions)
            prem_id_list.extend(premissions)
        prem_id_list = list(set(prem_id_list))
        return prem_id_list

    def get_all_menus(self, req_dict):
        '''
        获取所有菜单
        :param req_dict:
        :return:
        '''
        obj_list = get_base_query(PerMission, filter_tenant=False).filter(PerMission.menu_type.in_([0, 1])).all()
        result = []
        parent_objs = [obj for obj in obj_list if obj.parent_id is None]
        for obj in parent_objs:
            dic = serialize_permission(obj, 'menu')
            children = get_permission_children(obj, obj_list, 'menu')
            if children:
                dic['children'] = children
            result.append(dic)
        return result

    def get_user_menus(self, user_info):
        '''
        获取用户菜单
        :param req_dict:
        :return:
        '''
        prem_id_list = self.get_user_prem_ids(user_info)
        obj_list = get_base_query(PerMission, filter_tenant=False).filter(PerMission.id.in_(prem_id_list)).filter(
            PerMission.menu_type.in_([0, 1])).all()
        parent_objs = [obj for obj in obj_list if obj.parent_id is None]
        result = []
        for obj in parent_objs:
            dic = serialize_permission(obj, 'menu')
            children = get_permission_children(obj, obj_list, 'menu')
            if children:
                dic['children'] = children
            result.append(dic)
        return result

    def get_all_auth(self, req_dict):
        '''
        获取所有权限
        :param req_dict:
        :return:
        '''
        obj_list = get_base_query(PerMission, filter_tenant=False).filter(PerMission.menu_type == 2).all()
        result = []
        for obj in obj_list:
            dic = serialize_permission(obj, 'auth')
            result.append(dic)
        # 根据是否开启es日志，添加日志权限
        if SYS_CONF.get('LOGGER_TYPE') == "es":
            dic = {
                "action": "task:log",
                "describe": "查看任务日志",
                "type": "1",
                "status": "1"
            }
            result.append(dic)
        # 根据是否开启llm模块，添加llm相关权限
        if SYS_CONF.get('LLM_TYPE'):
            dic = {
                "action": "llm:data:chat",
                "describe": "数据对话",
                "type": "1",
                "status": "1"
            }
            result.append(dic)
        return result

    def get_user_auth(self, user_info):
        '''
        获取用户操作权限
        :param req_dict:
        :return:
        '''
        prem_id_list = self.get_user_prem_ids(user_info)
        prem_objs = get_base_query(PerMission, filter_tenant=False).filter(PerMission.id.in_(prem_id_list)).filter(
            PerMission.menu_type == 2).all()
        result = []
        for obj in prem_objs:
            dic = serialize_permission(obj, 'auth')
            result.append(dic)
        # 根据是否开启es日志，添加日志权限
        if SYS_CONF.get('LOGGER_TYPE') == "es":
            dic = {
                "action": "task:log",
                "describe": "查看任务日志",
                "type": "1",
                "status": "1"
            }
            result.append(dic)
        # 根据是否开启llm模块，添加llm相关权限
        if SYS_CONF.get('LLM_TYPE'):
            dic = {
                "action": "llm:data:chat",
                "describe": "数据对话",
                "type": "1",
                "status": "1"
            }
            result.append(dic)
        return result

    def get_role_tree_list(self, req_dict):
        '''
        获取角色权限树
        :param req_dict:
        :return:
        '''
        obj_list = get_base_query(PerMission, filter_tenant=False).all()
        treeList = []
        parent_objs = [obj for obj in obj_list if obj.parent_id is None]
        for obj in parent_objs:
            dic = serialize_permission(obj, 'tree')
            children = get_permission_children(obj, obj_list, 'tree')
            if children:
                dic['children'] = children
            treeList.append(dic)
        ids = [str(i.id) for i in obj_list]
        result = {
            'ids': ids,
            'treeList': treeList
        }
        return gen_json_response(result)

    def get_role_permissions(self, req_dict):
        '''
        获取角色权限列表
        :param req_dict:
        :return:
        '''
        role_id = req_dict.get('role_id')
        role_obj = db.session.query(Role).filter(Role.id == role_id).first()
        if role_obj is None:
            return gen_json_response(code=400, msg='找不到该对象！')
        permissions = json.loads(role_obj.permissions)
        return gen_json_response(permissions)

    def save_role_permissions(self, req_dict):
        '''
        设置角色权限列表
        :param req_dict:
        :return:
        '''
        role_id = req_dict.get('role_id')
        lastpermissionIds = req_dict.get('lastpermissionIds', '')
        permissionIds = req_dict.get('permissionIds', '')
        role_obj = db.session.query(Role).filter(Role.id == role_id).first()
        if role_obj is None:
            return gen_json_response(code=400, msg='找不到该对象！')
        permissionIds = permissionIds.split(',')
        role_obj.permissions = json.dumps(permissionIds)
        set_insert_user(role_obj)
        db.session.add(role_obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='操作成功', extends={'success': True})

    def get_depart_permissions(self, req_dict):
        '''
        获取部门权限列表
        :param req_dict:
        :return:
        '''
        depart_id = req_dict.get('depart_id')
        depart_obj = db.session.query(Depart).filter(Depart.id == depart_id).first()
        if depart_obj is None:
            return gen_json_response(code=400, msg='找不到该对象！')
        permissions = json.loads(depart_obj.permissions)
        return gen_json_response(permissions)

    def save_depart_permissions(self, req_dict):
        '''
        设置部门权限列表
        :param req_dict:
        :return:
        '''
        depart_id = req_dict.get('depart_id')
        lastpermissionIds = req_dict.get('lastpermissionIds', '')
        permissionIds = req_dict.get('permissionIds', '')
        depart_obj = db.session.query(Depart).filter(Depart.id == depart_id).first()
        if depart_obj is None:
            return gen_json_response(code=400, msg='找不到该对象！')
        permissionIds = permissionIds.split(',')
        depart_obj.permissions = json.dumps(permissionIds)
        set_insert_user(depart_obj)
        db.session.add(depart_obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='操作成功', extends={'success': True})

    def add_obj(self, req_dict):
        '''
        添加
        '''
        flag, not_valid = check_valid(req_dict)
        if not flag:
            return gen_json_response(code=400, msg=not_valid)
        obj = PerMission()
        for k in req_dict:
            setattr(obj, k, req_dict[k])
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
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
        obj = db.session.query(PerMission).filter(PerMission.id == obj_id).first()
        if obj is None:
            return gen_json_response(msg='找不到该对象！')
        for k in req_dict:
            setattr(obj, k, req_dict[k])
        child_objs = get_base_query(PerMission, filter_tenant=False).filter(PerMission.parent_id == obj.id).all()
        obj.is_leaf = 1 if child_objs == [] else 0
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='更新成功!', extends={'success': True})

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
        del_objs = db.session.query(PerMission).filter(PerMission.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(msg='删除成功!', extends={'success': True})
