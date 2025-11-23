from flask import jsonify, request, Blueprint
from utils.auth import get_auth_token_info
from utils.auth import validate_user, validate_permissions
from web_apps.system.services.permission_service import PerMissionService
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
permission_bp = Blueprint('sys_permission', __name__)


@permission_bp.route('/list', methods=['GET'])
@validate_user
def permission_list():
    """
    权限列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = PerMissionService().get_obj_list(req_dict)
    return jsonify(res_data)


@permission_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['sys:menu:add'])
def permission_add():
    """
    添加
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = PerMissionService().add_obj(req_dict)
    return jsonify(res_data)


@permission_bp.route('/edit', methods=['POST'])
@validate_user
@validate_permissions(['sys:menu:edit'])
def permission_edit():
    """
    更新
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = PerMissionService().update_obj(req_dict)
    return jsonify(res_data)


@permission_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['sys:menu:delete'])
def permission_delete():
    """
    删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = PerMissionService().delete_obj(req_dict)
    return jsonify(res_data)


@permission_bp.route('/getPermCode', methods=['GET'])
@validate_user
def get_prem_code():
    """
    获取系统权限
    1、查询用户拥有的按钮/表单访问权限
    2、所有权限
    3、系统安全模式
    """
    req_dict = get_req_para(request)
    user_info = get_auth_token_info()
    all_auth = PerMissionService().get_all_auth(req_dict)
    if user_info['username'] == 'admin':
        user_auth_list = all_auth
    else:
        user_auth_list = PerMissionService().get_user_auth(user_info)
    codeList = [i['action'] for i in user_auth_list]
    info = {
        "allAuth": all_auth,
        "auth": user_auth_list,
        "codeList": codeList
    }
    res_data = gen_json_response(data=info)
    return jsonify(res_data)


@permission_bp.route('/getUserPermissionByToken', methods=['GET'])
@validate_user
def get_user_prem_by_token():
    """
    获取用户菜单
    """
    req_dict = get_req_para(request)
    user_info = get_auth_token_info()
    all_auth = PerMissionService().get_all_auth(req_dict)
    user_auth_list = PerMissionService().get_user_auth(user_info)
    if user_info['username'] == 'admin':
        user_menus = PerMissionService().get_all_menus(req_dict)
    else:
        user_menus = PerMissionService().get_user_menus(user_info)
    res_data = {
        "allAuth": all_auth,
        "auth": user_auth_list,
        "menu": user_menus,
        "sysSafeMode": False
    }
    return jsonify(gen_json_response(data=res_data))


@permission_bp.route('/queryRolePermission', methods=['GET'])
@validate_user
def get_role_permission():
    """
    获取角色权限
    """
    req_dict = get_req_para(request)
    res_data = PerMissionService().get_role_permissions(req_dict)
    return jsonify(res_data)


@permission_bp.route('/saveRolePermission', methods=['POST'])
@validate_user
@validate_permissions(['sys:role:auth'])
def save_role_permission():
    """
    设置角色权限
    """
    req_dict = get_req_para(request)
    res_data = PerMissionService().save_role_permissions(req_dict)
    return jsonify(res_data)


@permission_bp.route('/queryDepartPermission', methods=['GET'])
@validate_user
def get_depart_permission():
    """
    获取部门权限
    """
    req_dict = get_req_para(request)
    res_data = PerMissionService().get_depart_permissions(req_dict)
    return jsonify(res_data)


@permission_bp.route('/saveDepartPermission', methods=['POST'])
@validate_user
@validate_permissions(['sys:depart:save_role'])
def save_depart_permission():
    """
    设置部门权限
    """
    req_dict = get_req_para(request)
    res_data = PerMissionService().save_depart_permissions(req_dict)
    return jsonify(res_data)
