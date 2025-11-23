import json
from utils.common_utils import gen_json_to_dict_code


def gen_import_code(params):
    '''
    头部导入模块代码
    :param params:
    :return:
    '''
    base_code = """
'''
${title}模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.${module_name}.services.${module_name}_api_services import ${model_value}ApiService
${module_name}_bp = Blueprint('${module_name}', __name__)
    """
    res_code = base_code
    return res_code


def gen_list_api_code(params):
    '''
    列表查询api代码
    :param params:
    :return:
    '''
    base_code = """
@${module_name}_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions(${list_permissions})
def ${module_name}_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = ${list_verify_dict}
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ${model_value}ApiService.get_obj_list(req_dict)
    return jsonify(res_data)
    """
    # 操作权限
    api_params = [i for i in params['buttons'] if i['function'] == 'list']
    if api_params != []:
        api_params = api_params[0]
        permissions = api_params['permissions'].split(',') if api_params['permissions'] != '' else []
    else:
        permissions = []
    base_code = base_code.replace('${list_permissions}', str(permissions))
    # 入参校验字典
    verify_dict = {
    }
    verify_code = gen_json_to_dict_code(verify_dict, indent=4)
    base_code = base_code.replace('${list_verify_dict}', verify_code)
    res_code = base_code
    return res_code


def gen_all_list_api_code(params):
    '''
    全量列表查询api代码
    :param params:
    :return:
    '''
    base_code = """
@${module_name}_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions(${all_list_permissions})
def ${module_name}_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = ${all_list_verify_dict}
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ${model_value}ApiService.get_obj_all_list(req_dict)
    return jsonify(res_data)
    """
    # 操作权限
    api_params = [i for i in params['buttons'] if i['function'] == 'getAllList']
    if api_params != []:
        api_params = api_params[0]
        permissions = api_params['permissions'].split(',') if api_params['permissions'] != '' else []
    else:
        # 全量列表为非必须接口，若未指定则不使用
        return ''
    base_code = base_code.replace('${all_list_permissions}', str(permissions))
    # 入参校验字典
    verify_dict = {
    }
    verify_code = gen_json_to_dict_code(verify_dict, indent=4)
    base_code = base_code.replace('${all_list_verify_dict}', verify_code)
    res_code = base_code
    return res_code


def gen_detail_api_code(params):
    '''
    详情查询api代码
    :param params:
    :return:
    '''
    base_code = """
@${module_name}_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions(${detail_permissions})
def ${module_name}_detail():
    '''
    详情
    '''
    req_dict = get_req_para(request)
    verify_dict = ${detail_verify_dict}
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ${model_value}ApiService.get_obj_detail(req_dict)
    return jsonify(res_data)
    """
    # 操作权限
    api_params = [i for i in params['buttons'] if i['function'] == 'handleDetail']
    if api_params != []:
        api_params = api_params[0]
        permissions = api_params['permissions'].split(',') if api_params['permissions'] != '' else []
    else:
        permissions = []
    base_code = base_code.replace('${detail_permissions}', str(permissions))
    # 入参校验字典
    verify_dict = {
        'id': {
            'name': 'id',
            'required': True
        }
    }
    verify_code = gen_json_to_dict_code(verify_dict, indent=4)
    base_code = base_code.replace('${detail_verify_dict}', verify_code)
    res_code = base_code
    return res_code


def gen_add_api_code(params):
    '''
    添加api代码
    :param params:
    :return:
    '''
    base_code = """
@${module_name}_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(${add_permissions})
def ${module_name}_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = ${add_verify_dict}
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ${model_value}ApiService.add_obj(req_dict)
    return jsonify(res_data)
    """
    # 操作权限
    api_params = [i for i in params['buttons'] if i['function'] == 'handleAdd']
    if api_params != []:
        api_params = api_params[0]
        permissions = api_params['permissions'].split(',') if api_params['permissions'] != '' else []
    else:
        permissions = []
    base_code = base_code.replace('${add_permissions}', str(permissions))
    # 入参校验字典
    verify_dict = {}
    nullable_fields = [i for i in params['fields'] if i['nullable'] == 0 and i['field'] != 'id']
    for field in nullable_fields:
        verify_dict[field['field']] = {
            'name': field['label'],
            'required': True
        }
    verify_code = gen_json_to_dict_code(verify_dict, indent=4)
    base_code = base_code.replace('${add_verify_dict}', verify_code)
    res_code = base_code
    return res_code


def gen_edit_api_code(params):
    '''
    编辑api代码
    :param params:
    :return:
    '''
    base_code = """
@${module_name}_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(${edit_permissions})
def ${module_name}_edit():
    '''
    编辑
    '''
    req_dict = get_req_para(request)
    verify_dict = ${edit_verify_dict}
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ${model_value}ApiService.edit_obj(req_dict)
    return jsonify(res_data)
    """
    # 操作权限
    api_params = [i for i in params['buttons'] if i['function'] == 'handleEdit']
    if api_params != []:
        api_params = api_params[0]
        permissions = api_params['permissions'].split(',') if api_params['permissions'] != '' else []
    else:
        permissions = []
    base_code = base_code.replace('${edit_permissions}', str(permissions))
    # 入参校验字典
    verify_dict = {
        'id': {
            'name': 'id',
            'required': True
        }
    }
    nullable_fields = [i for i in params['fields'] if i['nullable'] == 0 and i['field'] != 'id']
    for field in nullable_fields:
        verify_dict[field['field']] = {
            'name': field['label'],
            'required': True
        }
    verify_code = gen_json_to_dict_code(verify_dict, indent=4)
    base_code = base_code.replace('${edit_verify_dict}', verify_code)
    res_code = base_code
    return res_code


