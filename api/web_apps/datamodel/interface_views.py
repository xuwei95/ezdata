'''
数据接口模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.datamodel.services.data_interface_api_services import DataInterfaceApiService
data_interface_bp = Blueprint('data_interface', __name__)


@data_interface_bp.route('/query', methods=['GET', 'POST'])
def data_interface_query():
    '''
    接口查询
    '''
    args = request.args
    api_key = args.to_dict().get('api_key', '')
    req_dict = get_req_para(request)
    if 'api_key' not in req_dict:
        req_dict['api_key'] = api_key
    verify_dict = {
        "api_key": {
            "name": "api_key",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataInterfaceApiService().query(req_dict, request.method)
    return jsonify(res_data)


@data_interface_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def data_interface_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataInterfaceApiService().get_obj_list(req_dict)
    return jsonify(res_data)
    

@data_interface_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def data_interface_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataInterfaceApiService().get_obj_all_list(req_dict)
    return jsonify(res_data)
    

@data_interface_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def data_interface_detail():
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
    res_data = DataInterfaceApiService().get_obj_detail(req_dict)
    return jsonify(res_data)
    

@data_interface_bp.route('/apply', methods=['POST'])
@validate_user
@validate_permissions([])
def data_interface_apply():
    '''
    申请接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "datamodel_id": {
            "name": "所属数据模型",
            "required": True
        },
        "name": {
            "name": "接口名称",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataInterfaceApiService().apply_obj(req_dict)
    return jsonify(res_data)
    

@data_interface_bp.route('/review', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['data_interface:verify'])
def data_interface_review():
    '''
    审核
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        },
        "datamodel_id": {
            "name": "所属数据模型",
            "required": True
        },
        "name": {
            "name": "接口名称",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataInterfaceApiService().review_obj(req_dict)
    return jsonify(res_data)


@data_interface_bp.route('/status', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['data_interface:status'])
def data_interface_status():
    '''
    编辑状态
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
    res_data = DataInterfaceApiService().edit_obj_status(req_dict)
    return jsonify(res_data)


@data_interface_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['data_interface:delete'])
def data_interface_delete():
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
    res_data = DataInterfaceApiService().delete_obj(req_dict)
    return jsonify(res_data)
    

@data_interface_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['data_interface:delete'])
def data_interface_deleteBatch():
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
    res_data = DataInterfaceApiService().delete_batch(req_dict)
    return jsonify(res_data)
    

@data_interface_bp.route('/importExcel', methods=['POST'])
@validate_user
@validate_permissions([])
def data_interface_importExcel():
    '''
    excel导入
    '''
    file = request.files.get('file', '')
    if file == '':
        res_data = gen_json_response(code=400, msg='请上传文件')
    else:
        res_data = DataInterfaceApiService().importExcel(file)
    return jsonify(res_data)
    

@data_interface_bp.route('/exportXls', methods=['GET'])
@validate_user
@validate_permissions([])
def data_interface_exportXls():
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
        output_file = DataInterfaceApiService().exportXls(req_dict)
        return generate_download_file(output_file, 'output')
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"未知错误：{e}"))