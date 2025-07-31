from flask import jsonify, request, Blueprint
from utils.auth import get_auth_token_info
from utils.auth import validate_user, validate_permissions
from web_apps.system.services.system_service import SysLogService, SysInfoService
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
system_bp = Blueprint('system', __name__)


@system_bp.route('/log/query', methods=['GET'])
@validate_user
def logs_query():
    """
    系统日志查询
    """
    req_dict = get_req_para(request)
    res_data = SysLogService().query_logs(req_dict)
    return jsonify(res_data)


@system_bp.route('/dashboard/count', methods=['GET'])
@validate_user
def dashboard_count():
    """
    主页统计信息
    """
    req_dict = get_req_para(request)
    res_data = SysInfoService().query_dashboard_count(req_dict)
    return jsonify(res_data)


@system_bp.route('/visit/count', methods=['GET'])
@validate_user
def visit_count():
    """
    接口调用统计信息
    """
    req_dict = get_req_para(request)
    res_data = SysInfoService().query_visit_count(req_dict)
    return jsonify(res_data)


@system_bp.route('/task/count', methods=['GET'])
@validate_user
def task_count():
    """
    任务执行统计信息
    """
    req_dict = get_req_para(request)
    res_data = SysInfoService().query_task_count(req_dict)
    return jsonify(res_data)


@system_bp.route('/datamodel/type/count', methods=['GET'])
@validate_user
def datamodel_type_count():
    """
    数据模型类型统计信息
    """
    req_dict = get_req_para(request)
    res_data = SysInfoService().query_datamodel_type_count(req_dict)
    return jsonify(res_data)

@system_bp.route('/task/status/count', methods=['GET'])
@validate_user
def task_status_count():
    """
    任务状态统计信息
    """
    req_dict = get_req_para(request)
    res_data = SysInfoService().query_task_status_count(req_dict)
    return jsonify(res_data)


@system_bp.route('/interface/count', methods=['GET'])
@validate_user
def interface_count():
    """
    任务状态统计信息
    """
    req_dict = get_req_para(request)
    res_data = SysInfoService().query_interface_count(req_dict)
    return jsonify(res_data)
