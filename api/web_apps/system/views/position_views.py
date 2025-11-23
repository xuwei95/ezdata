from flask import jsonify, request, Blueprint
from utils.auth import get_auth_token_info
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
from web_apps.system.services.position_service import PositionService
position_bp = Blueprint('sys_position', __name__)


@position_bp.route('/list', methods=['GET'])
def position_list():
    """
    职务列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = PositionService().get_obj_list(req_dict)
    return jsonify(res_data)


@position_bp.route('/queryById', methods=['GET'])
def position_info():
    """
    职务信息
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = PositionService().get_obj_info(req_dict)
    return jsonify(res_data)


@position_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['system:position:add'])
def position_add():
    """
    添加
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = PositionService().add_obj(req_dict)
    return jsonify(res_data)


@position_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['system:position:edit'])
def position_edit():
    """
    更新
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = PositionService().update_obj(req_dict)
    return jsonify(res_data)


@position_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['system:position:delete'])
def position_delete():
    """
    删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = PositionService().delete_obj(req_dict)
    return jsonify(res_data)
