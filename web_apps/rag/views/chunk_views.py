'''
知识段管理模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.rag.services.chunk_api_services import ChunkApiService
from web_apps.rag.services.rag_service import train_qa_info
chunk_bp = Blueprint('chunk', __name__)
    

@chunk_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def chunk_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ChunkApiService.get_obj_list(req_dict)
    return jsonify(res_data)
    

@chunk_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def chunk_detail():
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
    res_data = ChunkApiService.get_obj_detail(req_dict)
    return jsonify(res_data)
    

@chunk_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions([])
def chunk_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = ChunkApiService.add_obj(req_dict)
    return jsonify(res_data)
    

@chunk_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions([])
def chunk_edit():
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
    res_data = ChunkApiService.edit_obj(req_dict)
    return jsonify(res_data)
    

@chunk_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def chunk_delete():
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
    res_data = ChunkApiService.delete_obj(req_dict)
    return jsonify(res_data)
    

@chunk_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def chunk_deleteBatch():
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
    res_data = ChunkApiService.delete_batch(req_dict)
    return jsonify(res_data)


@chunk_bp.route('/qa/star', methods=['POST'])
@validate_user
def chunk_qa_star():
    '''
    保存问答对到知识库
    '''
    req_dict = get_req_para(request)
    print(req_dict)
    verify_dict = {
        'question': {
            'name': '问题',
            'required': True,
        },
        'answer': {
            'name': '回答',
            'required': True,
        },
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return gen_json_response(code=400, msg=not_valid)
    question = req_dict.get('question')
    answer = req_dict.get('answer')
    metadata = req_dict.get('metadata', {})
    try:
        train_qa_info(question, answer, metadata)
        return gen_json_response(msg='标记成功', extends={'success': True})
    except Exception as e:
        return gen_json_response(code=400, msg=f'标记失败:{e}')