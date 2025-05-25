from flask import jsonify, request
from flask import Blueprint
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
from utils.auth import validate_user, validate_permissions
from web_apps.scheduler.services.scheduler_api_service import JobApiService
from web_apps.scheduler.services.celery_api_services import CeleryApiService
scheduler_bp = Blueprint('scheduler', __name__)


@scheduler_bp.route('/job/list', methods=['GET'])
def get_job_list():
    """
    任务列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = JobApiService().get_obj_list(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/job/info', methods=['GET'])
def get_job_info():
    """
    任务信息
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = JobApiService().get_obj_info(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/job/start', methods=['POST', 'PUT'])
def start_job():
    """
    启动任务
    """
    req_dict = get_req_para(request)
    print(req_dict)
    check_dict = {
        'job_id': {
            'name': '任务id',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, check_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = JobApiService().start_job(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/job/remove', methods=['POST', 'DELETE'])
def remove_job():
    """
    删除
    """
    req_dict = get_req_para(request)
    res_data = JobApiService().remove_job(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/celery/worker/base/list', methods=['GET'])
def get_celery_worker_base_list():
    """
    celery worker列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = CeleryApiService().get_worker_base_list(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/celery/worker/list', methods=['GET'])
@validate_user
@validate_permissions(['worker:detail'])
def get_celery_worker_list():
    """
    celery worker列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = CeleryApiService().get_worker_list(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/celery/worker/queue/add', methods=['POST'])
@validate_user
def add_worker_queue():
    """
    增加worker订阅队列
    """
    req_dict = get_req_para(request)
    print(req_dict)
    check_dict = {
        'workername': {
            'name': 'worker名称',
            'not_empty': True,
        },
        'queue': {
            'name': '队列名称',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, check_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = CeleryApiService().add_consumer(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/celery/worker/queue/delete', methods=['POST'])
@validate_user
def delete_worker_queue():
    """
    删除worker订阅队列
    """
    req_dict = get_req_para(request)
    print(req_dict)
    check_dict = {
        'workername': {
            'name': 'worker名称',
            'not_empty': True,
        },
        'queue': {
            'name': '队列名称',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, check_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = CeleryApiService().cancel_consumer(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/celery/worker/concurrency/add', methods=['POST'])
@validate_user
def add_worker_concurrency():
    """
    增加worker并发数
    """
    req_dict = get_req_para(request)
    print(req_dict)
    check_dict = {
        'workername': {
            'name': 'worker名称',
            'not_empty': True,
        },
        'concurrency': {
            'name': '并发数',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, check_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = CeleryApiService().add_concurrency(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/celery/worker/concurrency/reduce', methods=['POST'])
@validate_user
def reduce_worker_queue():
    """
    减少worker并发数
    """
    req_dict = get_req_para(request)
    print(req_dict)
    check_dict = {
        'workername': {
            'name': 'worker名称',
            'not_empty': True,
        },
        'concurrency': {
            'name': '并发数',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, check_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = CeleryApiService().reduce_concurrency(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/celery/worker/shutdown', methods=['POST'])
@validate_user
def shutdown_worker():
    """
    关闭worker
    """
    req_dict = get_req_para(request)
    print(req_dict)
    check_dict = {
        'workername': {
            'name': 'worker名称',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, check_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = CeleryApiService().shutdown_worker(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/celery/task/list', methods=['GET'])
@validate_user
def get_celery_task_list():
    """
    celery任务列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = CeleryApiService().get_task_list(req_dict)
    return jsonify(res_data)


@scheduler_bp.route('/celery/task/stop', methods=['POST'])
@validate_user
def task_stop():
    """
    启动任务
    """
    req_dict = get_req_para(request)
    print(req_dict)
    check_dict = {
        'task_id': {
            'name': '任务id',
            'not_empty': True,
        }
    }
    not_valid = validate_params(req_dict, check_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = CeleryApiService().revoke_task({'task_id': req_dict['task_id'], 'terminate': True})
    return jsonify(res_data)


@scheduler_bp.route('/celery/task/info', methods=['GET'])
@validate_user
def get_celery_task_info():
    """
    celery任务详情
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = CeleryApiService().get_task_info(req_dict)
    return jsonify(res_data)