'''
对话应用管理模块api
'''
import json
from flask import jsonify, request, Response
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.llm.services.app_services import ChatAppApiService
from web_apps.llm.db_models import ChatApp, ChatAppToken
from web_apps.llm.services.llm_services import generate_prompt, chat_generate, chat_run
from web_apps import db
from models import User

chat_app_bp = Blueprint('chat_app', __name__)


@chat_app_bp.route('/app/prompt/generate', methods=['POST'])
@validate_user
def prompt_generate():
    '''
    prompt generate
    '''
    args = request.args
    req_dict = args.to_dict()
    content = req_dict.get('prompt', '')
    return Response(generate_prompt(content), mimetype='text/event-stream')


@chat_app_bp.route('/app/debug', methods=['GET', 'POST'])
@validate_user
def debug_chat():
    '''
    app debug对话接口
    '''
    req_dict = get_req_para(request)
    chat_config = req_dict.get('app', {})
    message = req_dict.get('content', '')
    req_data = {
        'message': message,
        'chatConfig': chat_config
    }
    return Response(chat_generate(req_data), mimetype='text/event-stream')


@chat_app_bp.route('/api/chat', methods=['GET', 'POST'])
def api_chat():
    '''
    llm对话接口
    '''
    req_dict = get_req_para(request)
    api_key = req_dict.get('api_key', '')
    stream = req_dict.get('responseMode', 'streaming') == 'streaming'
    chat_token = db.session.query(ChatAppToken).filter(ChatAppToken.api_key == api_key).first()
    if chat_token is None:
        err = 'api_key错误'
        if stream:
            msg = {
                "conversationId": '',
                "data": {
                    "message": err
                },
                "event": "ERROR"
            }
            return Response(f"data:{json.dumps(msg, ensure_ascii=False)}\n\n", mimetype='text/event-stream')
        return gen_json_response(code=500, msg=err)
    chat_app = db.session.query(ChatApp).filter(ChatApp.id == chat_token.app_id).first()
    if chat_app is None:
        err = '未找到应用'
        if stream:
            msg = {
                "conversationId": '',
                "data": {
                    "message": err
                },
                "event": "ERROR"
            }
            return Response(f"data:{json.dumps(msg, ensure_ascii=False)}\n\n", mimetype='text/event-stream')
        return gen_json_response(code=500, msg=err)
    req_dict['chat_config'] = json.loads(chat_app.chat_config)
    user = db.session.query(User).filter(User.username == chat_token.create_by).first()
    if user:
        user_info = {'id': chat_token.create_by, 'user_name': chat_token.create_by}
    else:
        user_info = {}
    if stream:
        return Response(chat_generate(req_dict, user_info), mimetype='text/event-stream')
    else:
        return chat_run(req_dict)

@chat_app_bp.route('/release', methods=['POST'])
@validate_user
def release():
    '''
    app release
    '''
    req_dict = get_req_para(request)
    id = req_dict.get('id')
    release = req_dict.get('release')
    chat_app = db.session.query(ChatApp).filter(ChatApp.id == id).first()
    if chat_app is None:
        return gen_json_response(code=500, msg='未找到数据')
    chat_app.state = 1 if release else 0
    db.session.add(chat_app)
    db.session.commit()
    return gen_json_response(msg='ok', extends={'success': True})


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
    添加或编辑
    '''
    req_dict = get_req_para(request)
    if 'id' in req_dict:
        res_data = ChatAppApiService.edit_obj(req_dict)
    else:
        res_data = ChatAppApiService.add_obj(req_dict)
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
