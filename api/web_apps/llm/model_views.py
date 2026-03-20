"""
LLM模型管理API
"""
import json
import traceback
from flask import Blueprint, request
from utils.common_utils import gen_json_response, gen_uuid
from utils.auth import validate_user, set_insert_user, set_update_user
from web_apps import db
from web_apps.llm.db_models import LLMModel
from web_apps.llm.provider_config import PROVIDER_CONFIGS, get_provider_config
from utils.logger.logger import get_logger

logger = get_logger(p_name='system_log', f_name='llm_model', log_level='INFO')
model_bp = Blueprint('llm_model', __name__)


# ==================== Provider（只读，来自配置） ====================

@model_bp.route('/provider/list', methods=['GET'])
@validate_user
def provider_list():
    """获取提供商列表（来自配置，只读）"""
    # 隐藏 api_key，前端不需要
    data = [
        {k: v for k, v in p.items() if k != 'api_key'}
        for p in PROVIDER_CONFIGS
    ]
    return gen_json_response(data=data)


@model_bp.route('/provider/fetch_models', methods=['GET'])
@validate_user
def provider_fetch_models():
    """从提供商 API 获取可用模型列表（不写库）"""
    try:
        provider_code = request.args.get('provider', '')
        if not provider_code:
            return gen_json_response(code=400, msg='provider 不能为空')

        provider = get_provider_config(provider_code)
        if not provider:
            return gen_json_response(code=400, msg=f'未找到提供商: {provider_code}')

        models = _fetch_models_from_api(provider)
        logger.info(f"从 {provider['name']} 获取到 {len(models)} 个模型")
        return gen_json_response(data=models)
    except Exception as e:
        logger.error(f"获取提供商模型列表失败: {str(e)}\n{traceback.format_exc()}")
        return gen_json_response(code=500, msg=f'获取模型列表失败: {str(e)}')


