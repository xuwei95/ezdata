'''
数据源管理模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from utils.validate_utils import validate_json
from web_apps.datasource.services.datasource_api_services import DataSourceApiService
datasource_bp = Blueprint('datasource', __name__)
    

@datasource_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def datasource_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataSourceApiService().get_obj_list(req_dict)
    return jsonify(res_data)
    

@datasource_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def datasource_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataSourceApiService().get_obj_all_list(req_dict)
    return jsonify(res_data)
    

@datasource_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def datasource_detail():
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
    res_data = DataSourceApiService().get_obj_detail(req_dict)
    return jsonify(res_data)
    

@datasource_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['datasource:add'])
def datasource_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "name": {
            "name": "名称",
            "required": True
        },
        "type": {
            "name": "类型",
            "required": True
        },
         "conn_conf": {
            "name": "连接配置",
            "funcs": [validate_json]
        },
        "ext_params": {
            "name": "额外参数",
            "funcs": [validate_json]
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataSourceApiService().add_obj(req_dict)
    return jsonify(res_data)
    

@datasource_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['datasource:edit'])
def datasource_edit():
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
        },
        "type": {
            "name": "类型",
            "required": True
        },
        "conn_conf": {
            "name": "连接配置",
            "required": True,
            "funcs": [validate_json]
        },
        "ext_params": {
            "name": "额外参数",
            "funcs": [validate_json]
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataSourceApiService().edit_obj(req_dict)
    return jsonify(res_data)
    

@datasource_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['datasource:delete'])
def datasource_delete():
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
    res_data = DataSourceApiService().delete_obj(req_dict)
    return jsonify(res_data)
    

@datasource_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['datasource:delete'])
def datasource_deleteBatch():
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
    res_data = DataSourceApiService().delete_batch(req_dict)
    return jsonify(res_data)
    

@datasource_bp.route('/importExcel', methods=['POST'])
@validate_user
@validate_permissions([])
def datasource_importExcel():
    '''
    excel导入
    '''
    file = request.files.get('file', '')
    if file == '':
        res_data = gen_json_response(code=400, msg='请上传文件')
    else:
        res_data = DataSourceApiService().importExcel(file)
    return jsonify(res_data)
    

@datasource_bp.route('/exportXls', methods=['GET'])
@validate_user
@validate_permissions([])
def datasource_exportXls():
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
        output_file = DataSourceApiService().exportXls(req_dict)
        return generate_download_file(output_file, 'output')
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"未知错误：{e}"))


@datasource_bp.route('/connect', methods=['POST'])
@validate_user
@validate_permissions([])
def datasource_connect():
    '''
    数据源连接测试
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "type": {
            "name": "数据源类型",
            "required": True
        },
        "conn_conf": {
            "name": "连接配置",
            "funcs": [validate_json]
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataSourceApiService().connTest(req_dict)
    return jsonify(res_data)