def gen_delete_api_code(params):
    '''
    删除api代码
    :param params:
    :return:
    '''
    base_code = """
@${module_name}_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(${delete_permissions})
def ${module_name}_delete():
    '''
    删除
    '''
    req_dict = get_req_para(request)
    verify_dict = ${delete_verify_dict}
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ${model_value}ApiService.delete_obj(req_dict)
    return jsonify(res_data)
    """
    # 操作权限
    api_params = [i for i in params['buttons'] if i['function'] == 'handleDelete']
    if api_params != []:
        api_params = api_params[0]
        permissions = api_params['permissions'].split(',') if api_params['permissions'] != '' else []
    else:
        permissions = []
    base_code = base_code.replace('${delete_permissions}', str(permissions))
    # 入参校验字典
    verify_dict = {
        'id': {
            'name': 'id',
            'required': True
        }
    }
    verify_code = gen_json_to_dict_code(verify_dict, indent=4)
    base_code = base_code.replace('${delete_verify_dict}', verify_code)
    res_code = base_code
    return res_code


def gen_deleteBatch_api_code(params):
    '''
    批量删除api代码
    :param params:
    :return:
    '''
    base_code = """
@${module_name}_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(${deleteBatch_permissions})
def ${module_name}_deleteBatch():
    '''
    批量删除
    '''
    req_dict = get_req_para(request)
    verify_dict = ${deleteBatch_verify_dict}
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ${model_value}ApiService.delete_batch(req_dict)
    return jsonify(res_data)
    """
    # 操作权限
    api_params = [i for i in params['buttons'] if i['function'] == 'batchHandleDelete']
    if api_params != []:
        api_params = api_params[0]
        permissions = api_params['permissions'].split(',') if api_params['permissions'] != '' else [] if api_params['permissions'] != '' else []
    else:
        permissions = []
    base_code = base_code.replace('${deleteBatch_permissions}', str(permissions))
    # 入参校验字典
    verify_dict = {
        'ids': {
            'name': 'id列表',
            'required': True
        }
    }
    verify_code = gen_json_to_dict_code(verify_dict, indent=4)
    base_code = base_code.replace('${deleteBatch_verify_dict}', verify_code)
    res_code = base_code
    return res_code


def gen_importExcel_api_code(params):
    '''
    excel导入api代码
    :param params:
    :return:
    '''
    base_code = """
@${module_name}_bp.route('/importExcel', methods=['POST'])
@validate_user
@validate_permissions(${importExcel_permissions})
def ${module_name}_importExcel():
    '''
    excel导入
    '''
    file = request.files.get('file', '')
    if file == '':
        res_data = gen_json_response(code=400, msg='请上传文件')
    else:
        res_data = ${model_value}ApiService.importExcel(file)
    return jsonify(res_data)
    """
    # 操作权限
    api_params = [i for i in params['buttons'] if i['function'] == 'onImportXls']
    if api_params != []:
        api_params = api_params[0]
        permissions = api_params['permissions'].split(',') if api_params['permissions'] != '' else []
    else:
        # 导入为非必须接口，若未指定则不使用
        return ''
    base_code = base_code.replace('${importExcel_permissions}', str(permissions))
    res_code = base_code
    return res_code


def gen_exportXls_api_code(params):
    '''
    导出excel api代码
    :param params:
    :return:
    '''
    base_code = """
@${module_name}_bp.route('/exportXls', methods=['GET'])
@validate_user
@validate_permissions(${exportXls_permissions})
def ${module_name}_exportXls():
    '''
    导出excel 
    '''
    req_dict = get_req_para(request)
    verify_dict = ${exportXls_verify_dict}
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    try:
        output_file = ${model_value}ApiService.exportXls(req_dict)
        return generate_download_file(output_file, 'output')
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"未知错误：{e}"))
    """
    # 操作权限
    api_params = [i for i in params['buttons'] if i['function'] == 'onExportXls']
    if api_params != []:
        api_params = api_params[0]
        permissions = api_params['permissions'].split(',') if api_params['permissions'] != '' else []
    else:
        # 导出为非必须接口，若未指定则不使用
        return ''
    base_code = base_code.replace('${exportXls_permissions}', str(permissions))
    # 入参校验字典
    verify_dict = {
        'selections': {
            'name': '选择项',
            'required': True
        }
    }
    verify_code = gen_json_to_dict_code(verify_dict, indent=4)
    base_code = base_code.replace('${exportXls_verify_dict}', verify_code)
    res_code = base_code
    return res_code


def gen_other_api_code(params):
    '''
    其他 api代码
    :param params:
    :return:
    '''
    base_code = """
    """
    res_code = base_code
    return res_code


def gen_views_code(params):
    '''
    组合生成路由视图代码
    :return:
    '''
    import_code = gen_import_code(params)
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
    template_code = f"""
{import_code}
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
    views_code = gen_views_code(params)
    print(views_code)
    f = open('out/views.py', 'w')
    f.write(views_code)
