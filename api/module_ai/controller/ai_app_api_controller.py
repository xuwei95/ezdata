"""AI 应用对外 API:用应用 APIKey(非登录态)发起流式对话。

与登录态对话分开:本路由不挂 PreAuthDependency,鉴权改为校验 ai_app_token。
"""

import uuid
from typing import Annotated

from fastapi import Header, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.context import RequestContext
from common.router import APIRouterPro
from module_ai.entity.vo.ai_app_vo import ApiChatReq
from module_ai.entity.vo.ai_chat_vo import AiChatRequestModel
from module_ai.service.ai_app_service import AiAppService
from module_ai.service.ai_chat_service import AiChatService
from utils.log_util import logger
from utils.response_util import ResponseUtil

# 独立路由:无 PreAuthDependency(对外开放,靠 apikey 鉴权)
ai_app_api_controller = APIRouterPro(prefix='/ai/app/api', order_num=22, tags=['AI管理-应用对外API'])


@ai_app_api_controller.post(
    '/chat',
    summary='应用对外流式对话(APIKey鉴权)',
    description='Header X-API-Key 或 body.apiKey 传应用 APIKey;流式返回',
    response_class=StreamingResponse,
)
async def app_api_chat(
    request: Request,
    chat_req: ApiChatReq,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    x_api_key: Annotated[str | None, Header(alias='X-API-Key')] = None,
) -> Response:
    api_key = chat_req.api_key or x_api_key
    token = await AiAppService.resolve_token(query_db, (api_key or '').strip())
    if not token:
        return ResponseUtil.failure(msg='无效或已过期的 API Key')

    session_id = chat_req.session_id or str(uuid.uuid4())
    req = AiChatRequestModel(
        modelId=0, message=chat_req.message, sessionId=session_id, appId=str(token['app_id'])
    )
    # 外部调用无租户中间件:用 token 的租户开启上下文,使应用/工具/知识库查询正确隔离
    tenant_id = token.get('tenant_id')
    # 租户默认拒绝:无租户绑定的 Key 一律拒绝(不再无上下文放行)
    if tenant_id is None:
        return ResponseUtil.failure(msg='API Key 未绑定租户,禁止访问')

    async def _stream():
        tok = RequestContext.set_current_tenant_id(tenant_id)
        try:
            async for chunk in AiChatService.chat_services(query_db, req, 0):
                yield chunk
        except Exception as e:  # noqa: BLE001
            logger.exception(f'应用对外对话异常: {e}')
        finally:
            if tok is not None:
                RequestContext.reset_current_tenant_id(tok)

    logger.info(f'应用对外对话: app_id={token["app_id"]} session={session_id}')
    return StreamingResponse(content=_stream(), media_type='text/event-stream')
