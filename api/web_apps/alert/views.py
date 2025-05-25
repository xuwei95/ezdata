'''
告警模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.alert.services.alert_api_services import AlertApiService
alert_bp = Blueprint('alert', __name__)
    

@alert_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertApiService.get_obj_list(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertApiService.get_obj_all_list(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_detail():
    '''
    详情
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertApiService.get_obj_detail(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions([])
def alert_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertApiService.add_obj(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions([])
def alert_edit():
    '''
    编辑
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertApiService.edit_obj(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def alert_delete():
    '''
    删除
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertApiService.delete_obj(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def alert_deleteBatch():
    '''
    批量删除
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "ids": {
            "name": "id列表",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertApiService.delete_batch(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/importExcel', methods=['POST'])
@validate_user
@validate_permissions([])
def alert_importExcel():
    '''
    excel导入
    '''
    file = request.files.get('file', '')
    if file == '':
        res_data = gen_json_response(code=400, msg='请上传文件')
    else:
        res_data = AlertApiService.importExcel(file)
    return jsonify(res_data)
    

@alert_bp.route('/exportXls', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_exportXls():
    '''
    导出excel 
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "selections": {
            "name": "选择项",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    try:
        output_file = AlertApiService.exportXls(req_dict)
        return generate_download_file(output_file, 'output')
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"未知错误：{e}"))
