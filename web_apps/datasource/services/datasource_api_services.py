'''
数据源管理api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid
from web_apps.datasource.db_models import DataSource
from utils.web_utils import validate_params
import pandas as pd
import io
from utils.etl_utils import get_reader_model


def serialize_datasource_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'name', 'type', 'conn_conf', 'status', 'ext_params', 'description', 'create_by', 'create_time', 'update_by', 'update_time', 'sort_no', 'del_flag']:
            if k in ['conn_conf', 'ext_params']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in ['conn_conf']:
            dic[k] = json.loads(dic[k])
        for k in []:
            dic.pop(k)
    elif ser_type == 'all_list':
        res = {}
        for k in ['id', 'name', 'type']:
            if k in ['conn_conf', 'ext_params']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
        
    return dic

    
class DataSourceApiService(object):
    def __init__(self):
        pass
        
    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(DataSource)
        # 数据源名称 查询逻辑
        name = req_dict.get('name', '')
        if name != '':
            query = query.filter(DataSource.name.like("%" + name + "%"))
        # 数据源类型 查询逻辑
        type = req_dict.get('type', '')
        if type != '':
            query = query.filter(DataSource.type.like("%" + type + "%"))
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_datasource_model(obj, ser_type='list')
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
        query = get_base_query(DataSource)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_datasource_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(DataSource).filter(
            DataSource.id == obj_id,
            DataSource.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_datasource_model(obj, ser_type='detail')
        return gen_json_response(data=dic)
    
    def add_obj(self, req_dict):
        '''
        添加
        '''
        # 名称 判重逻辑
        name = req_dict.get('name', '')
        if name != '':
            exist_obj = db.session.query(DataSource).filter(
                DataSource.name == name,
                DataSource.del_flag == 0).first()
            if exist_obj:
                return gen_json_response(code=400, msg='字段"名称"已存在')
        obj = DataSource()
        for key in req_dict:
            if key in ['conn_conf']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'ext_params':
                try:
                    json_value = json.loads(req_dict[key])
                    obj.ext_params = json.dumps(json_value, ensure_ascii=False, indent=2)
                except Exception as e:
                    return gen_json_response(code=400, msg='额外参数必须是json格式')
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.flush()
        return gen_json_response(msg='添加成功', extends={'success': True})
    
    def edit_obj(self, req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        # 判重逻辑
        exist_query = db.session.query(DataSource).filter(DataSource.id != obj_id, DataSource.del_flag == 0)
        name = req_dict.get('name', '')
        if name != '':
            exist_query = exist_query.filter(DataSource.name == name)
        exist_obj = exist_query.first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在')
        obj = db.session.query(DataSource).filter(DataSource.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key in ['conn_conf']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'ext_params':
                try:
                    json_value = json.loads(req_dict[key])
                    obj.ext_params = json.dumps(json_value, ensure_ascii=False, indent=2)
                except Exception as e:
                    return gen_json_response(code=400, msg='额外参数必须是json格式')
            else:
                setattr(obj, key, req_dict[key])
        set_update_user(obj)
        db.session.add(obj)
        db.session.flush()
        return gen_json_response(msg='编辑成功', extends={'success': True})
    
    def delete_obj(self, req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(DataSource).filter(DataSource.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        del_obj.del_flag = 1
        set_update_user(del_obj)
        db.session.add(del_obj)
        db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    def delete_batch(self, req_dict):
        '''
        批量删除
        '''
        del_ids = req_dict.get('ids')
        if isinstance(del_ids, str):
            del_ids = del_ids.split(',')
        del_objs = db.session.query(DataSource).filter(DataSource.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
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
                    "name": {
                        "name": "名称",
                        "required": True
                    },
                    "type": {
                        "name": "类型",
                        "required": True
                    },
                    "conn_conf": {
                        "name": "连接配置",
                        "required": True
                    }
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
            # 名称 判重逻辑
            name_list = [row.get('name', '') for row in data_li]
            print(name_list)
            if name_list != []:
                exist_obj = db.session.query(DataSource).filter(
                    DataSource.name.in_(name_list),
                    DataSource.del_flag == 0).first()
                if exist_obj:
                    return gen_json_response(code=400, msg='字段"名称"已存在')
            # 循环导入
            for row in data_li:
                obj = DataSource()
                for key in row:
                    if key in ['conn_conf', 'ext_params']:
                        setattr(obj, key, json.dumps(row[key], ensure_ascii=False, indent=2))
                    else:
                        setattr(obj, key, row[key])
                obj.id = gen_uuid(res_type='base')
                set_insert_user(obj)
                db.session.add(obj)
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
        obj_list = db.session.query(DataSource).filter(DataSource.id.in_(ids)).all()
        result = []
        for obj in obj_list:
            dic = serialize_datasource_model(obj, ser_type='list')
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

    def connTest(self, req_dict):
        '''
        连接测试
        '''
        conn_type = req_dict.get('type')
        conn_conf = req_dict.get('conn_conf')
        model_info = {
            'source': {
                "name": "",
                "type": conn_type,
                "conn_conf": conn_conf,
                "ext_params": {}
            },
            'model': {},
            'extract_info': {
                'batch_size': 1,
                'extract_rules': []
            }
        }
        flag, reader = get_reader_model(model_info)
        if flag:
            flag, res = reader.connect()
            if flag:
                return gen_json_response(msg=res, extends={'success': True})
            else:
                return gen_json_response(code=400, msg=f'连接失败:{res}')
        else:
            return gen_json_response(code=400, msg=f'连接失败:{reader}')


if __name__ == '__main__':
    req_dict = {"type": "mongodb", "conn_conf": {"host": "124.220.54.30", "port": 27017, "username": "root", "password": "Datacenter123", "database_name": "datacenter"}}
    # req_dict = {
    #     "type": "elasticsearch",
    #     "conn_conf": {
    #         "auth_type": 1,
    #         "url": "101.35.23.52:9200"
    #     }
    # }
    res = DataSourceApiService().connTest(req_dict)
    print(res)