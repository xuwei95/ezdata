'''
数据字典模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
from web_apps.dictionary.services import DictService, DictItemService
dict_bp = Blueprint('dict', __name__)


@dict_bp.route('/list', methods=['GET'])
@validate_user
def dict_list():
    """
    字典列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DictService().get_obj_list(req_dict)
    return jsonify(res_data)


@dict_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['system:dict:add'])
def dict_add():
    """
    添加
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'dict_name': {
            'name': '字典名',
            'not_empty': True,
        },
        'dict_code': {
            'name': '字典值',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = DictService().add_obj(req_dict)
    return jsonify(res_data)


@dict_bp.route('/edit', methods=['POST'])
@validate_user
@validate_permissions(['system:dict:edit'])
def dict_edit():
    """
    更新字典
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'dict_name': {
            'name': '字典名',
            'not_empty': True,
        },
        'dict_code': {
            'name': '字典值',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = DictService().update_obj(req_dict)
    return jsonify(res_data)


@dict_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['system:dict:delete'])
def dict_delete():
    """
    删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DictService().delete_obj(req_dict)
    return jsonify(res_data)


@dict_bp.route('/deleteList', methods=['GET'])
@validate_user
def dict_delete_list():
    """
    字典回收站列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DictService().get_delete_list(req_dict)
    return jsonify(res_data)


@dict_bp.route('/deletePhysic', methods=['DELETE'])
@validate_user
@validate_permissions(['system:dict:recycle'])
def dict_delete_physic():
    """
    字典真实删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DictService().delete_physic(req_dict)
    return jsonify(res_data)


@dict_bp.route('/back', methods=['PUT'])
@validate_user
def dict_delete_back():
    """
    字典恢复
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DictService().delete_back(req_dict)
    return jsonify(res_data)


@dict_bp.route('/queryAllDictItems', methods=['GET'])
@validate_user
def get_dict_all_items():
    """
    所有系统字典列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    all_dict_items = DictService().get_obj_all_items(req_dict)
    return jsonify(gen_json_response(data=all_dict_items))


@dict_bp.route('/refreshCache', methods=['GET'])
@validate_user
@validate_permissions(['system:dict:refresh'])
def get_dict_reflesh_cache():
    """
    刷新系统字典列表缓存
    """
    req_dict = get_req_para(request)
    print(req_dict)
    all_dict_items = DictService().get_obj_all_items({'use_cache': False})
    return jsonify(gen_json_response(data=all_dict_items, extends={'success': True}))


@dict_bp.route('/getDictItems/<dict_code>', methods=['GET'])
@validate_user
def get_dict_items(dict_code):
    """
    查询字典项
    """
    req_dict = {'dict_code': dict_code}
    print(req_dict)
    res_data = DictItemService().get_dict_items(req_dict)
    return jsonify(res_data)


@dict_bp.route('/loadDictItem/<dict_code>', methods=['GET'])
@validate_user
def load_dict_items(dict_code):
    """
    加载字典项(带搜索)
    """
    req_dict = {'dict_code': dict_code}
    print(req_dict)
    req_dic = get_req_para(request)
    print(req_dic)
    req_dict['key'] = req_dic.get('key')
    res_data = DictItemService().get_dict_items(req_dict)
    return jsonify(res_data)


@dict_bp.route('/item/list', methods=['GET'])
@validate_user
def dict_item_list():
    """
    字典详情列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DictItemService().get_obj_list(req_dict)
    return jsonify(res_data)


@dict_bp.route('/item/add', methods=['POST'])
@validate_user
@validate_permissions(['system:dict:item:add'])
def dict_item_add():
    """
    添加
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'dict_id': {
            'name': '字典id',
            'not_empty': True,
        },
        'name': {
            'name': '名称',
            'not_empty': True,
        },
        'value': {
            'name': '值',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = DictItemService().add_obj(req_dict)
    return jsonify(res_data)


@dict_bp.route('/item/edit', methods=['POST'])
@validate_user
@validate_permissions(['system:dict:item:edit'])
def dict_item_edit():
    """
    更新字典项
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'name': {
            'name': '名称',
            'not_empty': True,
        },
        'value': {
            'name': '值',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = DictItemService().update_obj(req_dict)
    return jsonify(res_data)


@dict_bp.route('/item/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['system:dict:item:delete'])
def dict_item_delete():
    """
    删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = DictItemService().delete_obj(req_dict)
    return jsonify(res_data)



