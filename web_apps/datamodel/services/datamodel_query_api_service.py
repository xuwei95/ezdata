'''
数据模型查询api服务
'''
import json
from web_apps import db
from utils.auth import get_auth_token_info, set_update_user
from utils.common_utils import gen_json_response
from web_apps.datamodel.db_models import DataModel, DataModelField
from utils.common_utils import parse_json
from web_apps.datamodel.services.datamodel_service import gen_extract_info, gen_datamodel_conf
from utils.query_utils import get_base_query
from utils.etl_utils import get_reader_model, get_res_fields
from tasks.task_runners.etl_tasks import MyEtlTask
from web_apps.llm.utils import get_llm
from web_apps.llm.services import llm_query_data
from tasks.data_tasks import self_train_rag_data


class DataModelQueryApiService(object):
    def __init__(self):
        pass

    def get_obj_info(self, req_dict):
        '''
        获取查询信息
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(DataModel).filter(
            DataModel.id == obj_id,
            DataModel.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        res_data = gen_datamodel_conf(obj)
        return gen_json_response(data=res_data)

    def operate_obj(self, req_dict, use_auth=True):
        '''
        操作模型
        '''
        obj_id = req_dict.get('id')
        operate = req_dict.get('operate')
        obj = db.session.query(DataModel).filter(
            DataModel.id == obj_id,
            DataModel.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        flag, extract_info = gen_extract_info({
            'model_id': obj_id,
        })
        if not flag:
            return gen_json_response(code=400, msg='未找到查询配置')
        if use_auth:
            user_info = get_auth_token_info()
            if user_info['username'] != 'admin':
                model_conf = extract_info['model']
                depart_list = model_conf.get('depart_list')
                org_code = user_info.get('org_code')
                if org_code not in depart_list:
                    return gen_json_response(code=400, msg='无权限访问此数据模型')
        flag, reader = get_reader_model(extract_info)
        if not flag:
            return gen_json_response(code=400, msg=reader)
        if operate == 'status':
            flag, res = reader.connect()
            if flag:
                obj.status = 1
            else:
                obj.status = 0
                print(res)
            set_update_user(obj)
            db.session.add(obj)
            db.session.commit()
            db.session.flush()
        if operate == 'create':
            field_objs = get_base_query(DataModelField).filter(DataModelField.datamodel_id == obj_id).all()
            field_list = []
            for field_obj in field_objs:
                field_dic = {
                    'field_name': field_obj.field_name,
                    'field_value': field_obj.field_value,
                    **json.loads(field_obj.ext_params)
                }
                field_list.append(field_dic)
            flag, res = reader.create(field_list)
            if flag:
                obj.status = 1
                set_update_user(obj)
                db.session.add(obj)
                db.session.commit()
                db.session.flush()
            else:
                return gen_json_response(code=400, msg=res)
        if operate == 'delete':
            flag, res = reader.delete()
            if flag:
                obj.status = 0
                set_update_user(obj)
                db.session.add(obj)
                db.session.commit()
                db.session.flush()
            else:
                return gen_json_response(code=400, msg=res)
        if operate == 'train':
            # 训练数据模型
            user_info = get_auth_token_info()
            self_train_rag_data.apply_async(args=(obj.id, {'user_name': user_info['username']}, 'datamodel',))
        return gen_json_response(msg='操作成功', extends={'success': True})

    def query_obj_data(self, req_dict, use_auth=True):
        '''
        查询数据模型数据
        '''
        model_id = req_dict.get('id')
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        extract_info = {
            'model_id': model_id,
            'extract_rules': parse_json(req_dict.get('extract_rules', [])),
            'search_text': req_dict.get('search_text', ''),
            'search_type': req_dict.get('search_type', '')
        }
        flag, extract_info = gen_extract_info(extract_info)
        if not flag:
            return gen_json_response(code=400, msg='未找到查询配置')
        if use_auth:
            user_info = get_auth_token_info()
            if user_info['username'] != 'admin':
                model_conf = extract_info['model']
                depart_list = model_conf.get('depart_list')
                org_code = user_info.get('org_code')
                if org_code not in depart_list:
                    return gen_json_response(code=400, msg='无权限访问此数据模型')
        flag, reader = get_reader_model(extract_info)
        if not flag:
            return gen_json_response(code=400, msg=reader)
        ai_query = req_dict.get('ai_query', False)
        query_prompt = req_dict.get('query_prompt', '')
        if ai_query and query_prompt != '':
            _llm = get_llm()
            if _llm is None:
                return gen_json_response(code=400, msg='未找到对应llm配置')
            _flag, res, llm_result = llm_query_data(reader, _llm, query_prompt)
            df = res['value']
            for col in df.select_dtypes(include=['datetime']).columns:
                df[col] = df[col].astype(str)
            df.fillna("", inplace=True)
            data_li = df.to_dict(orient='records')
            res_data = {
                'records': data_li,
                'total': len(data_li),
                'llm_result': llm_result,
                'fields': get_res_fields(data_li),
                'extract_rules': reader.get_extract_rules(),
                'search_type_list': reader.get_search_type_list()
            }
            return gen_json_response(data=res_data)
        flag, res_data = reader.read_page(page=page, pagesize=pagesize)
        if not flag:
            return gen_json_response(code=400, msg=res_data)
        if res_data['code'] == 200:
            res_data['data']['fields'] = get_res_fields(res_data['data'])
            extract_rules = reader.get_extract_rules()
            search_type_list = reader.get_search_type_list()
            print(res_data)
            res_data['data']['extract_rules'] = extract_rules
            res_data['data']['search_type_list'] = search_type_list
            return res_data
        else:
            return res_data

    def etl_preview(self, req_dict):
        '''
        数据集成预览
        '''
        task_params = parse_json(req_dict.get('task_params'))
        run_load = req_dict.get('run_load', False)
        etl_task = MyEtlTask(task_params)
        etl_task.gen_data_models()
        res_data = etl_task.preview(run_load=run_load)
        return res_data


if __name__ == '__main__':
    res = DataModelQueryApiService().query_obj_data({
        "id": "d88b859297224ebcba7fe21efe118ebb",
        "page": 1,
        "pagesize": 10,
        "extract_rules": [],
        "search_type": "",
        "search_text": ""
    }, False)
    print(res)
