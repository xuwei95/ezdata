from flask import jsonify, request, Blueprint
from utils.auth import get_auth_token_info
from utils.auth import validate_user, validate_permissions
from web_apps.system.services.user_service import UserService
from web_apps.dictionary.services import DictService
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
user_bp = Blueprint('sys_user', __name__)


@user_bp.route('/checkOnlyUser', methods=['GET'])
@validate_user
def check_only_user():
    """
    检测是否重复
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = UserService().check_only_user(req_dict)
    return jsonify(res_data)


@user_bp.route('/departUserList', methods=['GET'])
@validate_user
def get_depart_user_list():
    """
    查询部门用户列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = UserService().get_depart_users(req_dict)
    return jsonify(res_data)


@user_bp.route('/userDepartList', methods=['GET'])
@validate_user
def get_user_depart_list():
    """
    查询用户部门列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'user_id': {
            'name': '用户id',
            'not_empty': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = UserService().get_user_departs(req_dict)
    return jsonify(res_data)


@user_bp.route('/editSysDepartWithUser', methods=['POST'])
@validate_user
@validate_permissions(['user-depart:user'])
def edit_user_depart():
    """
    修改部门用户
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'depart_id': {
            'name': '部门id',
            'not_empty': True
        },
        'user_id_list': {
            'name': '用户列表',
            'not_empty': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = UserService().edit_user_departs(req_dict)
    return jsonify(res_data)


@user_bp.route('/deleteUserInDepartBatch', methods=['DELETE'])
@validate_user
@validate_permissions(['user-depart:user'])
def delete_user_departs():
    """
    删除用户关联部门
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'depart_id': {
            'name': '部门id',
            'not_empty': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = UserService().delete_user_departs(req_dict)
    return jsonify(res_data)


@user_bp.route('/getCurrentUserDeparts', methods=['GET'])
@validate_user
def get_current_user_depart_list():
    """
    查询登录用户部门列表
    """
    user_info = get_auth_token_info()
    req_dict = {'user_id': user_info['userId']}
    depart_list = UserService().get_user_departs(req_dict, res_type='result')
    res_data = {
        'org_code': user_info['org_code'],
        'list': depart_list
    }
    return jsonify(gen_json_response(res_data))


@user_bp.route('/selectDepart', methods=['PUT'])
@validate_user
def user_select_depart():
    """
    切换用户登录部门
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'username': {
            'name': '用户名',
            'not_empty': True
        },
        'org_code': {
            'name': '部门',
            'not_empty': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = UserService().select_depart(req_dict)
    return jsonify(res_data)


@user_bp.route('/userRoleList', methods=['GET'])
@validate_user
def get_role_user_list():
    """
    查询角色用户列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'role_id': {
            'name': '角色id',
            'not_empty': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = UserService().get_role_user_list(req_dict)
    return jsonify(res_data)


@user_bp.route('/queryUserRole', methods=['GET'])
@validate_user
def get_user_roles():
    """
    查询用户角色列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = UserService().get_user_roles(req_dict)
    return jsonify(res_data)


@user_bp.route('/addSysUserRole', methods=['POST'])
@validate_user
@validate_permissions(['sys:role:user'])
def add_user_roles():
    """
    添加用户关联角色
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'role_id': {
            'name': '角色id',
            'not_empty': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = UserService().add_user_roles(req_dict)
    return jsonify(res_data)


@user_bp.route('/deleteUserRole', methods=['DELETE'])
@validate_user
@validate_permissions(['sys:role:user'])
def delete_user_roles():
    """
    删除用户关联角色
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'role_id': {
            'name': '角色id',
            'not_empty': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = UserService().delete_user_roles(req_dict)
    return jsonify(res_data)


@user_bp.route('/changePassword', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['user:password'])
def change_user_password():
    """
    管理员修改密码
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = UserService().change_password(req_dict)
    return jsonify(res_data)


@user_bp.route('/updatePassword', methods=['POST', 'PUT'])
@validate_user
def update_user_password():
    """
    用户修改密码
    """
    req_dict = get_req_para(request)
    print(req_dict)
    username = req_dict.get('username')
    user_info = get_auth_token_info()
    if user_info['username'] != username:
        res_data = gen_json_response(msg='非本人操作')
    else:
        res_data = UserService().update_password(req_dict)
    return jsonify(res_data)


@user_bp.route('/edit_self', methods=['POST', 'PUT'])
@validate_user
def user_edit_self():
    """
    用户修改个人信息
    """
    req_dict = get_req_para(request)
    print(req_dict)
    user_info = get_auth_token_info()
    username = user_info['username']
    res_data = UserService().edit_self(req_dict, username)
    return jsonify(res_data)


@user_bp.route('/frozenBatch', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['user:frozen'])
def user_frozenBatch():
    """
    批量冻结用户
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'ids': {
            'name': '用户id列表',
            'not_empty': True
        },
        'status': {
            'name': '状态',
            'not_empty': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = UserService().frozenBatch(req_dict)
    return jsonify(res_data)


@user_bp.route('/register', methods=['POST'])
def user_register():
    """
    注册
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'username': {
            'name': '用戶名',
            'not_empty': True,
            'length': [4, 20]
        },
        'password': {
            'name': '密码',
            'not_empty': True,
            'length': [4, 20]
        },
        'phone': {
            'name': '手机号',
            'length': [11, 12]
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = UserService().register(req_dict)
    return jsonify(res_data)


@user_bp.route('/login', methods=['POST'])
def user_login():
    """
    登录
    """
    req_dict = get_req_para(request)
    res_data = UserService().login(req_dict)
    return jsonify(res_data)


@user_bp.route('/token_login', methods=['POST'])
def user_login_by_token():
    """
    token登录
    """
    req_dict = get_req_para(request)
    res_data = UserService().login_by_token(req_dict)
    return jsonify(res_data)


@user_bp.route('/info', methods=['GET'])
@validate_user
def user_info():
    """
    用户信息
    """
    user_info = get_auth_token_info()
    info = {
        'userInfo': user_info,
        'sysAllDictItems': DictService().get_obj_all_items({})
    }
    res_data = gen_json_response(data=info)
    return jsonify(res_data)


@user_bp.route('/list', methods=['GET'])
@validate_user
def user_list():
    """
    用户列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = UserService().get_obj_list(req_dict)
    return jsonify(res_data)


@user_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['user:add'])
def user_add():
    """
    添加
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = UserService().add_obj(req_dict)
    return jsonify(res_data)


@user_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['user:edit'])
def user_edit():
    """
    更新
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = UserService().update_obj(req_dict)
    return jsonify(res_data)


@user_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['user:delete'])
def user_delete():
    """
    删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = UserService().delete_obj(req_dict)
    return jsonify(res_data)