import json
import time
from flask import Blueprint, request, jsonify, Response
from utils.common_utils import gen_json_response, gen_uuid
from utils.logger.logger import get_logger
from utils.web_utils import get_req_para
from utils.auth import validate_user, validate_permissions, set_insert_user, set_update_user, get_auth_token_info
from web_apps import db
from web_apps.llm.db_models import ChatHistory
from web_apps.llm.utils import get_llm
from web_apps.llm.services import data_chat
logger = get_logger(p_name='system_log', f_name='llm', log_level='INFO')
llm_bp = Blueprint('llm', __name__)


@llm_bp.route('/data_chat', methods=['POST'])
@validate_user
def llm_data_chat():
    try:
        req_dict = get_req_para(request)
        print(req_dict)
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
    else:
        history = json.loads(history_obj.content)
    res_data = {
        "success": True,
        "msg": "",
        "code": 200,
        "data": history,
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
        "msg": "",
        "code": 200,
    }
    return jsonify(res_data)


@llm_bp.route('/chat/send', methods=['GET'])
@validate_user
def llm_chat_send():
    req_dict = get_req_para(request)
    message = req_dict.get('message', '')
    topic_id = req_dict.get('topicId', gen_uuid())

    # 当请求类型为GET时，开始SSE流
    def generate():
        llm = get_llm()
        result = llm(message)
        data = {'content': result, 'type': 'text'}
        t = f"id:{topic_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
        yield f"{t}\n\n"
        # data = {'content': '\n最终结果如下：', 'type': 'text'}
        # t = f"id:{topic_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
        # yield f"{t}\n\n"
        # data = {'content': [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], 'type': 'data'}
        # yield f"id:{topic_id}\ndata:{json.dumps(data, ensure_ascii=False)}\n\n"
        yield f"id:[DONE]\ndata:[DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')
