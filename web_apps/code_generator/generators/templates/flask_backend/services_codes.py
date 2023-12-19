import json
import os.path

from utils.common_utils import gen_json_to_dict_code


def gen_import_code(params):
    '''
    头部导入模块代码
    :param params:
    :return:
    '''
    base_code = """
'''
${title}api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid
from web_apps.${module_name}.db_models import ${model_value}
${import_codes}
    """
    api_params = [i for i in params['buttons'] if i['function'] in ['onExportXls', 'onImportXls']]
    if api_params == []:
        # 非必须接口，若未指定则不使用
        import_codes = ''
    else:
        import_codes = """
from utils.web_utils import validate_params
import pandas as pd
import io
""".strip()
    base_code = base_code.replace('${import_codes}', import_codes)
    res_code = base_code
    return res_code


def gen_serialize_code(params):
    '''
    生成序列化模型代码
    :param params:
    :return:
    '''
    base_code = """
def serialize_${module_name}_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ${list_api_fields}:
            if k in ${json_fields}:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in ${json_fields}:
            dic[k] = json.loads(dic[k])
        for k in ${detail_ignore_fields}:
            dic.pop(k)${all_list_ser_code}
    return dic
    """
    fields = params.get('fields')
    all_list_api_params = [i for i in params['buttons'] if i['function'] == 'getAllList']
    if all_list_api_params != []:
        all_list_api_fields = [i['field'] for i in fields if i['all_list_show']]
        all_list_ser_code = """
    elif ser_type == 'all_list':
        res = {}
        for k in ${all_list_api_fields}:
            if k in ${json_fields}:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
        """
        all_list_ser_code = all_list_ser_code.replace('${all_list_api_fields}', str(all_list_api_fields).strip())
    else:
        # 全量列表为非必须接口，若未指定则不使用
        all_list_ser_code = ''
    base_code = base_code.replace('${all_list_ser_code}', all_list_ser_code)
    list_api_fields = [i['field'] for i in fields if i['list_show']]
    detail_ignore_fields = [i['field'] for i in fields if not i['detail_show']]
    json_fields = [i['field'] for i in fields if i['is_json']]
    base_code = base_code.replace('${list_api_fields}', str(list_api_fields))
    base_code = base_code.replace('${detail_ignore_fields}', str(detail_ignore_fields))
    base_code = base_code.replace('${json_fields}', str(json_fields))
    module_name = params.get('module_name')
    base_code = base_code.replace('${module_name}', str(module_name)).strip()
    return base_code


def gen_list_api_code(params):
    '''
    生成列表接口代码
    :param params:
    :return:
    '''
    base_code = """
    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(${model_value})
        ${query_params_code}
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_${module_name}_model(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)
    """
    query_params = params.get('query_params', [])
    query_params_codes = []
    model_value = params['model_value']
    for query_param in query_params:
        label = query_param['label']
        field = query_param['field']
        single_code = f"""
        # {label} 查询逻辑
        {field} = req_dict.get('{field}', '')
        if {field} != '':
            # query = query.filter({model_value}.{field}.like("%" + {field} + "%"))
            pass"""
        query_params_codes.append(single_code)
    query_params_code = '\n'.join(query_params_codes)
    res_code = base_code.replace('${query_params_code}', query_params_code).strip()
    return res_code


def gen_all_list_api_code(params):
    '''
    生成全量列表列表接口代码
    :param params:
    :return:
    '''
    base_code = """
    def get_obj_all_list(self, req_dict):
        '''
        获取全量列表
        '''
        query = get_base_query(${model_value})
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_${module_name}_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    """
    # 操作权限
    api_params = [i for i in params['buttons'] if i['function'] == 'getAllList']
    if api_params == []:
        # 全量列表为非必须接口，若未指定则不使用
        return ''
    res_code = base_code
    return res_code


def gen_detail_api_code(params):
    '''
    生成详情列表接口代码
    :param params:
    :return:
    '''
    base_code = """
    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(${model_value}).filter(
            ${model_value}.id == obj_id,
            ${model_value}.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_${module_name}_model(obj, ser_type='detail')
        return gen_json_response(data=dic)
    """
    res_code = base_code.strip()
    return res_code


