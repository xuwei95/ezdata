# coding: utf-8
'''
数据字典服务
'''
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user
from utils.common_utils import gen_json_response
from utils.cache_utils import set_key_exp, get_key_value
from models import Dict, DictItem
import json
from sqlalchemy import or_


class DictService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        query = get_base_query(Dict)
        #  dict_code 查询逻辑
        dict_code = req_dict.get('dict_code', '')
        if dict_code != '':
            query = query.filter(Dict.dict_code == dict_code)
        #  dict_name 查询逻辑
        dict_name = req_dict.get('dict_name', '')
        if dict_name != '':
            dict_name = f"%{dict_name}%"
            query = query.filter(Dict.dict_name.like(dict_name))
        total = query.count()
        page = int(page)
        pagesize = int(pagesize)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = obj.to_dict()
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def get_obj_all_items(self, req_dict):
        '''
        获取所有数据列表
        '''
        use_cache = req_dict.get('use_cache', True)
        cache_key = 'sysAllDictItems'
        sysAllDictItems = get_key_value(cache_key)
        if use_cache and sysAllDictItems is not None:
            sysAllDictItems = json.loads(sysAllDictItems)
        else:
            query = get_base_query(Dict)
            obj_list = query.all()
            sysAllDictItems = {}
            for obj in obj_list:
                dict_code = obj.dict_code
                dict_items = get_base_query(DictItem).filter(DictItem.dict_id == obj.id).filter(DictItem.status == 1).all()
                sysAllDictItems[dict_code] = []
                for item in dict_items:
                    dic = {
                        'label': item.name,
                        'text': item.name,
                        'title': item.name,
                        'value': item.value
                    }
                    sysAllDictItems[dict_code].append(dic)
            set_key_exp(cache_key, json.dumps(sysAllDictItems), 3600)
        return sysAllDictItems

    def add_obj(self, req_dict):
        '''
        添加
        '''
        dict_code = req_dict.get('dict_code')
        exist_obj = db.session.query(Dict).filter(
            Dict.dict_code == dict_code,
            Dict.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据字典已存在！')
        obj = Dict()
        obj.dict_name = req_dict.get('dict_name', '')
        obj.dict_code = req_dict.get('dict_code')
        obj.description = req_dict.get('description', '')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='添加成功。')

    def update_obj(self, req_dict):
        '''
        更新
        '''
        obj_id = req_dict.get('id')
        dict_code = req_dict.get('dict_code', '')
        exist_obj = db.session.query(Dict).filter(Dict.id != obj_id,
                                                  Dict.dict_code == dict_code,
                                                  Dict.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据字典已存在！')
        obj = db.session.query(Dict).filter(Dict.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='找不到该数据字典！')
        obj.dict_name = req_dict.get('dict_name', '')
        obj.dict_code = req_dict.get('dict_code')
        obj.description = req_dict.get('description', '')
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
            del_ids = req_dict['ids'].split(',')
        else:
            del_ids = req_dict
        del_objs = db.session.query(Dict).filter(Dict.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功。')

    def get_delete_list(self, req_dict):
        '''
        获取回收站已删除列表
        '''
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        query = get_base_query(Dict, filter_delete=False).filter(Dict.del_flag == 1)
        #  search_text 查询逻辑
        search_text = req_dict.get('search_text', '')
        if search_text != '':
            search_text = f"%{search_text}%"
            print(search_text)
            query = query.filter(or_(Dict.name.like(search_text), Dict.value.like(search_text)))
        total = query.count()
        page = int(page)
        pagesize = int(pagesize)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = obj.to_dict()
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def delete_physic(self, req_dict):
        '''
        物理真实删除
        :param req_dict:
        :return:
        '''
        if 'id' in req_dict:
            del_ids = [req_dict['id']]
        elif 'ids' in req_dict:
            del_ids = req_dict['ids']
        else:
            del_ids = req_dict
        del_objs = db.session.query(Dict).filter(Dict.id.in_(del_ids)).all()
        for del_obj in del_objs:
            db.session.delete(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(msg='删除成功。')

    def delete_back(self, req_dict):
        '''
        删除恢复
        :param req_dict:
        :return:
        '''
        if 'id' in req_dict:
            del_ids = [req_dict['id']]
        elif 'ids' in req_dict:
            del_ids = req_dict['ids']
        else:
            del_ids = req_dict
        del_objs = db.session.query(Dict).filter(Dict.id.in_(del_ids)).all()
        exist_objs = db.session.query(Dict).filter(Dict.dict_code.in_([i.dict_code for i in del_objs]), Dict.del_flag == 0).all()
        if exist_objs != []:
            return gen_json_response(msg=f"恢复失败，{','.join([i.dict_code for i in del_objs])}等字典已存在")
        for del_obj in del_objs:
            del_obj.del_flag = 0
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(msg='恢复成功！')


class DictItemService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        dict_id = req_dict.get('dict_id', '')
        name = req_dict.get('name', '')
        status = req_dict.get('status', '')
        query = get_base_query(DictItem)
        if dict_id != '':
            query = query.filter(DictItem.dict_id == dict_id)
        if status != '':
            query = query.filter(DictItem.status == status)
        if name != '':
            name = f"%{name}%"
            query = query.filter(DictItem.name.like(name) | DictItem.value.like(name))
        total = query.count()
        page = int(page)
        pagesize = int(pagesize)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = obj.to_dict()
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def get_dict_items(self, req_dict):
        '''
        获取字典项
        '''
        dict_code = req_dict.get('dict_code', '')
        dict_obj = get_base_query(Dict).filter(Dict.dict_code == dict_code).first()
        if not dict_obj:
            return gen_json_response(code=400, msg='未知字典编码')
        query = get_base_query(DictItem).filter(DictItem.dict_id == dict_obj.id, DictItem.status == 1)
        obj_list = query.all()
        result = []
        for item in obj_list:
            dic = {
                'label': item.name,
                'text': item.name,
                'title': item.name,
                'value': item.value,
                'extend': json.loads(item.extend)
            }
            result.append(dic)
        return gen_json_response(data=result)

    def add_obj(self, req_dict):
        '''
        添加
        '''
        value = req_dict.get('value', '')
        dict_id = req_dict.get('dict_id')
        exist_obj = db.session.query(DictItem).filter(DictItem.value == value,
                                                       DictItem.dict_id == dict_id,
                                                       DictItem.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='字典值已存在')
        obj = DictItem()
        obj.dict_id = req_dict.get('dict_id')
        obj.name = req_dict.get('name', '')
        obj.value = req_dict.get('value')
        extend = req_dict.get('extend', '')
        if extend != '':
            try:
                extend = json.loads(extend)
                if not isinstance(extend, dict) or not isinstance(extend, list):
                    obj.extend = json.dumps(extend, ensure_ascii=False, indent=2)
                else:
                    return gen_json_response(code=400, msg=f'拓展参数格式错误:必须为列表或对象格式')
            except Exception as e:
                return gen_json_response(code=400, msg=f'拓展参数格式错误:{e}')
        obj.description = req_dict.get('description', '')
        obj.status = req_dict.get('status', 1)
        obj.sort_no = req_dict.get('sort_no', 1)
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='添加成功!')

    def update_obj(self, req_dict):
        '''
        更新
        '''
        obj_id = req_dict.get('id')
        value = req_dict.get('value', '')
        dict_id = req_dict.get('dict_id')
        exist_obj = db.session.query(DictItem).filter(DictItem.id != obj_id,
                                                      DictItem.value == value,
                                                      DictItem.dict_id == dict_id,
                                                      DictItem.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='字典值已存在')
        obj = db.session.query(DictItem).filter(DictItem.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='找不到该字典值')
        obj.name = req_dict.get('name')
        obj.value = req_dict.get('value')
        extend = req_dict.get('extend', '')
        if extend != '':
            try:
                extend = json.loads(extend)
                if isinstance(extend, dict) or isinstance(extend, list):
                    obj.extend = json.dumps(extend, ensure_ascii=False, indent=2)
                else:
                    return gen_json_response(code=400, msg=f'拓展参数格式错误:必须为列表或对象格式')
            except Exception as e:
                return gen_json_response(code=400, msg=f'拓展参数格式错误:{e}')
        obj.description = req_dict.get('description', '')
        obj.status = req_dict.get('status', 1)
        obj.sort_no = req_dict.get('sort_no', 1)
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='更新成功!')

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
        del_objs = db.session.query(DictItem).filter(DictItem.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(msg='删除成功!')



