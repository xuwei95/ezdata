import json
import time
from flask import Blueprint, request, jsonify, Response
from utils.common_utils import gen_json_response, gen_uuid, parse_json
from utils.logger.logger import get_logger
from utils.web_utils import get_req_para, validate_params
from utils.auth import validate_user, set_insert_user, set_update_user, get_auth_token_info
from web_apps import db
from web_apps.llm.db_models import ChatHistory
from web_apps.llm.utils import get_llm
from web_apps.llm.services import data_chat, data_chat_generate
from web_apps.rag.services.rag_service import get_knowledge
logger = get_logger(p_name='system_log', f_name='llm', log_level='INFO')
llm_bp = Blueprint('llm', __name__)


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


@llm_bp.route('/chat', methods=['GET'])
@validate_user
def llm_chat():
    '''
    llm对话接口
    '''
    req_dict = get_req_para(request)
    message = req_dict.get('message', '')
    topic_id = req_dict.get('topicId', '')
    chat_config = parse_json(req_dict.get('chatConfig'), {})
    prompt = message
    # 查询知识库，若有相关知识，改写prompt
    rag_config = parse_json(chat_config.get('rag'), {})
    rag_enable = rag_config.get('enable', False)
    if rag_enable:
        rag_metadata = parse_json(chat_config.get('rag'), {'dataset_id': '1'})
        knowledge = get_knowledge(message, metadata=rag_metadata)
        if knowledge != '':
            prompt = f"结合知识库信息，回答用户的问题,若知识库中无相关信息，请尝试直接回答。\n知识库：{knowledge}\n用户问题：{message}\n回答："
    print(prompt)

    llm = get_llm(conversation_id=topic_id)

    def generate():
        for c in llm.stream(prompt):
            data = {'content': c.content, 'type': 'text'}
            t = f"id:{topic_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
            yield f"{t}\n\n"
        yield f"id:[DONE]\ndata:[DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')


@llm_bp.route('/data/chat/sync', methods=['POST'])
@validate_user
def llm_data_chat():
    '''
    数据对话同步接口
    '''
    try:
        req_dict = get_req_para(request)
        res_data = data_chat(req_dict)
        return jsonify(res_data)
    except Exception as e:
        logger.exception(e)
        res_data = {
            'text': str(e)[:200],
            'data': [],
            'html': '',
        }
        return gen_json_response(data=res_data)


@llm_bp.route('/data/chat', methods=['GET'])
@validate_user
def llm_data_chat_stream():
    '''
    数据对话流式接口
    '''
    req_dict = get_req_para(request)
    return Response(data_chat_generate(req_dict), mimetype='text/event-stream')
