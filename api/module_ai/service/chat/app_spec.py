"""AI 应用(ai_app)→ 多 agent Team 成员装配规格解析(从 ai_chat_service 抽出)。

把用户对话配置里「引用的应用」解析成建成员 Agent 所需的 build_kwargs + 该应用的 mcp_configs,
与 chat_services 的应用模式分支同源(模型/人设/工具/数据源范围/知识库)。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from module_ai.service.chat import agent_factory
from module_ai.service.chat.prompts import _PASSTHROUGH_BUILTIN

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from module_ai.entity.vo.ai_chat_vo import AiChatConfigModel


def load_agent_app_ids(user_config: AiChatConfigModel) -> list[int]:
    """解析用户对话配置里「引用的应用 agent」CSV id 列表(空则不启用多 agent)。"""
    raw = (getattr(user_config, 'agent_app_ids', None) or '').strip()
    if not raw:
        return []
    out: list[int] = []
    for x in raw.split(','):
        x = x.strip()
        if x.isdigit():
            out.append(int(x))
    return out


async def resolve_app_agent_spec(
    query_db: AsyncSession,
    app_id: int,
    user_id: int,
    session_id: str,
    default_temperature: float,
) -> dict | None:
    """把一个应用(ai_app)配置解析成"建成员 Agent 所需的 build_kwargs + 该应用的 mcp_configs"。

    与 chat_services 应用模式分支同源(模型/人设/工具/数据源范围/知识库),供 Team 成员复用。
    成员不加载会话历史(add_history=False),历史由 Team 统一注入。返回 None 表示应用不存在。
    """
    from module_ai.service.ai_app_service import AiAppService
    from module_ai.service.ai_tool_service import AiToolService

    app_cfg = await AiAppService.get_app_config(query_db, app_id)
    if not app_cfg:
        return None
    system_prompt = (app_cfg.get('prompt') or '').strip() or None
    m = app_cfg.get('model') or {}
    model_config = await agent_factory.resolve_chat_model_config(query_db, m.get('modelId') or 0)
    temperature = m['temperature'] if m.get('temperature') is not None else default_temperature
    if m.get('maxTokens'):
        model_config.max_tokens = m['maxTokens']
    resolved = await AiToolService.resolve_app_tools(query_db, app_cfg.get('toolIds') or [])
    # 同应用模式:自选内置工具透传,sandbox_code 始终挂(绘图/计算),data_explore 由数据源选择控制
    builtin_codes = [c for c in resolved['builtin_codes'] if c in _PASSTHROUGH_BUILTIN] + ['sandbox_code']
    mcp_configs = resolved['mcp_configs']
    ds_codes = app_cfg.get('datasourceCodes') or []
    datasource_scope = None
    datasource_query_enabled = bool(ds_codes)
    if ds_codes:
        builtin_codes = builtin_codes + ['data_explore']
        datasource_scope = ds_codes
    kb_tool = None
    dsids = app_cfg.get('datasetIds') or []
    if dsids:
        from common.context import RequestContext
        from module_rag.agent_tools import make_kb_tool

        kb_tool = make_kb_tool(dataset_ids=dsids, tenant_id=RequestContext.get_effective_tenant_id())
    from module_ai.service.ai_skill_service import AiSkillService

    skills = await AiSkillService.resolve_agent_skills(
        query_db, app_cfg.get('skillIds') or None, scope_codes=datasource_scope
    )
    build_kwargs = dict(
        model_config=model_config,
        temperature=temperature,
        system_prompt=system_prompt,
        user_id=user_id,
        session_id=f'{session_id}-m{app_id}',
        add_history=False,
        num_history=0,
        builtin_codes=builtin_codes,
        kb_tool=kb_tool,
        instructions=[],
        datasource_scope=datasource_scope,
        datasource_query_enabled=datasource_query_enabled,
        name=app_cfg.get('_name') or f'应用{app_id}',
        agent_id=f'app-{app_id}',  # 成员需唯一 id,否则 Team 无法按 member_id 区分路由
        skills=skills,
    )
    return {'build_kwargs': build_kwargs, 'mcp_configs': mcp_configs}
