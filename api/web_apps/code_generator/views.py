'''
代码生成器模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.code_generator.services.code_gen_api_services import CodeGenApiService
code_gen_bp = Blueprint('code_gen', __name__)


@code_gen_bp.route('/list', methods=['GET'])
@validate_user
def code_gen_list():
    """
    列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = CodeGenApiService().get_obj_list(req_dict)
    return jsonify(res_data)


@code_gen_bp.route('/queryById', methods=['GET'])
@validate_user
def screen_list():
    """
    列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = CodeGenApiService().get_obj_detail(req_dict)
    return jsonify(res_data)


@code_gen_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['codegen:add'])
def code_gen_add():
    """
    添加
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'title': {
            'name': '项目名称',
            'not_empty': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = CodeGenApiService().add_obj(req_dict)
    return jsonify(res_data)


@code_gen_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['codegen:edit'])
def code_gen_edit():
    """
    更新
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = CodeGenApiService().edit_obj(req_dict)
    return jsonify(res_data)


@code_gen_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['codegen:delete'])
def code_gen_delete():
    """
    删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = CodeGenApiService().delete_obj(req_dict)
    return jsonify(res_data)


@code_gen_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['codegen:delete'])
def code_gen_delete_batch():
    """
    批量删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = CodeGenApiService().delete_obj(req_dict)
    return jsonify(res_data)


@code_gen_bp.route('/code_generate', methods=['POST'])
@validate_user
@validate_permissions(['codegen:generate'])
def code_gen_generate():
    """
    生成代码
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'id': {
            'name': 'id',
            'required': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = CodeGenApiService().generate_code(req_dict)
    return jsonify(res_data)


@code_gen_bp.route('/code_export', methods=['POST'])
@validate_user
def code_gen_export():
    """
    导出代码
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'data': {
            'name': '数据',
            'required': True
        },
        'type': {
            'name': '导出类型',
            'required': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    try:
        output_file, file_name = CodeGenApiService().export_code(req_dict)
        return generate_download_file(output_file, file_name)
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"未知错误：{e}"))


