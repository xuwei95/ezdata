'''
文档管理模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.rag.services.document_api_services import DocumentApiService
document_bp = Blueprint('document', __name__)


@document_bp.route('/train', methods=['POST'])
@validate_user
@validate_permissions([])
def document_train():
    '''
    训练知识库
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DocumentApiService.train_obj(req_dict)
    return jsonify(res_data)



@document_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def document_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DocumentApiService.get_obj_list(req_dict)
    return jsonify(res_data)
    

@document_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def document_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DocumentApiService.get_obj_all_list(req_dict)
    return jsonify(res_data)
    

@document_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def document_detail():
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
    res_data = DocumentApiService.get_obj_detail(req_dict)
    return jsonify(res_data)
    

@document_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions([])
def document_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DocumentApiService.add_obj(req_dict)
    return jsonify(res_data)
    

@document_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions([])
def document_edit():
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
    res_data = DocumentApiService.edit_obj(req_dict)
    return jsonify(res_data)
    

@document_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def document_delete():
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
    res_data = DocumentApiService.delete_obj(req_dict)
    return jsonify(res_data)
    

@document_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def document_deleteBatch():
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
    res_data = DocumentApiService.delete_batch(req_dict)
    return jsonify(res_data)
