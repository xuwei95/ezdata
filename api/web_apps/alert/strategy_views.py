'''
告警策略模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.alert.services.strategy_api_services import AlertStrategyApiService
alert_strategy_bp = Blueprint('alert_strategy', __name__)
    

@alert_strategy_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_strategy_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertStrategyApiService.get_obj_list(req_dict)
    return jsonify(res_data)
    

@alert_strategy_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_strategy_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertStrategyApiService.get_obj_all_list(req_dict)
    return jsonify(res_data)
    

@alert_strategy_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_strategy_detail():
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
    res_data = AlertStrategyApiService.get_obj_detail(req_dict)
    return jsonify(res_data)
    

@alert_strategy_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions([])
def alert_strategy_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertStrategyApiService.add_obj(req_dict)
    return jsonify(res_data)
    

@alert_strategy_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions([])
def alert_strategy_edit():
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
    res_data = AlertStrategyApiService.edit_obj(req_dict)
    return jsonify(res_data)
    

@alert_strategy_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def alert_strategy_delete():
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
    res_data = AlertStrategyApiService.delete_obj(req_dict)
    return jsonify(res_data)
    

@alert_strategy_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def alert_strategy_deleteBatch():
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
    res_data = AlertStrategyApiService.delete_batch(req_dict)
    return jsonify(res_data)
    

@alert_strategy_bp.route('/importExcel', methods=['POST'])
@validate_user
@validate_permissions([])
def alert_strategy_importExcel():
    '''
    excel导入
    '''
    file = request.files.get('file', '')
    if file == '':
        res_data = gen_json_response(code=400, msg='请上传文件')
    else:
        res_data = AlertStrategyApiService.importExcel(file)
    return jsonify(res_data)
    

@alert_strategy_bp.route('/exportXls', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_strategy_exportXls():
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
        output_file = AlertStrategyApiService.exportXls(req_dict)
        return generate_download_file(output_file, 'output')
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"未知错误：{e}"))