@model_bp.route('/provider/sync_models', methods=['POST'])
@validate_user
def provider_sync_models():
    """将选中的模型批量同步（写入）到数据库，已存在的跳过"""
    try:
        req_data = request.get_json()
        provider_code = req_data.get('provider', '')
        model_items = req_data.get('models', [])

        if not provider_code:
            return gen_json_response(code=400, msg='provider 不能为空')
        if not get_provider_config(provider_code):
            return gen_json_response(code=400, msg=f'未找到提供商: {provider_code}')
        if not model_items:
            return gen_json_response(code=400, msg='请选择至少一个模型')

        existing_codes = {
            m.model_code for m in db.session.query(LLMModel.model_code).filter(
                LLMModel.provider == provider_code
            ).all()
        }

        added = []
        for item in model_items:
            code = item.get('model_code', '').strip()
            if not code or code in existing_codes:
                continue
            model = LLMModel(
                id=gen_uuid(),
                provider=provider_code,
                name=item.get('name', code),
                model_code=code,
                model_type=item.get('model_type', 'chat'),
                api_key='',
                base_url='',
                description='',
                config='{}',
                status=1,
                is_default=0
            )
            set_insert_user(model)
            db.session.add(model)
            added.append(code)

        db.session.commit()
        logger.info(f"同步模型完成，provider={provider_code}，新增 {len(added)} 个")
        return gen_json_response(msg=f'同步成功，新增 {len(added)} 个模型', extends={'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"同步模型失败: {str(e)}\n{traceback.format_exc()}")
        return gen_json_response(code=500, msg=str(e))


def _fetch_models_from_api(provider: dict) -> list:
    """从提供商 API 拉取模型列表"""
    import requests as req_lib

    provider_type = provider['provider_type']
    base_url = (provider.get('base_url') or '').rstrip('/')
    api_key = provider.get('api_key', '')

    if provider_type in ('openai', 'tongyi'):
        if not base_url:
            base_url = 'https://api.openai.com/v1' if provider_type == 'openai' \
                else 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        resp = req_lib.get(
            f'{base_url}/models',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=15
        )
        resp.raise_for_status()
        items = resp.json().get('data', [])
        return [{'model_code': m['id'], 'name': m['id']} for m in items]

    raise ValueError(f'提供商类型 {provider_type} 不支持自动获取模型列表')


# ==================== Model CRUD ====================

@model_bp.route('/list', methods=['GET'])
@validate_user
def model_list():
    """获取模型列表（分页）"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        provider = request.args.get('provider', '')
        model_type = request.args.get('model_type', '')
        keyword = request.args.get('keyword', '')

        query = db.session.query(LLMModel)

        if provider:
            query = query.filter(LLMModel.provider == provider)
        if model_type:
            query = query.filter(LLMModel.model_type == model_type)
        if keyword:
            query = query.filter(
                db.or_(
                    LLMModel.name.like(f'%{keyword}%'),
                    LLMModel.model_code.like(f'%{keyword}%')
                )
            )

        total = query.count()
        models = query.order_by(LLMModel.create_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return gen_json_response(data={'records': [m.to_dict() for m in models], 'total': total})
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return gen_json_response(code=500, msg=str(e))


@model_bp.route('/queryAllList', methods=['GET'])
@validate_user
def model_query_all_list():
    """获取所有模型列表（下拉用）"""
    try:
        model_type = request.args.get('model_type', '')
        provider = request.args.get('provider', '')

        query = db.session.query(LLMModel).filter(LLMModel.status == 1)
        if model_type:
            query = query.filter(LLMModel.model_type == model_type)
        if provider:
            query = query.filter(LLMModel.provider == provider)

        models = query.order_by(LLMModel.create_time.desc()).all()
        return gen_json_response(data=[m.to_dict() for m in models])
    except Exception as e:
        logger.error(f"获取模型全量列表失败: {str(e)}")
        return gen_json_response(code=500, msg=str(e))


@model_bp.route('/add', methods=['POST'])
@validate_user
def model_add():
    """新增模型"""
    try:
        req_data = request.get_json()

        provider_code = req_data.get('provider', '')
        if not provider_code:
            return gen_json_response(code=400, msg='provider 不能为空')
        if not get_provider_config(provider_code):
            return gen_json_response(code=400, msg=f'未找到提供商: {provider_code}')

        config = req_data.get('config', {})
        if isinstance(config, dict):
            config = json.dumps(config, ensure_ascii=False)

        model = LLMModel(
            id=gen_uuid(),
            provider=provider_code,
            name=req_data.get('name'),
            model_code=req_data.get('model_code'),
            model_type=req_data.get('model_type', 'chat'),
            api_key=req_data.get('api_key', ''),
            base_url=req_data.get('base_url', ''),
            description=req_data.get('description', ''),
            config=config,
            status=req_data.get('status', 1),
            is_default=req_data.get('is_default', 0)
        )
        set_insert_user(model)
        db.session.add(model)
        db.session.commit()

        logger.info(f"新增模型成功: {model.name}")
        return gen_json_response(data=model.to_dict(), msg='新增成功', extends={'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"新增模型失败: {str(e)}")
        return gen_json_response(code=500, msg=str(e))


@model_bp.route('/edit', methods=['POST'])
@validate_user
def model_edit():
    """编辑模型"""
    try:
        req_data = request.get_json()
        model_id = req_data.get('id')
        if not model_id:
            return gen_json_response(code=400, msg='模型ID不能为空')

        model = db.session.query(LLMModel).filter(LLMModel.id == model_id).first()
        if not model:
            return gen_json_response(code=400, msg='模型不存在')

        model.name = req_data.get('name', model.name)
        model.model_code = req_data.get('model_code', model.model_code)
        model.model_type = req_data.get('model_type', model.model_type)
        model.api_key = req_data.get('api_key', model.api_key)
        model.base_url = req_data.get('base_url', model.base_url)
        model.description = req_data.get('description', model.description)
        model.status = req_data.get('status', model.status)
        model.is_default = req_data.get('is_default', model.is_default)

        if 'config' in req_data:
            config = req_data['config']
            model.config = json.dumps(config, ensure_ascii=False) if isinstance(config, dict) else config

        set_update_user(model)
        db.session.commit()

        logger.info(f"编辑模型成功: {model.name}")
        return gen_json_response(data=model.to_dict(), msg='编辑成功', extends={'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"编辑模型失败: {str(e)}")
        return gen_json_response(code=500, msg=str(e))


@model_bp.route('/delete', methods=['DELETE'])
@validate_user
def model_delete():
    """删除模型"""
    try:
        req_data = request.get_json()
        model_id = req_data.get('id')
        if not model_id:
            return gen_json_response(code=400, msg='模型ID不能为空')

        model = db.session.query(LLMModel).filter(LLMModel.id == model_id).first()
        if not model:
            return gen_json_response(code=400, msg='模型不存在')

        db.session.delete(model)
        db.session.commit()

        logger.info(f"删除模型成功: {model.name}")
        return gen_json_response(msg='删除成功', extends={'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除模型失败: {str(e)}")
        return gen_json_response(code=500, msg=str(e))


@model_bp.route('/set_default', methods=['POST'])
@validate_user
def model_set_default():
    """设置默认模型（同 provider 下其他模型取消默认）"""
    try:
        req_data = request.get_json()
        model_id = req_data.get('id')
        if not model_id:
            return gen_json_response(code=400, msg='模型ID不能为空')

        model = db.session.query(LLMModel).filter(LLMModel.id == model_id).first()
        if not model:
            return gen_json_response(code=400, msg='模型不存在')

        db.session.query(LLMModel).filter(LLMModel.provider == model.provider).update({'is_default': 0})
        model.is_default = 1
        db.session.commit()

        logger.info(f"设置默认模型成功: {model.name}")
        return gen_json_response(msg='设置成功', extends={'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"设置默认模型失败: {str(e)}")
        return gen_json_response(code=500, msg=str(e))
