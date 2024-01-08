'''
数据接口api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid, get_now_time, parse_json, timestamp_to_date, trans_dict_to_rules, trans_time_length
from web_apps.datamodel.db_models import DataInterface, DataModel
from web_apps.datamodel.services.datamodel_service import gen_datamodel_conf, gen_datasource_conf
from utils.etl_utils import get_reader_model, get_res_fields
from utils.web_utils import validate_params
import pandas as pd
import io
from utils.log_utils import get_interface_logger
interface_log_keys = {
    'duration': '',
    'interface_id': '',
    'interface_name': '',
    'datamodel_id': '',
    'api_key': '',
    'apply_user_id': '',
    'apply_user': '',
    'valid_time': '',
    'valid_fields': ''
}
interface_logger = get_interface_logger(interface_log_keys)


def serialize_data_interface_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in dic.keys():
            if k in ['valid_time', 'apply_time', 'review_time']:
                res[k] = timestamp_to_date(dic[k], '')
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
        for k in ['id', 'datamodel_id', 'name', 'status']:
            if k in []:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    return dic


def gen_interface_info(api_key):
    '''
    组合数据接口信息
    :param api_key:
    :return:
    '''
    # todo: redis缓存
    interface_obj = get_base_query(DataInterface).filter(DataInterface.api_key == api_key).first()
    if interface_obj is None:
        return False, '无效api_key'
    datamodel_obj = get_base_query(DataModel).filter(DataModel.id == interface_obj.datamodel_id).first()
    if datamodel_obj is None:
        return False, '未找到数据模型'
    _source = gen_datasource_conf(datamodel_obj.datasource_id)
    model_conf = gen_datamodel_conf(interface_obj.datamodel_id)
    interface_info = {
        'api_key': interface_obj.api_key,
        'interface_id': interface_obj.id,
        'interface_name': interface_obj.name,
        'datamodel_id': interface_obj.datamodel_id,
        'apply_user': interface_obj.apply_user,
        'apply_user_id': interface_obj.apply_user_id,
        'valid_time': interface_obj.valid_time,
        'valid_fields': interface_obj.valid_fields.split(','),
        'status': interface_obj.status,
        'model': model_conf,
        'source': _source
    }
    return True, interface_info


class DataInterfaceApiService(object):
    def __init__(self):
        pass

    def query(self, req_dict, request_method='POST'):
        '''
        查询数据
        '''
        st = get_now_time('')
        api_key = req_dict.get('api_key')
        show_info = req_dict.get('show_info', '')
        if request_method == 'GET':
            rule_dict = {}
            for k in req_dict:
                if k not in ['api_key', 'show_info', 'page', 'pagesize']:
                    rule_dict[k] = req_dict[k]
            extract_rules = trans_dict_to_rules(rule_dict)
        else:
            extract_rules = parse_json(req_dict.get('extract_rules', []))
        print(extract_rules)
        flag, interface_info = gen_interface_info(api_key)
        if not flag:
            return gen_json_response(code=400, msg=interface_info)
        now = get_now_time('')
        if now > interface_info['valid_time']:
            return gen_json_response(code=400, msg='接口时效已过期')
        if interface_info['status'] == 0:
            return gen_json_response(code=400, msg='接口已被禁用')
        interface_info['extract_info'] = {
            'extract_rules': extract_rules
        }
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        flag, reader = get_reader_model(interface_info)
        if not flag:
            return gen_json_response(code=400, msg=reader)
        flag, res_data = reader.read_page(page=page, pagesize=pagesize)
        # 记录接口日志
        interface_log_info = {}
        for k in interface_log_keys:
            interface_log_info[k] = interface_info.get(k, '')
        et = get_now_time('')
        interface_log_info['duration'] = round(et - st, 3)
        print(interface_log_info)
        interface_logger.info(interface_log_info)
        if flag:
            if str(show_info) == '1' and res_data['code'] == 200:
                res_data['data']['fields'] = get_res_fields(res_data['data'])
                extract_rules = reader.get_extract_rules()
                search_type_list = reader.get_search_type_list()
                res_data['data']['extract_rules'] = extract_rules
                res_data['data']['search_type_list'] = search_type_list
            return res_data
        else:
            return gen_json_response(code=400, msg=res_data)

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(DataInterface)
        datamodel_id = req_dict.get('datamodel_id', '')
        if datamodel_id != '':
            query = query.filter(DataInterface.datamodel_id == datamodel_id)
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_data_interface_model(obj, ser_type='list')
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
        query = get_base_query(DataInterface)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_data_interface_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(DataInterface).filter(
            DataInterface.id == obj_id,
            DataInterface.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_data_interface_model(obj, ser_type='detail')
        return gen_json_response(data=dic)
    
    def apply_obj(self, req_dict):
        '''
        申请
        '''
        # 接口名称 判重逻辑
        name = req_dict.get('name', '')
        datamodel_id = req_dict.get('datamodel_id')
        if name != '':
            exist_obj = db.session.query(DataInterface).filter(
                DataInterface.datamodel_id == datamodel_id,
                DataInterface.name == name,
                DataInterface.del_flag == 0).first()
            if exist_obj:
                return gen_json_response(code=400, msg='字段"接口名称"已存在')
        obj = DataInterface()
        for key in req_dict:
            # if key in ['valid_fields']:
            #     v = req_dict[key].split(',')
            #     setattr(obj, key, json.dumps(v, ensure_ascii=False, indent=2))
            # else:
            setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        obj.api_key = gen_uuid(res_type='base')
        user_info = get_auth_token_info()
        obj.apply_user_id = user_info.get('id')
        obj.apply_user = user_info.get('username')
        obj.apply_time = get_now_time()
        # 申请时状态禁用，有效期限0
        obj.valid_time = 0
        obj.status = 0
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='添加成功', extends={'success': True})
    
    def review_obj(self, req_dict):
        '''
        审核
        '''
        obj_id = req_dict.get('id')
        # 判重逻辑
        datamodel_id = req_dict.get('datamodel_id')
        exist_query = db.session.query(DataInterface).filter(DataInterface.id != obj_id, DataInterface.datamodel_id == datamodel_id)
        name = req_dict.get('name', '')
        if name != '':
            exist_query = exist_query.filter(DataInterface.name == name)
        exist_obj = exist_query.first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在')
        obj = db.session.query(DataInterface).filter(DataInterface.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            # if key in ['valid_fields']:
            #     v = req_dict[key].split(',')
            #     setattr(obj, key, json.dumps(v, ensure_ascii=False, indent=2))
            # else:
            setattr(obj, key, req_dict[key])
        user_info = get_auth_token_info()
        obj.review_user_id = user_info.get('id')
        obj.review_user = user_info.get('username')
        obj.review_time = get_now_time()
        # 审核时状态启用，有效期限转换
        obj.valid_time = obj.review_time + trans_time_length(obj.review_time_length)
        obj.status = 1
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='操作成功', extends={'success': True})

    def edit_obj_status(self, req_dict):
        '''
        编辑状态
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(DataInterface).filter(DataInterface.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        obj.status = 1 if obj.status == 0 else 0
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='操作成功', extends={'success': True})
    
    def delete_obj(self, req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(DataInterface).filter(DataInterface.id == obj_id).first()
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
        del_objs = db.session.query(DataInterface).filter(DataInterface.id.in_(del_ids)).all()
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
                    "datamodel_id": {
                        "name": "所属数据模型",
                        "required": True
                    },
                    "name": {
                        "name": "接口名称",
                        "required": True
                    },
                    "status": {
                        "name": "状态",
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
            # 接口名称 判重逻辑
            name_list = [row.get('name', '') for row in data_li]
            if name_list != []:
                exist_obj = db.session.query(DataInterface).filter(
                    DataInterface.name.in_(name_list),
                    DataInterface.del_flag == 0).first()
                if exist_obj:
                    return gen_json_response(code=400, msg='字段"接口名称"已存在')
            # 循环导入
            for row in data_li:
                obj = DataInterface()
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
        obj_list = db.session.query(DataInterface).filter(DataInterface.id.in_(ids)).all()
        result = []
        for obj in obj_list:
            dic = serialize_data_interface_model(obj, ser_type='export')
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


if __name__ == '__main__':
    from web_apps import app
    with app.app_context():
        req_dict = {
            "api_key": "f282756633214b04b5a00b81b2aa5342",
            "page": "10",
        }
        DataInterfaceApiService().query(req_dict, 'GET')