def gen_add_api_code(params):
    '''
    生成添加接口代码
    :param params:
    :return:
    '''
    base_code = """
    def add_obj(self, req_dict):
        '''
        添加
        '''
        ${exist_check_code}
        obj = ${model_value}()
        for key in req_dict:
            if key in ${json_fields}:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        ${gen_id_code}
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='添加成功', extends={'success': True})
    """
    fields = params['fields']
    # 生成主键代码
    id_field = [i for i in fields if i['field'] == 'id']
    if id_field != [] and id_field[0].get('field_type') == 'String':
        gen_id_code = "obj.id = gen_uuid(res_type='base')"
    else:
        gen_id_code = ''
    res_code = base_code.replace('${gen_id_code}', gen_id_code)
    # 唯一性判断代码
    only_fields = [i for i in fields if i['is_only'] == 1 and i['field'] != 'id']
    if only_fields == []:
        exist_check_code = ''
    else:
        exist_check_codes = []
        model_value = params.get('model_value')
        for only_field in only_fields:
            field = only_field['field']
            label = only_field['label']
            if field != 'id':
                single_code = f"""
        # {label} 判重逻辑
        {field} = req_dict.get('{field}', '')
        if {field} != '':
            exist_obj = db.session.query({model_value}).filter(
                {model_value}.{field} == {field},
                {model_value}.del_flag == 0).first()
            if exist_obj:
                return gen_json_response(code=400, msg='字段"{label}"已存在')"""
                exist_check_codes.append(single_code)
        exist_check_code = ''.join(exist_check_codes).strip()
    res_code = res_code.replace('${exist_check_code}', exist_check_code)
    json_fields = [i['field'] for i in fields if i['is_json']]
    res_code = res_code.replace('${json_fields}', str(json_fields))
    return res_code


def gen_edit_api_code(params):
    '''
    生成编辑接口代码
    :param params:
    :return:
    '''
    base_code = """
    def edit_obj(self, req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        ${exist_check_code}
        obj = db.session.query(${model_value}).filter(${model_value}.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key in ${json_fields}:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='编辑成功', extends={'success': True})
    """
    fields = params['fields']
    # 唯一性判断代码
    only_fields = [i for i in fields if i['is_only'] == 1 and i['field'] != 'id']
    if only_fields == []:
        exist_check_code = ''
    else:
        model_value = params.get('model_value')
        exist_query_codes = []
        for only_field in only_fields:
            field = only_field['field']
            if field != 'id':
                single_code = f"""
        {field} = req_dict.get('{field}', '')
        if {field} != '':
            exist_query = exist_query.filter({model_value}.{field} == {field})"""
                exist_query_codes.append(single_code)
        exist_query_code = '\n'.join(exist_query_codes).strip()
        exist_check_code = f"""
        # 判重逻辑
        exist_query = db.session.query({model_value}).filter({model_value}.id != obj_id)
        {exist_query_code}
        exist_obj = exist_query.first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在')
        """
    res_code = base_code.replace('${exist_check_code}', exist_check_code.strip())
    json_fields = [i['field'] for i in fields if i['is_json']]
    res_code = res_code.replace('${json_fields}', str(json_fields)).strip()
    return res_code


def gen_delete_api_code(params):
    '''
    生成删除接口代码
    :param params:
    :return:
    '''
    base_code = """
    def delete_obj(self, req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(${model_value}).filter(${model_value}.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        del_obj.del_flag = 1
        set_update_user(del_obj)
        db.session.add(del_obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    """
    res_code = base_code
    return res_code


def gen_deleteBatch_api_code(params):
    '''
    生成批量删除接口代码
    :param params:
    :return:
    '''
    base_code = """
    def delete_batch(self, req_dict):
        '''
        批量删除
        '''
        del_ids = req_dict.get('ids')
        if isinstance(del_ids, str):
            del_ids = del_ids.split(',')
        del_objs = db.session.query(${model_value}).filter(${model_value}.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    """
    res_code = base_code.strip()
    return res_code


