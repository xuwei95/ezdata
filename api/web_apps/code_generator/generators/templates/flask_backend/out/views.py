'''
测试模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
from web_apps.test.services.test_api_services import TestApiService
test_bp = Blueprint('test', __name__)
    

@test_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions(['test:query', 'aaa'])
def test_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TestApiService().get_obj_list(req_dict)
    return jsonify(res_data)
    

@test_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def test_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TestApiService().get_obj_all_list(req_dict)
    return jsonify(res_data)
    

@test_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def test_detail():
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
    res_data = TestApiService().get_obj_detail(req_dict)
    return jsonify(res_data)
    

@test_bp.route('/add', methods=['GET'])
@validate_user
@validate_permissions([])
def test_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TestApiService().add_obj(req_dict)
    return jsonify(res_data)
    

@test_bp.route('/edit', methods=['GET'])
@validate_user
@validate_permissions([])
def test_add():
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
    res_data = TestApiService().edit_obj(req_dict)
    return jsonify(res_data)
    

@test_bp.route('/delete', methods=['GET'])
@validate_user
@validate_permissions([])
def test_delete():
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
    res_data = TestApiService().delete_obj(req_dict)
    return jsonify(res_data)
    

@test_bp.route('/deleteBatch', methods=['GET'])
@validate_user
@validate_permissions([])
def test_deleteBatch():
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
    res_data = TestApiService().delete_batch(req_dict)
    return jsonify(res_data)
    

@test_bp.route('/importExcel', methods=['GET'])
@validate_user
@validate_permissions([])
def test_importExcel():
    '''
    excel导入
    '''
    file = request.files.get('file', '')
    if file == '':
        res_data = gen_json_response(code=400, msg='请上传文件')
    else:
        res_data = TestApiService().importExcel(file)
    return jsonify(res_data)
    

@test_bp.route('/exportXls', methods=['GET'])
@validate_user
@validate_permissions([])
def test_exportXls():
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
    res_data = TestApiService().exportXls(req_dict)
    return jsonify(res_data)
