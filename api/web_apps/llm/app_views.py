'''
对话应用管理模块api
'''
from flask import jsonify, request, Response
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.llm.services.app_services import ChatAppApiService
from web_apps.llm.db_models import ChatApp, ChatAppToken
from web_apps import db

chat_app_bp = Blueprint('chat_app', __name__)


@chat_app_bp.route('/app/chat', methods=['GET', 'POST'])
@validate_user
def app_chat():
    '''
    app对话接口
    '''
    req_dict = get_req_para(request)
    app_id = req_dict.get('app_id', '')
    message = req_dict.get('message', '')
    chat_app = db.session.query(ChatApp).filter(ChatApp.id == app_id).first()
    if chat_app is None:
        err = '未找到应用'
        return f"[ERR]\ndata:[{err}]\n\n"
    return Response(ChatAppApiService.chat(chat_app, message, True), mimetype='text/event-stream')


@chat_app_bp.route('/api/chat', methods=['GET', 'POST'])
def api_chat():
    '''
    llm对话接口
    '''
    req_dict = get_req_para(request)
    api_key = req_dict.get('api_key', '')
    message = req_dict.get('message', '')
    stream = req_dict.get('stream', '1') == '1'
    chat_token = db.session.query(ChatAppToken).filter(ChatAppToken.api_key == api_key).first()
    if chat_token is None:
        err = 'api_key错误'
        if stream:
            return f"[ERR]\ndata:[{err}]\n\n"
        return gen_json_response(code=500, msg=err)
    chat_app = db.session.query(ChatApp).filter(ChatApp.id == chat_token.app_id).first()
    if chat_app is None:
        err = '未找到应用'
        if stream:
            return f"[ERR]\ndata:[{err}]\n\n"
        return gen_json_response(code=500, msg=err)
    if stream:
        return Response(ChatAppApiService.chat(chat_app, message, True), mimetype='text/event-stream')
    else:
        return ChatAppApiService.chat(chat_app, message, False)


@chat_app_bp.route('/token/list', methods=['GET'])
@validate_user
@validate_permissions([])
def chat_app_token_list():
    '''
    api列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ChatAppApiService.api_key_list(req_dict)
    return jsonify(res_data)


@chat_app_bp.route('/token/apply', methods=['POST'])
@validate_user
@validate_permissions([])
def chat_app_token_apply():
    '''
    api申请
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ChatAppApiService.apply_token(req_dict)
    return jsonify(res_data)


@chat_app_bp.route('/token/status', methods=['POST'])
@validate_user
@validate_permissions([])
def chat_app_token_status():
    '''
    api状态修改
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ChatAppApiService.api_key_status(req_dict)
    return jsonify(res_data)


@chat_app_bp.route('/token/delete', methods=['POST'])
@validate_user
@validate_permissions([])
def chat_app_token_delete():
    '''
    api删除
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ChatAppApiService.api_key_delete(req_dict)
    return jsonify(res_data)


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
