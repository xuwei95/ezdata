'''
对话应用管理模块api
'''
from flask import jsonify, request, Response
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.llm.services.app_services import ChatAppApiService

chat_app_bp = Blueprint('chat_app', __name__)


@chat_app_bp.route('/chat', methods=['GET'])
@validate_user
def llm_chat():
    '''
    llm对话接口
    '''
    req_dict = get_req_para(request)
    stream = req_dict.get('stream', False)
    if stream:
        return Response(ChatAppApiService.chat(req_dict), mimetype='text/event-stream')
    else:
        return ChatAppApiService.chat(req_dict)


@chat_app_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def chat_app_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ChatAppApiService.get_obj_list(req_dict)
    return jsonify(res_data)


@chat_app_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def chat_app_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ChatAppApiService.get_obj_all_list(req_dict)
    return jsonify(res_data)


@chat_app_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def chat_app_detail():
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
    res_data = ChatAppApiService.get_obj_detail(req_dict)
    return jsonify(res_data)


@chat_app_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions([])
def chat_app_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ChatAppApiService.add_obj(req_dict)
    return jsonify(res_data)


@chat_app_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions([])
def chat_app_edit():
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
    res_data = ChatAppApiService.edit_obj(req_dict)
    return jsonify(res_data)


@chat_app_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def chat_app_delete():
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
    res_data = ChatAppApiService.delete_obj(req_dict)
    return jsonify(res_data)


@chat_app_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def chat_app_deleteBatch():
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
    res_data = ChatAppApiService.delete_batch(req_dict)
    return jsonify(res_data)
