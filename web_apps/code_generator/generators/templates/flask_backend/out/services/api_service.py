'''
测试api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid
from web_apps.test.db_models import Test

    
def serialize_test_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'create_by', 'create_time', 'update_by', 'update_time', 'del_flag', 'sort_no', 'description', 'test']:
            if k in ['test']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in ['test']:
            dic[k] = json.loads(dic[k])
        for k in []:
            dic.pop(k)
    elif ser_type == 'all_list':
        res = {}
        for k in ['id', 'test']:
            if k in ['test']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
        
    return dic

    
class TestApiService(object):
    def __init__(self):
        pass
        
    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(Test)
        # 关键词 查询逻辑
        search_text = req_dict.get('search_text', '')
        if search_text != '':
            # query = query.filter(Test.search_text.like("%search_text%"))
            pass
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_test_model(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)
    
    def get_obj_all_list(self, req_dict):
        '''
        获取全量列表
        '''
        query = get_base_query(Test)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_test_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Test).filter(
            Test.id == obj_id,
            Test.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_test_model(obj, ser_type='detail')
        return gen_json_response(data=dic)
    
    def add_obj(self, req_dict):
        '''
        添加
        '''
        # 测试字段 判重逻辑
        test = req_dict.get('test', '')
        if test != '':
            exist_obj = db.session.query(Test).filter(
                Test.test == test,
                Test.del_flag == 0).first()
            if exist_obj:
                return gen_json_response(code=400, msg='字段"测试字段"已存在')
        obj = Test()
        for key in req_dict:
            if key in ['test']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='添加成功')
    
    def edit_obj(self, req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        # 判重逻辑
        exist_query = db.session.query(Test).filter(Test.id == obj_id)
        test = req_dict.get('test', '')
        if test != '':
            exist_query = exist_query.filter(Test.test == test)
        exist_obj = exist_query.first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在')
        obj = db.session.query(Test).filter(Test.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key in ['test']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='添加成功')
    
    def delete_obj(self, req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(Test).filter(Test.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        del_obj.del_flag = 1
        set_update_user(del_obj)
        db.session.add(del_obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='删除成功')
    
    def delete_batch(self, req_dict):
        '''
        批量删除
        '''
        del_ids = str(req_dict['ids']).split(',')
        del_objs = db.session.query(Test).filter(Test.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功')
    
    def importExcel(self, req_dict):
        '''
        excel导入
        '''
        pass
    
    
    def exportXls(self, req_dict):
        '''
        导出excel
        '''
        pass
