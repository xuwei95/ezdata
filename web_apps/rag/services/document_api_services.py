'''
文档管理api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid
from web_apps.rag.db_models import Document
from tasks.data_tasks import self_train_rag_data

    
def serialize_document_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'dataset_id', 'document_type', 'name', 'meta_data', 'chunk_strategy', 'status', 'create_by', 'create_time', 'update_by', 'update_time', 'del_flag', 'sort_no', 'description']:
            if k in ['meta_data', 'chunk_strategy']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in ['meta_data', 'chunk_strategy']:
            dic[k] = json.loads(dic[k])
        for k in []:
            dic.pop(k)
    elif ser_type == 'all_list':
        res = {}
        for k in ['id', 'name']:
            if k in ['meta_data', 'chunk_strategy']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
        
    return dic

    
class DocumentApiService(object):
    def __init__(self):
        pass
        
    @staticmethod
    def get_obj_list(req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(Document)
        
        # 名称 查询逻辑
        name = req_dict.get('name', '')
        if name != '':
            query = query.filter(Document.name.like("%" + name + "%"))

        # 文档类型 查询逻辑
        document_type = req_dict.get('document_type', '')
        if document_type != '':
            query = query.filter(Document.document_type == document_type)

        # 所属数据集 查询逻辑
        dataset_id = req_dict.get('dataset_id', '')
        if dataset_id != '':
            query = query.filter(Document.dataset_id == dataset_id)

        # 状态 查询逻辑
        status = req_dict.get('status', '')
        if status != '':
            query = query.filter(Document.status == status)
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_document_model(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)
    
    @staticmethod
    def get_obj_all_list(req_dict):
        '''
        获取全量列表
        '''
        query = get_base_query(Document)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_document_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    @staticmethod
    def get_obj_detail(req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Document).filter(
            Document.id == obj_id,
            Document.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_document_model(obj, ser_type='detail')
        return gen_json_response(data=dic)
    
    @staticmethod
    def add_obj(req_dict):
        '''
        添加
        '''
        
        obj = Document()
        for key in req_dict:
            if key in ['meta_data', 'chunk_strategy']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        # 训练文档
        self_train_rag_data.apply_async(args=(obj.id, {}, 'document',))
        return gen_json_response(msg='添加成功', extends={'success': True})
    
    @staticmethod
    def edit_obj(req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        
        obj = db.session.query(Document).filter(Document.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key in ['meta_data', 'chunk_strategy']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='编辑成功', extends={'success': True})
    
    @staticmethod
    def delete_obj(req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(Document).filter(Document.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        del_obj.del_flag = 1
        set_update_user(del_obj)
        db.session.add(del_obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    @staticmethod
    def delete_batch(req_dict):
        '''
        批量删除
        '''
        del_ids = req_dict.get('ids')
        if isinstance(del_ids, str):
            del_ids = del_ids.split(',')
        del_objs = db.session.query(Document).filter(Document.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
