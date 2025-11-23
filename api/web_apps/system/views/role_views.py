from flask import jsonify, request, Blueprint
from utils.auth import get_auth_token_info
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
from web_apps.system.services.role_service import RoleService
from web_apps.system.services.permission_service import PerMissionService
role_bp = Blueprint('sys_role', __name__)


@role_bp.route('/list', methods=['GET'])
def role_list():
    """
    角色列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = RoleService().get_obj_list(req_dict)
    return jsonify(res_data)


@role_bp.route('/queryall', methods=['GET'])
def role_all_list():
    """
    所有角色列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = RoleService().get_obj_all_list(req_dict)
    return jsonify(res_data)


@role_bp.route('/queryTreeList', methods=['GET'])
def role_query_tree_list():
    """
    角色权限树
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = PerMissionService().get_role_tree_list(req_dict)
    return jsonify(res_data)


@role_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['sys:role:add'])
def role_add():
    """
    添加
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = RoleService().add_obj(req_dict)
    return jsonify(res_data)


@role_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['sys:role:edit'])
def role_edit():
    """
    更新字典
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = RoleService().update_obj(req_dict)
    return jsonify(res_data)


@role_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['sys:role:delete'])
def role_delete():
    """
    删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = RoleService().delete_obj(req_dict)
    return jsonify(res_data)
