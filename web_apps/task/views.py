'''
任务模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.task.services.task_api_services import TaskApiService
task_bp = Blueprint('task', __name__)


@task_bp.route('/resetAllJob', methods=['POST'])
@validate_user
@validate_permissions(['job:restart'])
def task_reset_all_job():
    """
    重启所有定时任务
    """
    req_dict = get_req_para(request)
    print(req_dict)
    check_dict = {}
    not_valid = validate_params(req_dict, check_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = TaskApiService().reset_all_job(req_dict)
    return jsonify(res_data)


@task_bp.route('/start', methods=['POST'])
@validate_user
@validate_permissions(['task:run', 'dag_detail:run'])
def task_start():
    """
    启动任务
    """
    req_dict = get_req_para(request)
    print(req_dict)
    check_dict = {
        'id': {
            'name': '任务id',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, check_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = TaskApiService().start_task(req_dict)
    return jsonify(res_data)


@task_bp.route('/instance/list', methods=['GET'])
@validate_user
@validate_permissions([])
def task_instance_list():
    '''
    任务实例列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {}
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TaskApiService().get_instance_list(req_dict)
    return jsonify(res_data)


@task_bp.route('/instance/logs', methods=['GET'])
# @validate_user
# @validate_permissions([])
def task_instance_logs():
    '''
    任务实例日志查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {}
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TaskApiService().get_instance_logs(req_dict)
    return jsonify(res_data)


@task_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def task_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TaskApiService().get_obj_list(req_dict)
    return jsonify(res_data)


@task_bp.route('/dag/list', methods=['GET'])
@validate_user
@validate_permissions([])
def dag_task_list():
    '''
    dag任务列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TaskApiService().get_dag_task_list(req_dict)
    return jsonify(res_data)


@task_bp.route('/dag/menu', methods=['GET'])
@validate_user
@validate_permissions([])
def dag_task_menu():
    '''
    dag任务模版菜单
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TaskApiService().get_dag_task_menu(req_dict)
    return jsonify(res_data)


@task_bp.route('/dag/node/status', methods=['GET'])
@validate_user
@validate_permissions([])
def dag_task_node_status():
    '''
    dag任务节点状态查询
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TaskApiService().get_dag_task_node_status(req_dict)
    return jsonify(res_data)


@task_bp.route('/template/params', methods=['GET'])
@validate_user
@validate_permissions([])
def task_template_params():
    '''
    任务模版
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        'code': {
            'name': '任务模版编码',
            'required': True,
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TaskApiService().get_task_template_params(req_dict)
    return jsonify(res_data)


@task_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def task_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TaskApiService().get_obj_all_list(req_dict)
    return jsonify(res_data)
    

@task_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def task_detail():
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
    res_data = TaskApiService().get_obj_detail(req_dict)
    return jsonify(res_data)


@task_bp.route('/queryParamsById', methods=['GET'])
@validate_user
@validate_permissions([])
def task_params_detail():
    '''
    参数详情
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
    res_data = TaskApiService().get_obj_params_detail(req_dict)
    return jsonify(res_data)


@task_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['task:add', 'dag:add'])
def task_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = TaskApiService().add_obj(req_dict)
    return jsonify(res_data)
    

@task_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['task:edit', 'dag:edit'])
def task_edit():
    '''
    编辑
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
    res_data = TaskApiService().edit_obj(req_dict)
    return jsonify(res_data)


@task_bp.route('/status', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['task:status', 'dag:status'])
def task_status():
    '''
    编辑状态
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
    res_data = TaskApiService().edit_obj_status(req_dict)
    return jsonify(res_data)


@task_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['task:delete', 'dag:delete'])
def task_delete():
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
    res_data = TaskApiService().delete_obj(req_dict)
    return jsonify(res_data)
    

@task_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['task:delete', 'dag:delete'])
def task_deleteBatch():
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
    res_data = TaskApiService().delete_batch(req_dict)
    return jsonify(res_data)
    

@task_bp.route('/importExcel', methods=['POST'])
@validate_user
@validate_permissions([])
def task_importExcel():
    '''
    excel导入
    '''
    file = request.files.get('file', '')
    if file == '':
        res_data = gen_json_response(code=400, msg='请上传文件')
    else:
        res_data = TaskApiService().importExcel(file)
    return jsonify(res_data)
    

@task_bp.route('/exportXls', methods=['GET'])
@validate_user
@validate_permissions([])
def task_exportXls():
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
        output_file = TaskApiService().exportXls(req_dict)
        return generate_download_file(output_file, 'output')
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"未知错误：{e}"))
