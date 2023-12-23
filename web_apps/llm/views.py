from flask import Blueprint, request, jsonify
from utils.common_utils import gen_json_response
from utils.logger.logger import get_logger
from utils.web_utils import get_req_para
from utils.auth import validate_user, validate_permissions
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


