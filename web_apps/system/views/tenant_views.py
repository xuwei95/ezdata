from flask import jsonify, request, Blueprint
from utils.auth import get_auth_token_info
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
from web_apps.system.services.tenant_service import TenantService
tenant_bp = Blueprint('sys_tenant', __name__)


@tenant_bp.route('/list', methods=['GET'])
def tenant_list():
    """
    租户列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = TenantService().get_obj_list(req_dict)
    return jsonify(res_data)


@tenant_bp.route('/queryList', methods=['GET'])
def tenant_all_list():
    """
    租户全量列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = TenantService().get_obj_all_list(req_dict)
    return jsonify(res_data)


@tenant_bp.route('/queryById', methods=['GET'])
def tenant_info():
    """
    租户信息
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = TenantService().get_obj_info(req_dict)
    return jsonify(res_data)


@tenant_bp.route('/getCurrentUserTenant', methods=['GET'])
@validate_user
def get_current_user_tenant_list():
    """
    查询登录用户租户列表
    """
    user_info = get_auth_token_info()
    req_dict = {'user_id': user_info['userId']}
    depart_list = TenantService().get_user_tenants(req_dict, res_type='result')
    res_data = {
        'list': depart_list
    }
    return jsonify(gen_json_response(res_data))


@tenant_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['system:tenant:add'])
def tenant_add():
    """
    添加
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = TenantService().add_obj(req_dict)
    return jsonify(res_data)


@tenant_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['system:tenant:edit'])
def tenant_edit():
    """
    更新
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = TenantService().update_obj(req_dict)
    return jsonify(res_data)


@tenant_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['system:tenant:delete'])
def tenant_delete():
    """
    删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = TenantService().delete_obj(req_dict)
    return jsonify(res_data)
