import json
from typing import Any

from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_ai.dao.ai_app_dao import AiAppDao
from module_ai.entity.vo.ai_app_vo import AiAppModel, AiAppPageQueryModel, DeleteAiAppModel
from utils.ai_util import AiUtil
from utils.common_util import CamelCaseUtil

_DEFAULT_CONFIG: dict = {
    'prompt': '', 'prologue': '', 'presetQuestions': [], 'quickCommands': [],
    'toolIds': [], 'datasetIds': [], 'model': {'modelId': 0, 'temperature': None, 'maxTokens': None},
}

_PROMPT_META = (
    '你是资深提示词工程师。请根据用户给出的“应用定位/需求”,产出一份高质量、结构化的中文系统提示词(system prompt),'
    '用于设定一个 AI 助手的角色、技能、工作流程与限制。要求:用 Markdown 分节(# 角色 / ## 技能 / ## 限制 等),'
    '具体可执行、贴合需求,不要加解释或寒暄,直接输出提示词正文。'
)


def _dumps(v: Any) -> str:
    return v if isinstance(v, str) else json.dumps(v or {}, ensure_ascii=False)


def _loads(v: Any) -> Any:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (ValueError, TypeError):
            return {}
    return v if v is not None else {}


class AiAppService:
    """AI应用管理服务层"""

    @classmethod
    async def get_ai_app_list_services(
        cls, query_db: AsyncSession, query_object: AiAppPageQueryModel,
        data_scope_sql: ColumnElement, is_page: bool = False,
    ) -> PageModel | list[dict[str, Any]]:
        result = await AiAppDao.get_ai_app_list(query_db, query_object, data_scope_sql, is_page)
        rows = result.rows if isinstance(result, PageModel) else result
        for row in rows:
            if 'config' in row:
                row['config'] = _loads(row['config'])
        return result

    @classmethod
    async def add_ai_app_services(cls, query_db: AsyncSession, page_object: AiAppModel) -> CrudResponseModel:
        data = page_object.model_dump(exclude_unset=True)
        data.pop('app_id', None)
        cfg = {**_DEFAULT_CONFIG, **(data.get('config') or {})}
        data['config'] = _dumps(cfg)
        try:
            obj = await AiAppDao.add_ai_app_dao(query_db, data)
            app_id = obj.app_id  # flush 后已有主键;commit 后 ORM 实例会过期,提前捕获避免惰性加载
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功', result={'appId': app_id})
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_ai_app_services(cls, query_db: AsyncSession, page_object: AiAppModel) -> CrudResponseModel:
        existing = await AiAppDao.get_ai_app_detail_by_id(query_db, page_object.app_id)
        if not existing:
            raise ServiceException(message='应用不存在')
        data = page_object.model_dump(exclude_unset=True)
        if 'config' in data:
            data['config'] = _dumps(data.get('config'))
        data['app_id'] = page_object.app_id
        try:
            await AiAppDao.edit_ai_app_dao(query_db, data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_ai_app_services(cls, query_db: AsyncSession, page_object: DeleteAiAppModel) -> CrudResponseModel:
        if not page_object.app_ids:
            raise ServiceException(message='传入应用id为空')
        try:
            for aid in page_object.app_ids.split(','):
                await AiAppDao.delete_ai_app_dao(query_db, int(aid))
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def ai_app_detail_services(cls, query_db: AsyncSession, app_id: int) -> AiAppModel:
        obj = await AiAppDao.get_ai_app_detail_by_id(query_db, app_id)
        if not obj:
            return AiAppModel()
        result = AiAppModel(**CamelCaseUtil.transform_result(obj))
        result.config = {**_DEFAULT_CONFIG, **_loads(result.config)}
        return result

    @classmethod
    async def get_app_config(cls, query_db: AsyncSession, app_id: int) -> dict | None:
        """取应用配置(对话装配用),不存在返回 None。"""
        obj = await AiAppDao.get_ai_app_detail_by_id(query_db, app_id)
        if not obj:
            return None
        return {**_DEFAULT_CONFIG, **_loads(obj.config), '_name': obj.name}

    # ---------- 对外 APIKey ----------
    @classmethod
    async def list_tokens_services(cls, query_db: AsyncSession, app_id: int) -> list[dict]:
        from sqlalchemy import select  # noqa: PLC0415

        from module_ai.entity.do.ai_app_token_do import AiAppToken  # noqa: PLC0415

        rows = (await query_db.execute(
            select(AiAppToken).where(AiAppToken.app_id == app_id).order_by(AiAppToken.create_time.desc())
        )).scalars().all()
        return [CamelCaseUtil.transform_result(r) for r in rows]

    @classmethod
    async def create_token_services(cls, query_db: AsyncSession, app_id: int, name: str, operator: str) -> dict:
        import uuid  # noqa: PLC0415
        from datetime import datetime  # noqa: PLC0415

        from module_ai.entity.do.ai_app_token_do import AiAppToken  # noqa: PLC0415

        api_key = 'app-' + uuid.uuid4().hex
        try:
            obj = AiAppToken(app_id=app_id, api_key=api_key, name=name or '', status='0',
                             create_by=operator, create_time=datetime.now())
            query_db.add(obj)
            await query_db.flush()
            tid = obj.token_id
            await query_db.commit()
            return {'tokenId': tid, 'apiKey': api_key}
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_token_services(cls, query_db: AsyncSession, token_id: int) -> CrudResponseModel:
        from sqlalchemy import delete  # noqa: PLC0415

        from module_ai.entity.do.ai_app_token_do import AiAppToken  # noqa: PLC0415

        await query_db.execute(delete(AiAppToken).where(AiAppToken.token_id == token_id))
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def set_token_status_services(cls, query_db: AsyncSession, token_id: int, status: str) -> CrudResponseModel:
        from sqlalchemy import update  # noqa: PLC0415

        from module_ai.entity.do.ai_app_token_do import AiAppToken  # noqa: PLC0415

        await query_db.execute(update(AiAppToken).where(AiAppToken.token_id == token_id).values(status=status))
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='操作成功')

    @classmethod
    async def resolve_token(cls, query_db: AsyncSession, api_key: str) -> dict | None:
        """校验 apikey:存在+启用+未过期 → 返回 {app_id, tenant_id, create_by};否则 None。"""
        from datetime import datetime  # noqa: PLC0415

        from sqlalchemy import select  # noqa: PLC0415

        from module_ai.entity.do.ai_app_token_do import AiAppToken  # noqa: PLC0415

        if not api_key:
            return None
        t = (await query_db.execute(
            select(AiAppToken).where(AiAppToken.api_key == api_key)
        )).scalars().first()
        if not t or t.status != '0':
            return None
        if t.expire_time and t.expire_time < datetime.now():
            return None
        return {'app_id': t.app_id, 'tenant_id': t.tenant_id, 'create_by': t.create_by}

    @classmethod
    async def generate_prompt_services(cls, query_db: AsyncSession, requirement: str, model_id: int) -> str:
        """调 LLM 根据一句话需求草拟系统提示词(非流式)。"""
        from agno.agent import Agent  # noqa: PLC0415

        from module_ai.service.ai_chat_service import AiChatService  # noqa: PLC0415

        mc = await AiChatService._resolve_chat_model_config(query_db, model_id or 0)
        # 提示词较短,且过大的 max_tokens 会触发 Anthropic SDK "必须流式" 限制 → 固定较小上限
        model = AiUtil.get_model_from_factory(
            provider=mc.provider, model_code=mc.model_code, model_name=mc.model_name,
            api_key=mc.api_key, base_url=mc.base_url, max_tokens=4096,
        )
        agent = Agent(model=model, id='prompt-gen', instructions=[_PROMPT_META], markdown=False)
        run = await agent.arun(f'应用定位/需求:{requirement}')
        return (getattr(run, 'content', None) or '').strip()