def gen_importExcel_api_code(params):
    '''
    生成excel导入接口代码
    :param params:
    :return:
    '''
    base_code = """
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
                verify_dict = ${verify_dict}
                not_valid = validate_params(row, verify_dict)
                if not_valid:
                    not_valid = {
                        'code': 400,
                        'msg': f'第{n}行{not_valid}'
                    }
                    return not_valid
                data_li.append(row)
                n += 1
            ${exist_check_code}
            # 循环导入
            for row in data_li:
                obj = ${model_value}()
                for key in row:
                    if key in ${json_fields}:
                        setattr(obj, key, json.dumps(row[key], ensure_ascii=False, indent=2))
                    else:
                        setattr(obj, key, row[key])
                ${gen_id_code}
                set_insert_user(obj)
                db.session.add(obj)
                db.session.commit()
                db.session.flush()
            return gen_json_response(code=200, msg='导入成功', extends={'success': True})
        except Exception as e:
            return gen_json_response(code=500, msg=f'导入错误{e}')
    """
    api_params = [i for i in params['buttons'] if i['function'] == 'onImportXls']
    if api_params == []:
        # 非必须接口，若未指定则不使用
        return ''
    # 入参校验字典
    verify_dict = {}
    nullable_fields = [i for i in params['fields'] if i['nullable'] == 0 and i['field'] != 'id']
    for field in nullable_fields:
        verify_dict[field['field']] = {
            'name': field['label'],
            'required': True
        }
    verify_code = gen_json_to_dict_code(verify_dict, indent=4)
    res_code = base_code.replace('${verify_dict}', verify_code)
    fields = params['fields']
    # 生成主键代码
    id_field = [i for i in fields if i['field'] == 'id']
    if id_field != [] and id_field[0].get('field_type') == 'String':
        gen_id_code = "obj.id = gen_uuid(res_type='base')"
    else:
        gen_id_code = ''
    res_code = res_code.replace('${gen_id_code}', gen_id_code)
    # 唯一性判断代码
    only_fields = [i for i in fields if i['is_only'] == 1 and i['field'] != 'id']
    if only_fields == []:
        exist_check_code = ''
    else:
        exist_check_codes = []
        model_value = params.get('model_value')
        for only_field in only_fields:
            field = only_field['field']
            label = only_field['label']
            if field != 'id':
                single_code = f"""
            # {label} 判重逻辑
            {field}_list = [row.get('{field}', '') for row in data_li]
            if {field}_list != []:
                exist_obj = db.session.query({model_value}).filter(
                    {model_value}.{field}.in_({field}_list),
                    {model_value}.del_flag == 0).first()
                if exist_obj:
                    return gen_json_response(code=400, msg='字段"{label}"已存在')"""
                exist_check_codes.append(single_code)
        exist_check_code = ''.join(exist_check_codes).strip()
    res_code = res_code.replace('${exist_check_code}', exist_check_code)
    json_fields = [i['field'] for i in fields if i['is_json']]
    res_code = res_code.replace('${json_fields}', str(json_fields))
    return res_code


def gen_exportXls_api_code(params):
    '''
    生成excel导出接口代码
    :param params:
    :return:
    '''
    base_code = """
    def exportXls(self, req_dict):
        '''
        导出excel
        '''
        selections = req_dict.get('selections', '')
        ids = selections.split(',')
        obj_list = db.session.query(${model_value}).filter(${model_value}.id.in_(ids)).all()
        result = []
        for obj in obj_list:
            dic = serialize_${module_name}_model(obj, ser_type='export')
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
    """
    # 操作权限
    api_params = [i for i in params['buttons'] if i['function'] == 'onExportXls']
    if api_params == []:
        # 非必须接口，若未指定则不使用
        return ''
    res_code = base_code
    return res_code


def gen_other_api_code(params):
    '''
    生成其他接口代码
    :param params:
    :return:
    '''
    base_code = """
    """
    res_code = base_code
    return res_code


def gen_api_service_code(params):
    '''
    生成api service 代码
    :param params:
    :return:
    '''
    list_api_code = gen_list_api_code(params)
    all_list_api_code = gen_all_list_api_code(params)
    detail_api_code = gen_detail_api_code(params)
    add_api_code = gen_add_api_code(params)
    edit_api_code = gen_edit_api_code(params)
    delete_api_code = gen_delete_api_code(params)
    deleteBatch_api_code = gen_deleteBatch_api_code(params)
    importExcel_api_code = gen_importExcel_api_code(params)
    exportXls_api_code = gen_exportXls_api_code(params)
    other_api_code = gen_other_api_code(params)
    model_value = params.get('model_value')
    base_code = f"""
    
class {model_value}ApiService(object):
    def __init__(self):
        pass
        
    {list_api_code}
    {all_list_api_code}
    {detail_api_code}
    {add_api_code}
    {edit_api_code}
    {delete_api_code}
    {deleteBatch_api_code}
    {importExcel_api_code}
    {exportXls_api_code}
    {other_api_code}
    """
    res_code = base_code
    return res_code


def gen_services_code(params):
    '''
    组合生成服务代码
    :return:
    '''
    import_code = gen_import_code(params)
    serialize_code = gen_serialize_code(params)
    api_service_code = gen_api_service_code(params)
    template_code = f"""
{import_code}
{serialize_code}
{api_service_code}
        """
    for k in ['title', 'module_name', 'model_value']:
        v = params.get(k)
        print(k, v)
        template_code = template_code.replace('${%s}' % k, v)
    template_code = template_code.strip() + '\n'
    print(template_code)
    return template_code


if __name__ == '__main__':
    from web_apps.code_generator.db_models import CodeGenModel, db
    obj = db.session.query(CodeGenModel).filter(CodeGenModel.id == '5deb88593c024033ae6de2f9ed5e7806').first()
    params = obj.to_dict()
    params['fields'] = json.loads(params['fields'])
    params['query_params'] = json.loads(params['query_params'])
    params['buttons'] = json.loads(params['buttons'])
    print(params)
    views_code = gen_services_code(params)
    print(views_code)
    if not os.path.exists('out/services'):
        os.mkdir('out/services')
    f = open('out/services/api_service.py', 'w')
    f.write(views_code)
