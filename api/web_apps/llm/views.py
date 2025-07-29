import json
import time
from flask import Blueprint, request, jsonify, Response
from utils.common_utils import gen_json_response, gen_uuid, format_date
from utils.logger.logger import get_logger
from utils.web_utils import get_req_para
from utils.auth import validate_user, set_insert_user, set_update_user, get_auth_token_info
from web_apps import db
from web_apps.llm.db_models import ChatHistory, Conversation, ChatApp
from web_apps.llm.services.llm_services_v2 import chat_generate, data_chat_generate, get_tool_list
from web_apps.llm.services.conversation_service import get_conversations, get_messages
from web_apps.llm.services.app_services import ChatAppApiService
logger = get_logger(p_name='system_log', f_name='llm', log_level='INFO')
llm_bp = Blueprint('llm', __name__)


@llm_bp.route('/tool/list', methods=['GET'])
@validate_user
def tool_list():
    res_data = get_tool_list()
    return jsonify(res_data)


@llm_bp.route('/chat/history/get', methods=['GET'])
@validate_user
def get_llm_chat_history():
    user_info = get_auth_token_info()
    user_id = user_info['id']
    history_obj = db.session.query(ChatHistory).filter(ChatHistory.user_id == user_id).first()
    if history_obj is None:
        history = {
            'active': 1002,
            'usingContext': True,
            'history': [{'uuid': 1002, 'title': '新建聊天', 'isEdit': False}],
            'chat': [{'uuid': 1002, 'data': []}],
        }
        history = json.dumps(history, ensure_ascii=False)
    else:
        history = history_obj.content
    res_data = {
        "success": True,
        "msg": "",
        "code": 200,
        "data": {'content': history},
        "timestamp": int(time.time() * 1000)
    }
    return jsonify(res_data)


@llm_bp.route('/chat/history/save', methods=['POST'])
@validate_user
def save_llm_chat_history():
    req_dict = get_req_para(request)
    content = req_dict.get('content')
    if content:
        user_info = get_auth_token_info()
        user_id = user_info['id']
        user_name = user_info.get('username')
        history_obj = db.session.query(ChatHistory).filter(ChatHistory.user_id == user_id).first()
        if history_obj is None:
            history_obj = ChatHistory(
                id=gen_uuid(),
                user_id=user_id,
                user_name=user_name,
                content=content
            )
            set_insert_user(history_obj)
        else:
            history_obj.content = content
            set_update_user(history_obj)
        db.session.add(history_obj)
        db.session.commit()
        db.session.flush()
    res_data = {
        "success": True,
        "msg": "保存成功",
        "code": 200,
    }
    return jsonify(res_data)


@llm_bp.route('/chat/conversations', methods=['GET'])
@validate_user
def get_chat_conversations():
    user_info = get_auth_token_info()
    user_id = user_info['id']
    req_dict = get_req_para(request)
    app_id = req_dict.get('appId', '')
    conversations = get_conversations({'user_id': user_id, 'app_id': app_id})
    res_data = {
        "success": True,
        "msg": "",
        "code": 200,
        "data": conversations,
        "timestamp": int(time.time() * 1000)
    }
    return jsonify(res_data)

@llm_bp.route('/chat/conversation/update/title', methods=['PUT'])
@validate_user
def update_conversation():
    req_dict = get_req_para(request)
    _id = req_dict.get('id', '')
    title = req_dict.get('title', '')
    if _id and title:
        conversation = db.session.query(Conversation).filter(Conversation.id == _id).first()
        if conversation:
            conversation.description = title
            db.session.add(conversation)
            db.session.commit()
    res_data = {
        "success": True,
        "msg": "修改成功",
        "code": 200
    }
    return jsonify(res_data)

@llm_bp.route('/chat/conversation/<id>', methods=['DELETE'])
@validate_user
def delete_conversation(id):
    if id:
        conversation = db.session.query(Conversation).filter(Conversation.id == id).first()
        if conversation:
            db.session.delete(conversation)
            db.session.commit()
    res_data = {
        "success": True,
        "msg": "删除成功",
        "code": 200
    }
    return jsonify(res_data)

@llm_bp.route('/chat/messages', methods=['GET'])
@validate_user
def get_chat_messages():
    req_dict = get_req_para(request)
    conversation_id = req_dict.get('conversationId', '')
    messages, total = get_messages(conversation_id=conversation_id, size=50)
    results = []
    for msg in messages:
        dic = {
             "conversationId": conversation_id,
              "role": "user",
              "content": msg.get('question', ''),
              "images": [],
              "datetime": format_date(msg.get('created_at'))
        }
        results.append(dic)
        dic = {
             "conversationId": conversation_id,
              "role": "ai",
              "content": msg.get('answer', ''),
              "images": [],
              "datetime": format_date(msg.get('created_at'))
        }
        results.append(dic)
    res_data = {
        "success": True,
        "msg": "ok",
        "code": 200,
        "data": results
    }
    return jsonify(res_data)

@llm_bp.route('/chat', methods=['GET', 'POST'])
@validate_user
def llm_chat():
    '''
    llm对话接口
    '''
    req_dict = get_req_para(request)
    req_dict['message'] = req_dict.get('message', req_dict.get('content', ''))
    user_info = get_auth_token_info()
    if req_dict.get('appId'):
        app_id = req_dict.get('appId')
        chat_app = db.session.query(ChatApp).filter(ChatApp.id == app_id).first()
        if chat_app is None:
            err = '未找到应用'
            msg = {
                    "conversationId": '',
                    "data": {
                        "message": err
                    },
                    "event": "ERROR"
                }
            return Response(f"data:{json.dumps(msg, ensure_ascii=False)}\n\n", mimetype='text/event-stream')
        req_dict['chat_config'] = json.loads(chat_app.chat_config)
    return Response(chat_generate(req_dict, user_info), mimetype='text/event-stream')


@llm_bp.route('/data/chat', methods=['GET', 'POST'])
@validate_user
def llm_data_chat_stream():
    '''
    数据对话流式接口
    '''
    req_dict = get_req_para(request)
    return Response(data_chat_generate(req_dict), mimetype='text/event-stream')
