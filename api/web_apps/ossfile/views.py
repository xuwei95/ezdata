'''
对象存储模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
from web_apps.ossfile.services import FileService
from utils.storage_utils import storage
from config import SYS_CONF
file_bp = Blueprint('file', __name__)


@file_bp.route('/list', methods=['GET'])
@validate_user
def file_list():
    """
    文件列表
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = FileService().get_obj_list(req_dict)
    return jsonify(res_data)


@file_bp.route('/upload', methods=['POST'])
@validate_user
@validate_permissions(['system:oss:upload'])
def file_upload():
    """
    上传文件到对象存储
    """
    req_dict = get_req_para(request)
    file = request.files.get('file', '')
    if file != '':
        file_name = req_dict.get('file_name', file.filename)
        file_type = file.filename.split('.')[-1]
        content = file.read()
        storage.save(file_name, content)
        file_url = storage.get_download_url(file_name)
    else:
        res_data = gen_json_response(code=400, msg='文件获取失败')
        return jsonify(res_data)
    file_params = {'url': file_url, 'file_type': file_type, 'file_name': file.filename}
    res_data = FileService().add_obj(file_params)
    return jsonify(res_data)


@file_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['system:oss:delete'])
def file_delete():
    """
    删除
    """
    req_dict = get_req_para(request)
    print(req_dict)
    res_data = FileService().delete_obj(req_dict)
    return jsonify(res_data)