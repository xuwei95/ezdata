'''
告警api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid
from web_apps.alert.db_models import Alert
from utils.web_utils import validate_params
import pandas as pd
import io


def serialize_alert_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'strategy_id', 'title', 'content', 'level', 'status', 'rule_id', 'rule_name', 'biz', 'source', 'tags', 'metric', 'recover_time', 'ext_params', 'create_by', 'create_time', 'update_by', 'update_time', 'del_flag', 'sort_no', 'description']:
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

    
class AlertApiService(object):
    def __init__(self):
        pass
        
    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(Alert)
        
        # 告警标题 查询逻辑
        title = req_dict.get('title', '')
        if title != '':
            query = query.filter(Alert.title.like("%" + title + "%"))

        # 告警等级 查询逻辑
        level = req_dict.get('level', '')
        if level != '':
            query = query.filter(Alert.level == level)

        # 告警状态 查询逻辑
        status = req_dict.get('status', '')
        if status != '':
            query = query.filter(Alert.status == status)

        # 告警内容 查询逻辑
        content = req_dict.get('content', '')
        if content != '':
            query = query.filter(Alert.content.like("%" + content + "%"))

        # 创建时间 查询逻辑
        create_time = req_dict.get('create_time', '')
        if create_time != '':
            query = query.filter(Alert.create_time >= create_time)
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_alert_model(obj, ser_type='list')
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
        query = get_base_query(Alert)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_alert_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Alert).filter(
            Alert.id == obj_id,
            Alert.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_alert_model(obj, ser_type='detail')
        return gen_json_response(data=dic)
    
    def add_obj(self, req_dict):
        '''
        添加
        '''
        obj = Alert()
        for key in req_dict:
            if key in []:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='添加成功', extends={'success': True})
    
    def edit_obj(self, req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Alert).filter(Alert.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key in []:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='编辑成功', extends={'success': True})
    
    def delete_obj(self, req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(Alert).filter(Alert.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        del_obj.del_flag = 1
        set_update_user(del_obj)
        db.session.add(del_obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    def delete_batch(self, req_dict):
        '''
        批量删除
        '''
        del_ids = req_dict.get('ids')
        if isinstance(del_ids, str):
            del_ids = del_ids.split(',')
        del_objs = db.session.query(Alert).filter(Alert.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    def importExcel(self, file):
        '''
        excel导入
        '''
        try:
            df = pd.read_excel(file, dtype=object)
            df.fillna("", inplace=True)
            # 校验上传字段
            data_li = []
            n = 2
            for k, row in df.iterrows():
                row = row.to_dict()
                verify_dict = {
    }
                not_valid = validate_params(row, verify_dict)
                if not_valid:
                    not_valid = {
                        'code': 400,
                        'msg': f'第{n}行{not_valid}'
                    }
                    return not_valid
                data_li.append(row)
                n += 1
            
            # 循环导入
            for row in data_li:
                obj = Alert()
                for key in row:
                    if key in []:
                        setattr(obj, key, json.dumps(row[key], ensure_ascii=False, indent=2))
                    else:
                        setattr(obj, key, row[key])
                obj.id = gen_uuid(res_type='base')
                set_insert_user(obj)
                db.session.add(obj)
                db.session.commit()
                db.session.flush()
            return gen_json_response(code=200, msg='导入成功', extends={'success': True})
        except Exception as e:
            return gen_json_response(code=500, msg=f'导入错误{e}')

    def exportXls(self, req_dict):
        '''
        导出excel
        '''
        selections = req_dict.get('selections', '')
        ids = selections.split(',')
        obj_list = db.session.query(Alert).filter(Alert.id.in_(ids)).all()
        result = []
        for obj in obj_list:
            dic = serialize_alert_model(obj, ser_type='export')
            result.append(dic)
        df = pd.DataFrame(result)
        print(df)
        # 使用字节流存储
        output = io.BytesIO()
        # 保存文件
        df.to_excel(output, index=False)
        # 文件seek位置，从头(0)开始
        output.seek(0)
        return output
