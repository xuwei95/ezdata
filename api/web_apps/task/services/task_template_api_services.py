'''
任务模版api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user
from utils.common_utils import gen_json_response, gen_uuid
from web_apps.task.db_models import TaskTemplate, Task
from utils.web_utils import validate_params
import pandas as pd
import io


def serialize_task_template_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'name', 'code', 'icon', 'type', 'component', 'params', 'runner_type', 'runner_code', 'status', 'create_by', 'create_time', 'update_by', 'update_time', 'del_flag', 'sort_no', 'description', 'built_in']:
            if k in []:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in []:
            dic[k] = json.loads(dic[k])
    elif ser_type == 'all_list':
        res = {}
        for k in ['id', 'name', 'code', 'type']:
            res[k] = dic[k]
        return res
        
    return dic

    
class TaskTemplateApiService(object):
    def __init__(self):
        pass
        
    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(TaskTemplate)
        
        # 模版类型 查询逻辑
        typ = req_dict.get('type', '')
        if typ != '':
            query = query.filter(TaskTemplate.type == typ)
        # 模版名称 查询逻辑
        name = req_dict.get('name', '')
        if name != '':
            query = query.filter(TaskTemplate.name.like("%" + name + "%"))
        # 模版编码 查询逻辑
        code = req_dict.get('code', '')
        if code != '':
            query = query.filter(TaskTemplate.code.like("%" + code + "%"))
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_task_template_model(obj, ser_type='list')
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
        query = get_base_query(TaskTemplate)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_task_template_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(TaskTemplate).filter(
            TaskTemplate.id == obj_id,
            TaskTemplate.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_task_template_model(obj, ser_type='detail')
        return gen_json_response(data=dic)
    
    def add_obj(self, req_dict):
        '''
        添加
        '''
        # 模版编码 判重逻辑
        code = req_dict.get('code', '')
        if code != '':
            exist_obj = db.session.query(TaskTemplate).filter(
                TaskTemplate.code == code,
                TaskTemplate.del_flag == 0).first()
            if exist_obj:
                return gen_json_response(code=400, msg='字段"模版编码"已存在')
        obj = TaskTemplate()
        for key in req_dict:
            if key in ['params']:
                try:
                    json_value = json.loads(req_dict[key])
                    setattr(obj, key, json.dumps(json_value, ensure_ascii=False, indent=2))
                except Exception as e:
                    return gen_json_response(code=400, msg=f'{key}必须是json格式')
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
        # 判重逻辑
        exist_query = db.session.query(TaskTemplate).filter(TaskTemplate.id != obj_id)
        code = req_dict.get('code', '')
        if code != '':
            exist_query = exist_query.filter(TaskTemplate.code == code)
        exist_obj = exist_query.first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在')
        obj = db.session.query(TaskTemplate).filter(TaskTemplate.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key in ['params']:
                try:
                    json_value = json.loads(req_dict[key])
                    setattr(obj, key, json.dumps(json_value, ensure_ascii=False, indent=2))
                except Exception as e:
                    return gen_json_response(code=400, msg=f'{key}必须是json格式')
            else:
                setattr(obj, key, req_dict[key])
        if obj.icon in [None, '']:
            obj.icon = 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ'
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='编辑成功', extends={'success': True})

    def check_link_tasks(self, code):
        '''
        判断是否有关联任务，若有禁止删除
        '''
        link_task = db.session.query(Task).filter(Task.del_flag == 0, Task.template_code == code).first()
        return link_task

    def delete_obj(self, req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(TaskTemplate).filter(TaskTemplate.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        link_task = self.check_link_tasks(del_obj.code)
        if link_task:
            return gen_json_response(code=400, msg='模板下存在关联任务，禁止删除')
        if del_obj.built_in == 1:
            return gen_json_response(code=400, msg='内置模版，禁止删除')
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
        del_objs = db.session.query(TaskTemplate).filter(TaskTemplate.id.in_(del_ids)).all()
        link_tasks = [self.check_link_tasks(obj.code) for obj in del_objs]
        if link_tasks != []:
            return gen_json_response(code=400, msg='模板下存在关联任务，禁止删除')
        has_built_in = [i for i in del_objs if i.built_in == 1] != []
        if has_built_in:
            return gen_json_response(code=400, msg='含有内置模版，禁止删除')
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})

    def edit_obj_status(self, req_dict):
        '''
        编辑状态
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(TaskTemplate).filter(TaskTemplate.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        obj.status = 1 if obj.status == 0 else 0
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='操作成功', extends={'success': True})

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
            # 模版名称 判重逻辑
            name_list = [row.get('name', '') for row in data_li]
            if name_list != []:
                exist_obj = db.session.query(TaskTemplate).filter(
                    TaskTemplate.name.in_(name_list),
                    TaskTemplate.del_flag == 0).first()
                if exist_obj:
                    return gen_json_response(code=400, msg='字段"模版名称"已存在')
            # 循环导入
            for row in data_li:
                obj = TaskTemplate()
                for key in row:
                    if key in ['params']:
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
        obj_list = db.session.query(TaskTemplate).filter(TaskTemplate.id.in_(ids)).all()
        result = []
        for obj in obj_list:
            dic = serialize_task_template_model(obj, ser_type='export')
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