"""会话与用户对话配置的读写(从 ai_chat_service 抽出)。

这些方法与「活体 agent 运行」解耦:只读写 agno storage(会话/transcript)与库内用户配置,
不构造 agent、不涉及流式。历史回放的展示重建(图片路径、工具块)也归在此处。
对外仍由 AiChatService 门面委派(见 ai_chat_service.py 末尾)。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING, Any

from agno.db.base import SessionType
from agno.run.cancel import acancel_run
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from config.env import UploadConfig
from exceptions.exception import ServiceException
from module_ai.dao.ai_chat_dao import AiChatConfigDao
from module_ai.entity.do.ai_chat_do import AiChatConfig
from module_ai.entity.vo.ai_chat_vo import (
    AgentDataModel,
    AiChatConfigModel,
    AiChatSessionBaseModel,
    AiChatSessionModel,
    ChatMessageModel,
    MessageMetrics,
    SessionDataModel,
    SessionMetricsModel,
)
from utils.ai_util import AiUtil
from utils.common_util import CamelCaseUtil

if TYPE_CHECKING:
    from agno.media import Image
    from agno.models.message import Message
    from agno.run.agent import RunOutput
    from agno.run.team import TeamRunOutput
    from agno.run.workflow import WorkflowRunOutput
    from agno.session import Session


def _rebuild_blocks(m: Message, tool_results: dict[str, Any]) -> list[dict] | None:
    """把一条 assistant 消息重建成与流式同构的 blocks(文字 + 工具调用),供历史回放展示工具调用。

    tool_results: {tool_call_id: 结果文本}(由 role='tool' 的消息预索引)。
    工具调用参数(arguments)为 JSON 串 → 解析成 dict;结果从 tool_results 回填。
    """
    blocks: list[dict] = []
    if m.content:
        blocks.append({'type': 'text', 'text': m.content})
    for tc in getattr(m, 'tool_calls', None) or []:
        if isinstance(tc, dict):
            tc_id = tc.get('id')
            fn = tc.get('function') or {}
            name = fn.get('name')
            raw_args = fn.get('arguments')
        else:  # 对象形态兜底
            tc_id = getattr(tc, 'id', None)
            fn = getattr(tc, 'function', None)
            name = getattr(fn, 'name', None) if fn else None
            raw_args = getattr(fn, 'arguments', None) if fn else None
        args: Any = raw_args
        if isinstance(raw_args, str):
            try:
                args = json.loads(raw_args)
            except (ValueError, TypeError):
                args = raw_args
        result = tool_results.get(tc_id)
        err = isinstance(result, str) and result.lstrip().startswith(('执行失败', '调用沙箱失败', '数据源解析失败'))
        blocks.append(
            {
                'type': 'tool',
                'id': tc_id,
                'name': name,
                'args': args,
                'status': 'error' if err else 'done',
                'result': result,
            }
        )
    return blocks or None


def _convert_images_to_upload_paths(images: list[Image] | None) -> list[str] | None:
    """
    将Agno Image对象列表转换为前端可访问的上传路径列表

    :param images: Image对象列表
    :return: 上传路径列表
    """
    if not images:
        return None

    result = []
    for img in images:
        # 如果是本地文件路径
        if hasattr(img, 'filepath') and img.filepath:
            try:
                # 使用 abspath 确保路径标准化
                abs_filepath = os.path.abspath(img.filepath)
                abs_upload_path = os.path.abspath(UploadConfig.UPLOAD_PATH)

                if abs_filepath.startswith(abs_upload_path):
                    relative_path = os.path.relpath(abs_filepath, abs_upload_path)
                    # 转换路径分隔符为URL格式
                    url_path = relative_path.replace(os.sep, '/')
                    # 拼接前缀
                    full_url = f'{UploadConfig.UPLOAD_PREFIX}/{url_path}'.replace('//', '/')
                    result.append(full_url)
                else:
                    result.append(img.filepath)
            except Exception:
                result.append(img.filepath)
        # 如果是URL
        elif hasattr(img, 'url') and img.url:
            result.append(img.url)

    return result if result else None


async def ai_chat_config_detail_services(query_db: AsyncSession, user_id: int) -> AiChatConfigModel:
    """
    获取用户配置

    :param query_db: orm对象
    :param user_id: 用户ID
    :return: 配置模型
    """
    chat_config = await AiChatConfigDao.get_chat_config_detail_by_user_id(query_db, user_id)
    result = AiChatConfigModel(**CamelCaseUtil.transform_result(chat_config)) if chat_config else AiChatConfig()

    return result


async def save_ai_chat_config_services(
    query_db: AsyncSession, user_id: int, page_object: AiChatConfigModel
) -> CrudResponseModel:
    """
    保存用户配置

    :param query_db: orm对象
    :param user_id: 用户ID
    :param page_object: AI对话配置对象
    :return: 更新后的配置模型
    """
    chat_config = await AiChatConfigDao.get_chat_config_detail_by_user_id(query_db, user_id)
    if page_object.user_id is None:
        page_object.user_id = user_id

    try:
        if chat_config:
            if chat_config.chat_config_id != page_object.chat_config_id:
                raise ServiceException(message='只允许修改当前用户的配置')
            page_object.update_time = datetime.now()
            edit_ai_chat_config = page_object.model_dump(exclude_unset=True)
            await AiChatConfigDao.edit_chat_config_dao(query_db, edit_ai_chat_config)
        else:
            page_object.create_time = datetime.now()
            await AiChatConfigDao.add_chat_config_dao(query_db, page_object)

        await query_db.commit()
    except Exception as e:
        await query_db.rollback()
        raise e

    return CrudResponseModel(is_success=True, message='保存成功')


async def get_chat_session_list_services(user_id: int, app_id: str | None = None) -> list[AiChatSessionBaseModel]:
    """
    获取用户会话列表

    会话按 session_id 前缀区分归属:应用对话用 `app-{appId}-` 前缀。
    - 传 app_id:只返回该应用的会话;
    - 不传:返回普通对话会话(排除所有 `app-` 前缀的应用会话),保持普通对话页干净。

    :param user_id: 用户ID
    :param app_id: 应用ID(可选,按应用过滤会话)
    :return: 用户会话列表
    """
    # 获取Agno会话列表
    storage = AiUtil.get_storage_engine()
    sessions: list[Session] = await storage.get_sessions(
        user_id=str(user_id),
        component_id='chat-agent',
        session_type=SessionType.AGENT,
    )

    app_prefix = f'app-{app_id}-' if app_id else None
    result = []
    for s in sessions:
        sid = s.session_id or ''
        if app_prefix is not None:
            if not sid.startswith(app_prefix):
                continue  # 只要本应用的会话
        elif sid.startswith('app-'):
            continue  # 普通对话列表:排除应用会话
        created_at = datetime.fromtimestamp(s.created_at) if s.created_at else None
        updated_at = datetime.fromtimestamp(s.updated_at) if s.updated_at else None

        title_limit = 20
        session_title = s.runs[0].input.input_content[:title_limit] + '...' if s.runs else ''

        result.append(
            AiChatSessionBaseModel(
                sessionId=s.session_id,
                sessionTitle=session_title if len(session_title) <= title_limit else session_title[:title_limit],
                userId=s.user_id,
                createdAt=created_at,
                updatedAt=updated_at,
            )
        )
    return result


async def delete_chat_session_services(session_id: str) -> CrudResponseModel:
    """
    删除会话

    :param session_id: 会话ID
    :return: 删除结果
    """
    storage = AiUtil.get_storage_engine()
    delete_result = await storage.delete_session(session_id=session_id)
    if not delete_result:
        raise ServiceException(message='删除会话失败')
    return CrudResponseModel(is_success=True, message='删除成功')


async def get_chat_session_detail_services(session_id: str) -> AiChatSessionModel:
    """
    获取会话消息详情

    :param session_id: 会话ID
    :return: 会话消息详情
    """
    storage = AiUtil.get_storage_engine()
    session: Session | None = await storage.get_session(session_id=session_id, session_type=SessionType.AGENT)

    if not session:
        raise ServiceException(message='会话不存在')

    session_data: dict[str, Any] = session.session_data or {}  # 快路/异常会话可能为空,兜底避免 NoneType
    agent_data: dict[str, Any] = session.agent_data or {}
    runs: list[RunOutput | TeamRunOutput | WorkflowRunOutput] = session.runs
    messages: list[Message] = session.get_messages(skip_roles=['system'])

    run_metrics_map = {}
    if runs:
        for run in runs:
            if run.model_provider_data and (provider_id := run.model_provider_data.get('id')):
                run_metrics_map[provider_id] = run.metrics

    # 工具结果按 tool_call_id 预索引(role='tool' 的消息),供重建工具块时回填 result
    tool_results = {
        getattr(m, 'tool_call_id', None): m.content
        for m in messages
        if m.role == 'tool' and getattr(m, 'tool_call_id', None)
    }

    chat_messages = []
    for m in messages:
        if hasattr(m, 'provider_data') and m.provider_data:
            provider_id = m.provider_data.get('id')
            if provider_id and provider_id in run_metrics_map:
                m.metrics = run_metrics_map[provider_id]

        metrics_model = None
        if getattr(m, 'metrics', None) and hasattr(m.metrics, 'to_dict'):
            metrics_dict = m.metrics.to_dict()
            if metrics_dict:
                metrics_model = MessageMetrics(**CamelCaseUtil.transform_result(metrics_dict))

        chat_messages.append(
            ChatMessageModel(
                id=m.id,
                role=m.role,
                content=m.content,
                images=_convert_images_to_upload_paths(m.images),
                metrics=metrics_model,
                createdAt=datetime.fromtimestamp(m.created_at) if m.created_at else None,
                reasoningContent=m.reasoning_content,
                fromHistory=m.from_history,
                stopAfterToolCall=m.stop_after_tool_call,
                blocks=_rebuild_blocks(m, tool_results) if m.role == 'assistant' else None,
            )
        )

    session_detail = AiChatSessionModel(
        sessionId=session.session_id,
        sessionTitle=session.runs[0].input.input_content[:20] + '...' if session.runs else '',
        userId=session.user_id,
        createdAt=datetime.fromtimestamp(session.created_at) if session.created_at else None,
        updatedAt=datetime.fromtimestamp(session.updated_at) if session.updated_at else None,
        agentId=session.agent_id,
        sessionData=SessionDataModel(
            sessionState=session_data.get('session_state'),
            sessionMetrics=SessionMetricsModel(
                **CamelCaseUtil.transform_result(session_data.get('session_metrics') or {})
            ),
        ),
        agentData=AgentDataModel(**CamelCaseUtil.transform_result(agent_data)),
        messages=chat_messages,
    )

    return session_detail


async def cancel_run_services(run_id: str) -> CrudResponseModel:
    """
    取消运行

    :param run_id: 运行ID
    :return: 取消结果
    """
    cancel_result = await acancel_run(run_id)
    if not cancel_result:
        raise ServiceException(message='取消运行失败')
    return CrudResponseModel(is_success=True, message='取消成功')
