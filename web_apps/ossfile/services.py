# coding: utf-8
'''
oss对象存储服务
'''
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user
from utils.common_utils import gen_json_response
from models import File
from sqlalchemy import or_


class FileService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        query = get_base_query(File)
        #  file_name 查询逻辑
        file_name = req_dict.get('file_name', '')
        if file_name != '':
            file_name = f"%{file_name}%"
            print(file_name)
            query = query.filter(or_(File.file_name.like(file_name)))
        #  url 查询逻辑
        url = req_dict.get('url', '')
        if url != '':
            query = query.filter(File.url == url)
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

    def add_obj(self, req_dict):
        '''
        添加
        '''
        obj = File()
        for k in req_dict:
            setattr(obj, k, req_dict[k])
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        res_data = {
            'url': obj.url,
            'source_name': obj.file_name
        }
        return gen_json_response(data=res_data, msg='上传成功。', extends={'success': True})

    def add_or_update_obj(self, req_dict):
        '''
        根据文件名添加或更新
        '''
        file_name = req_dict.get('file_name')
        obj = get_base_query(File).filter(File.file_name == file_name).first()
        if obj is None:
            obj = File()
            for k in req_dict:
                setattr(obj, k, req_dict[k])
            set_insert_user(obj)
        else:
            set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        res_data = {
            'url': obj.url,
            'source_name': obj.file_name
        }
        return gen_json_response(data=res_data, msg='上传成功。', extends={'success': True})

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
        del_objs = db.session.query(File).filter(File.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(msg='删除成功。')
