'''
知识段管理api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid
from web_apps.rag.db_models import Chunk
from web_apps.rag.services.rag_service import add_chunk, delete_chunk

    
def serialize_chunk_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'dataset_id', 'document_id', 'datasource_id', 'datamodel_id', 'chunk_type', 'question', 'answer', 'content', 'hash', 'position', 'status', 'star_flag', 'create_by', 'create_time', 'update_by', 'update_time', 'del_flag', 'sort_no', 'description']:
            if k in []:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in []:
            dic[k] = json.loads(dic[k])
        for k in []:
            dic.pop(k)
    elif ser_type == 'all_list':
        res = {}
        for k in ['id']:
            if k in []:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
        
    return dic

    
class ChunkApiService(object):
    def __init__(self):
        pass
        
    @staticmethod
    def get_obj_list(req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(Chunk)
        # 分段类型 查询逻辑
        chunk_type = req_dict.get('chunk_type', '')
        if chunk_type != '':
            query = query.filter(Chunk.chunk_type == chunk_type)

        # 所属数据集 查询逻辑
        dataset_id = req_dict.get('dataset_id', '')
        if dataset_id != '':
            query = query.filter(Chunk.dataset_id == dataset_id)

        # 所属文档 查询逻辑
        document_id = req_dict.get('document_id', '')
        if document_id != '':
            query = query.filter(Chunk.document_id == document_id)

        # 所属数据源 查询逻辑
        datasource_id = req_dict.get('datasource_id', '')
        if datasource_id != '':
            query = query.filter(Chunk.datasource_id == datasource_id)

        # 所属数据模型 查询逻辑
        datamodel_id = req_dict.get('datamodel_id', '')
        if datamodel_id != '':
            query = query.filter(Chunk.datamodel_id == datamodel_id)

        # 关键词 查询逻辑
        content = req_dict.get('content', '')
        if content != '':
            query = query.filter(Chunk.content.like("%" + content + "%"))

        # 状态 查询逻辑
        status = req_dict.get('status', '')
        if status != '':
            query = query.filter(Chunk.status == status)
        total = query.count()
        if req_dict.get('show_all') and document_id != '':
            # 展示文档下全部chunk，按position排序
            obj_list = query.all()
            obj_list = sorted(obj_list, key=lambda obj: obj.position)
        else:
            query = query.offset((page - 1) * pagesize)
            query = query.limit(pagesize)
            obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_chunk_model(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)
    
    @staticmethod
    def get_obj_detail(req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Chunk).filter(
            Chunk.id == obj_id,
            Chunk.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_chunk_model(obj, ser_type='detail')
        return gen_json_response(data=dic)
    
    @staticmethod
    def add_obj(req_dict):
        '''
        添加
        '''
        add_chunk(req_dict)
        return gen_json_response(msg='添加成功', extends={'success': True})
    
    @staticmethod
    def edit_obj(req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Chunk).filter(Chunk.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        add_chunk(req_dict)
        return gen_json_response(msg='编辑成功', extends={'success': True})
    
    @staticmethod
    def delete_obj(req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(Chunk).filter(Chunk.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        del_obj.del_flag = 1
        set_update_user(del_obj)
        db.session.add(del_obj)
        db.session.commit()
        db.session.flush()
        delete_chunk(obj_id)
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    @staticmethod
    def delete_batch(req_dict):
        '''
        批量删除
        '''
        del_ids = req_dict.get('ids')
        if isinstance(del_ids, str):
            del_ids = del_ids.split(',')
        del_objs = db.session.query(Chunk).filter(Chunk.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
            delete_chunk(del_obj.id)
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
