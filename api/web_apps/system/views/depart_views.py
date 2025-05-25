from flask import jsonify, request, Blueprint
from utils.auth import get_auth_token_info
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
from web_apps.system.services.depart_service import DepartService
from web_apps.system.services.permission_service import PerMissionService
depart_bp = Blueprint('sys_depart', __name__)


@depart_bp.route('/queryDepartTreeSync', methods=['GET'])
def depart_tree_sync():
    """
    查询部门树
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DepartService().get_obj_list(req_dict)
    return jsonify(res_data)


@depart_bp.route('/queryMyDeptTreeList', methods=['GET'])
def query_my_depart_tree_list():
    """
    查询个人部门树
    """
    req_dict = get_req_para(request)
    print(req_dict)
    user_info = get_auth_token_info()
    res_data = DepartService().query_user_depart_tree(user_info)
    return jsonify(res_data)


@depart_bp.route('/queryTreeList', methods=['GET'])
def query_depart_tree_list():
    """
    查询部门树
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DepartService().query_depart_tree(req_dict)
    return jsonify(res_data)


@depart_bp.route('/queryIdTree', methods=['GET'])
def query_depart_id_tree_list():
    """
    查询部门id树
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DepartService().query_depart_id_tree(req_dict)
    return jsonify(res_data)


@depart_bp.route('/queryall', methods=['GET'])
def query_depart_all_list():
    """
    查询所有部门列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DepartService().query_depart_all_list(req_dict)
    return jsonify(res_data)


@depart_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['sys:depart:add'])
def depart_add():
    """
    添加
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DepartService().add_obj(req_dict)
    return jsonify(res_data)


@depart_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['sys:depart:edit'])
def depart_edit():
    """
    更新
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DepartService().update_obj(req_dict)
    return jsonify(res_data)


@depart_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['sys:depart:delete'])
def depart_delete():
    """
    删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DepartService().delete_obj(req_dict)
    return jsonify(res_data)