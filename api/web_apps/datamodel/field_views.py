'''
数据模型管理模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.datamodel.services.datamodel_field_api_services import DataModelFieldApiService

datamodel_field_bp = Blueprint('datamodel_field', __name__)


@datamodel_field_bp.route('/sync_fields', methods=['POST'])
@validate_user
@validate_permissions([])
def datamodel_sync_fields():
    '''
    同步模型字段
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelFieldApiService().sync_fields(req_dict)
    return jsonify(res_data)


@datamodel_field_bp.route('/sync', methods=['POST'])
@validate_user
@validate_permissions([])
def datamodel_field_sync():
    '''
    同步字段到模型
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelFieldApiService().sync_field(req_dict)
    return jsonify(res_data)


@datamodel_field_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_field_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelFieldApiService().get_obj_list(req_dict)
    return jsonify(res_data)


@datamodel_field_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_field_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelFieldApiService().get_obj_all_list(req_dict)
    return jsonify(res_data)


@datamodel_field_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_field_detail():
    '''
    详情
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelFieldApiService().get_obj_detail(req_dict)
    return jsonify(res_data)


@datamodel_field_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions([])
def datamodel_field_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "datamodel_id": {
            "name": "数据模型id",
            "required": True
        },
        "field_name": {
            "name": "字段名",
            "required": True
        },
        "field_value": {
            "name": "字段值",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelFieldApiService().add_obj(req_dict)
    return jsonify(res_data)


@datamodel_field_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions([])
def datamodel_field_edit():
    '''
    编辑
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        },
        "datamodel_id": {
            "name": "数据模型id",
            "required": True
        },
        "field_name": {
            "name": "字段名",
            "required": True
        },
        "field_value": {
            "name": "字段值",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelFieldApiService().edit_obj(req_dict)
    return jsonify(res_data)


@datamodel_field_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def datamodel_field_delete():
    '''
    删除
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelFieldApiService().delete_obj(req_dict)
    return jsonify(res_data)


@datamodel_field_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def datamodel_field_deleteBatch():
    '''
    批量删除
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "ids": {
            "name": "id列表",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelFieldApiService().delete_batch(req_dict)
    return jsonify(res_data)


@datamodel_field_bp.route('/importExcel', methods=['POST'])
@validate_user
@validate_permissions([])
def datamodel_field_importExcel():
    '''
    excel导入
    '''
    file = request.files.get('file', '')
    if file == '':
        res_data = gen_json_response(code=400, msg='请上传文件')
    else:
        res_data = DataModelFieldApiService().importExcel(file)
    return jsonify(res_data)


@datamodel_field_bp.route('/exportXls', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_field_exportXls():
    '''
    导出excel
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "selections": {
            "name": "选择项",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    try:
        output_file = DataModelFieldApiService().exportXls(req_dict)
        return generate_download_file(output_file, 'output')
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"未知错误：{e}"))
