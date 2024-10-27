'''
对话应用管理api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid, parse_json, get_now_time, timestamp_to_date, trans_time_length
from web_apps.llm.db_models import ChatApp, ChatAppToken
from web_apps.llm.services.llm_services import chat_generate, chat_run


def serialize_chat_app_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'name', 'icon', 'type', 'state', 'depart_list', 'chat_config', 'create_by', 'create_time',
                  'update_by', 'update_time', 'del_flag', 'sort_no', 'description']:
            if k in ['chat_config']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in ['chat_config', 'depart_list']:
            dic[k] = json.loads(dic[k])
        for k in []:
            dic.pop(k)
    elif ser_type == 'all_list':
        res = {}
        for k in ['id']:
            if k in ['chat_config']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res

    return dic


class ChatAppApiService(object):
    def __init__(self):
        pass

    @staticmethod
    def chat(chat_app, message, stream=True):
        '''
        应用对话
        '''
        chat_config = parse_json(chat_app.chat_config)
        req_data = {
            'message': message,
            'chatConfig': chat_config
        }
        if stream:
            return chat_generate(req_data)
        else:
            return gen_json_response(chat_run(req_data))

    @staticmethod
    def apply_token(req_dict):
        '''
        申请api_key
        '''
        app_id = req_dict.get('app_id', '')
        apply_time_length = req_dict.get('apply_time_length', 'forever')
        apply_caption = req_dict.get('apply_caption', '')
        obj = ChatAppToken()
        obj.id = gen_uuid(res_type='base')
        obj.app_id = app_id
        obj.api_key = gen_uuid(res_type='base')
        user_info = get_auth_token_info()
        obj.apply_user_id = user_info.get('id')
        obj.apply_user = user_info.get('username')
        obj.apply_time = get_now_time()
        obj.review_time = get_now_time()
        obj.valid_time = obj.review_time + trans_time_length(apply_time_length)
        obj.status = 1
        obj.description = apply_caption
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='添加成功', extends={'success': True})

    @staticmethod
    def api_key_list(req_dict):
        '''
        api_key列表
        '''
        app_id = req_dict.get('app_id', '')
        user_info = get_auth_token_info()
        apply_user_id = user_info['id']
        chat_tokens = get_base_query(ChatAppToken).filter(ChatAppToken.app_id == app_id,
                                                          ChatAppToken.apply_user_id == apply_user_id).all()
        records = []
        for i in chat_tokens:
            dic = i.to_dict()
            dic['valid_time'] = timestamp_to_date(dic['valid_time'])
            dic['apply_time'] = timestamp_to_date(dic['apply_time'])
            records.append(dic)
        res_data = {
            'records': records,
            'total': len(chat_tokens)
        }
        return gen_json_response(data=res_data)

    @staticmethod
    def api_key_status(req_dict):
        '''
        修改api_key状态
        '''
        api_id = req_dict.get('id', '')
        chat_token = db.session.query(ChatAppToken).filter(ChatAppToken.id == api_id).first()
        if chat_token is None:
            return gen_json_response(code=500, msg='未找到api_key')
        chat_token.status = 1 if chat_token.status == 0 else 0
        set_update_user(chat_token)
        db.session.add(chat_token)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='修改成功')

    @staticmethod
    def api_key_delete(req_dict):
        '''
        删除api_key
        '''
        api_id = req_dict.get('id', '')
        chat_token = db.session.query(ChatAppToken).filter(ChatAppToken.id == api_id).first()
        if chat_token is None:
            return gen_json_response(code=500, msg='未找到api_key')
        chat_token.del_flag = 1
        set_update_user(chat_token)
        db.session.add(chat_token)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='删除成功')

    @staticmethod
    def get_obj_list(req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(ChatApp)

        # 名称 查询逻辑
        name = req_dict.get('name', '')
        if name != '':
            query = query.filter(ChatApp.name.like("%" + name + "%"))

        # 类型 查询逻辑
        _type = req_dict.get('type', '')
        if _type != '':
            query = query.filter(ChatApp.type == _type)

        # 状态 查询逻辑
        state = req_dict.get('state', '')
        if state != '':
            query = query.filter(ChatApp.state == state)
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_chat_app_model(obj, ser_type='list')
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
        query = get_base_query(ChatApp)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_chat_app_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)

    @staticmethod
    def get_obj_detail(req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(ChatApp).filter(
            ChatApp.id == obj_id,
            ChatApp.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_chat_app_model(obj, ser_type='detail')
        return gen_json_response(data=dic)

    @staticmethod
    def add_obj(req_dict):
        '''
        添加
        '''
        # 名称 判重逻辑
        name = req_dict.get('name', '')
        if name != '':
            exist_obj = db.session.query(ChatApp).filter(
                ChatApp.name == name,
                ChatApp.del_flag == 0).first()
            if exist_obj:
                return gen_json_response(code=400, msg='字段"名称"已存在')
        obj = ChatApp()
        for key in req_dict:
            if key in ['chat_config']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'depart_list':
                li = req_dict.get(key, "").split(',')
                if li == ['']:
                    li = []
                setattr(obj, key, json.dumps(li))
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='添加成功', extends={'success': True})

    @staticmethod
    def edit_obj(req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        # 判重逻辑
        exist_query = db.session.query(ChatApp).filter(ChatApp.id != obj_id)
        name = req_dict.get('name', '')
        if name != '':
            exist_query = exist_query.filter(ChatApp.name == name)
        exist_obj = exist_query.first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在')
        obj = db.session.query(ChatApp).filter(ChatApp.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key in ['chat_config']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'depart_list':
                li = req_dict.get(key, "").split(',')
                if li == ['']:
                    li = []
                setattr(obj, key, json.dumps(li))
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
        del_obj = db.session.query(ChatApp).filter(ChatApp.id == obj_id).first()
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
        del_objs = db.session.query(ChatApp).filter(ChatApp.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
