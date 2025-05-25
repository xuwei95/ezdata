# coding: utf-8
'''
租户模块服务
'''
import json
from web_apps import db
from models import User, Tenant, PerMission
from utils.auth import encode_auth_token, set_insert_user, set_update_user
from utils.web_utils import get_user_ip
from utils.common_utils import get_now_time, gen_json_response, date_to_timestamp, timestamp_to_date
from utils.query_utils import get_base_query
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_


class TenantService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        query = get_base_query(Tenant, filter_tenant=False)
        name = req_dict.get('name', '')
        if name != '':
            search_text = f"%{name}%"
            query = query.filter(Tenant.name.like(search_text))
        total = query.count()
        page = int(page)
        pagesize = int(pagesize)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = obj.to_dict()
            dic['begin_date'] = timestamp_to_date(dic['begin_date'])
            dic['end_date'] = timestamp_to_date(dic['end_date'])
            dic['status_dictText'] = '正常' if dic['status'] == 1 else '冻结'
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(res_data)

    def get_obj_all_list(self, req_dict):
        '''
        获取全量列表
        '''
        query = get_base_query(Tenant, filter_tenant=False)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = obj.to_dict()
            dic['id'] = str(dic['id'])
            dic['begin_date'] = timestamp_to_date(dic['begin_date'])
            dic['end_date'] = timestamp_to_date(dic['end_date'])
            dic['status_dictText'] = '正常' if dic['status'] == 1 else '冻结'
            result.append(dic)
        return gen_json_response(result)

    def get_obj_info(self, req_dict):
        '''
        获取信息
        '''
        obj_id = req_dict.get('id')
        obj = get_base_query(Tenant, filter_tenant=False).filter(Tenant.id == obj_id).first()
        dic = obj.to_dict()
        dic['begin_date'] = timestamp_to_date(dic['begin_date'])
        dic['end_date'] = timestamp_to_date(dic['end_date'])
        dic['status_dictText'] = '正常' if dic['status'] == 1 else '冻结'
        return gen_json_response(dic)

    def get_user_tenants(self, req_dict, res_type='response'):
        '''
        查询用户租户列表
        :param req_dict:
        :return:
        '''
        user_id = req_dict.get('user_id')
        user_obj = db.session.query(User).filter(User.id == user_id).first()
        if user_obj is None:
            return gen_json_response(code=400, msg='找不到该用户')
        tenant_id_list = json.loads(user_obj.tenant_id_list)
        obj_list = get_base_query(Tenant, filter_tenant=False).filter(Tenant.id.in_(tenant_id_list)).all()
        result = []
        for obj in obj_list:
            dic = {
                'id': str(obj.id),
                'name': obj.name,
                'status': obj.status
            }
            result.append(dic)
        if res_type == 'response':
            return gen_json_response(data=result)
        else:
            return result

    def add_obj(self, req_dict):
        '''
        添加
        '''
        name = req_dict.get('name', '')
        exist_obj = db.session.query(Tenant).filter(Tenant.name == name, Tenant.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='名称已存在！')
        exist_obj = db.session.query(Tenant).filter(Tenant.id == req_dict['id']).first()
        if exist_obj:
            return gen_json_response(code=400, msg='编号已存在！')
        obj = Tenant()
        for k in ['name', 'status', 'id']:
            setattr(obj, k, req_dict[k])
        obj.begin_date = date_to_timestamp(req_dict.get('begin_date'), default=get_now_time())
        obj.end_date = date_to_timestamp(req_dict.get('end_date'), default=get_now_time() + 86400 * 365 * 10)
        set_insert_user(obj, set_tenant=False)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='添加成功。', extends={'success': True})

    def update_obj(self, req_dict):
        '''
        更新
        '''
        obj_id = req_dict.get('id')
        name = req_dict.get('code', '')
        exist_obj = db.session.query(Tenant).filter(Tenant.id != obj_id,
                                                    Tenant.name == name,
                                                    Tenant.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='名称已存在！')
        obj = db.session.query(Tenant).filter(Tenant.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='找不到该对象！')
        for k in ['name', 'status']:
            setattr(obj, k, req_dict[k])
        obj.begin_date = date_to_timestamp(req_dict.get('begin_date'))
        obj.end_date = date_to_timestamp(req_dict.get('end_date'))
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
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
        del_objs = db.session.query(Tenant).filter(Tenant.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(msg='删除成功。', extends={'success': True})

