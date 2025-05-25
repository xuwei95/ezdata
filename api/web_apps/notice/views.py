'''
通知公告模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
from web_apps.notice.services import NoticeService, NoticeSendService
notice_bp = Blueprint('notice', __name__)


@notice_bp.route('/list', methods=['GET'])
@validate_user
def notice_list():
    """
    列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = NoticeService().get_obj_list(req_dict)
    return jsonify(res_data)


@notice_bp.route('/listByUser', methods=['GET'])
@validate_user
def notice_list_by_user():
    """
    用户通知列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = NoticeService().get_obj_list_by_user(req_dict)
    return jsonify(res_data)


@notice_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['system:notice:add'])
def notice_add():
    """
    新增
    """
    req_dict = get_req_para(request)
    res_data = NoticeService().add_obj(req_dict)
    return jsonify(res_data)


@notice_bp.route('/send/edit', methods=['POST', 'PUT'])
@validate_user
def notice_send_edit():
    """
    修改
    """
    req_dict = get_req_para(request)
    print(6666, req_dict)
    res_data = NoticeSendService().update_obj(req_dict)
    return jsonify(res_data)


@notice_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
def notice_edit():
    """
    修改
    """
    req_dict = get_req_para(request)
    res_data = NoticeService().update_obj(req_dict)
    return jsonify(res_data)


@notice_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['system:notice:delete'])
def notice_delete():
    """
    删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = NoticeService().delete_obj(req_dict)
    return jsonify(res_data)