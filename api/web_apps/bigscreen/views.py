'''
数据大屏模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
from web_apps.bigscreen.services import ScreenService
from utils.storage_utils import storage
screen_bp = Blueprint('screen', __name__)


@screen_bp.route('/project/getOssInfo', methods=['GET'])
def get_oss_info():
    """
    获取oss bucket地址
    """
    req_dict = get_req_para(request)
    print(req_dict)
    bucket_url = storage.get_download_url('')
    res_data = gen_json_response(data={'bucketURL': bucket_url})
    return jsonify(res_data)


@screen_bp.route('/project/list', methods=['GET'])
@validate_user
def screen_list():
    """
    列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = ScreenService().get_obj_list(req_dict)
    return jsonify(res_data)


@screen_bp.route('/project/getData', methods=['GET'])
def screen_detail():
    """
    详情
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = ScreenService().get_obj_detail(req_dict)
    return jsonify(res_data)


@screen_bp.route('/project/upload', methods=['POST'])
@validate_user
def screen_upload():
    """
    上传
    """
    file = request.files.get('object', '')
    if file != '':
        file_name = file.filename
        file_type = file.filename.split('.')[-1]
        content = file.read()
        print(content)
        file_url = storage.save(file_name, content)
    else:
        res_data = gen_json_response(code=400, msg='文件获取失败')
        return jsonify(res_data)
    res_data = gen_json_response(data={'fileName': file_name})
    print(res_data)
    return jsonify(res_data)


@screen_bp.route('/project/create', methods=['POST'])
@validate_user
def screen_add():
    """
    添加
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'projectName': {
            'name': '项目名称',
            'not_empty': True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = ScreenService().add_obj(req_dict)
    return jsonify(res_data)


@screen_bp.route('/project/edit', methods=['POST', 'PUT'])
@validate_user
def screen_edit():
    """
    更新
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = ScreenService().update_obj(req_dict)
    return jsonify(res_data)


@screen_bp.route('/project/save/data', methods=['POST', 'PUT'])
@validate_user
def screen_save_data():
    """
    保存内容数据
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = ScreenService().save_obj_data(req_dict)
    return jsonify(res_data)


@screen_bp.route('/project/publish', methods=['POST', 'PUT'])
@validate_user
def screen_publish():
    """
    发布/取消
    """
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    res_data = ScreenService().handle_publish_obj(req_dict)
    return jsonify(res_data)


@screen_bp.route('/project/delete', methods=['POST', 'DELETE'])
@validate_user
def screen_delete():
    """
    删除
    """
    args = request.args
    req_dict = args.to_dict()
    res_data = ScreenService().delete_obj(req_dict)
    return jsonify(res_data)




