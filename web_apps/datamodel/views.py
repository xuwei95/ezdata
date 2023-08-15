'''
数据模型管理模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.datamodel.services.datamodel_api_services import DataModelApiService
from web_apps.datamodel.services.datamodel_query_api_service import DataModelQueryApiService
datamodel_bp = Blueprint('datamodel', __name__)


@datamodel_bp.route('/query', methods=['POST'])
@validate_user
@validate_permissions([])
def datamodel_query():
    '''
    模型数据查询
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
    res_data = DataModelQueryApiService().query_obj_data(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/etl_preview', methods=['POST'])
@validate_user
@validate_permissions([])
def etl_preview():
    '''
    数据集成预览
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "task_params": {
            "name": "任务配置",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelQueryApiService().etl_preview(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/tree', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_tree():
    '''
    模型树查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().get_obj_tree(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().get_obj_list(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().get_obj_all_list(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_detail():
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
    res_data = DataModelApiService().get_obj_detail(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/getInfoById', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_info():
    '''
    模型查询信息，组成查询需要结构
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
    res_data = DataModelQueryApiService().get_obj_info(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/operate', methods=['POST'])
@validate_user
@validate_permissions(['datamodel:operate'])
def datamodel_operate():
    '''
    操作模型
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "模型id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelQueryApiService().operate_obj(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['datamodel:add'])
def datamodel_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "name": {
            "name": "名称",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().add_obj(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['datamodel:edit'])
def datamodel_edit():
    '''
    编辑
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        },
        "name": {
            "name": "名称",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().edit_obj(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['datamodel:delete'])
def datamodel_delete():
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
    res_data = DataModelApiService().delete_obj(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['datamodel:delete'])
def datamodel_deleteBatch():
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
    res_data = DataModelApiService().delete_batch(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/importExcel', methods=['POST'])
@validate_user
@validate_permissions([])
def datamodel_importExcel():
    '''
    excel导入
    '''
    file = request.files.get('file', '')
    if file == '':
        res_data = gen_json_response(code=400, msg='请上传文件')
    else:
        res_data = DataModelApiService().importExcel(file)
    return jsonify(res_data)


@datamodel_bp.route('/exportXls', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_exportXls():
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
        output_file = DataModelApiService().exportXls(req_dict)
        return generate_download_file(output_file, 'output')
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"未知错误：{e}"))

