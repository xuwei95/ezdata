"""对话 Agent / Team 的构造工厂(从 ai_chat_service 抽出)。

聚合"构造期"关注点:解析模型配置、造 agno 模型对象(含 provider/网关修复)、装配工具、
长期记忆与工具调用旋钮、运行参数(图片),以及最终 build_agent / build_team。
供单 agent 与 Team leader/成员共用;不涉及流式与会话读写。
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from agno.agent import Agent
from agno.media import Image

from config.env import UploadConfig
from exceptions.exception import ServiceException
from module_ai.dao.ai_model_dao import AiModelDao
from module_ai.entity.vo.ai_model_vo import AiModelModel
from module_ai.service.chat.prompts import _DATA_AGENT_INSTRUCTIONS, _WEAK_AGENT_NUDGE
from utils.ai_util import AiUtil
from utils.common_util import CamelCaseUtil
from utils.crypto_util import CryptoUtil
from utils.log_util import logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from module_ai.entity.vo.ai_chat_vo import AiChatConfigModel, AiChatRequestModel


def make_baidu_tools() -> Any:
    """百度搜索工具集。

    构造时 eager 校验可选依赖(baidusearch/pycountry)——agno 的 BaiduSearchTools 是懒加载
    (import 在搜索方法内),不校验会"挂得上、调用才 ImportError",冒泡到流处理外层拖垮整轮对话。
    这里主动 import 触发依赖检查:缺依赖→抛错→由 assemble_tools 的 try/except 跳过并告警(工具缺席
    而非中途炸),符合"单个内置工具构造失败只跳过"的既定策略。
    """
    import baidusearch  # noqa: F401  eager 触发依赖检查
    import pycountry  # noqa: F401
    from agno.tools.baidusearch import BaiduSearchTools

    return BaiduSearchTools()


async def resolve_chat_model_config(query_db: AsyncSession, model_id: int) -> AiModelModel:
    """解析对话模型配置,返回 api_key 已为明文的 AiModelModel。

    model_id == 0 走环境变量兜底模型(AiConfig/LLM_*,api_key 明文);
    否则查库内模型并解密 api_key。
    """
    if model_id == 0:
        from config.env import AiConfig

        if not AiConfig.enabled:
            raise ServiceException(
                message='未配置兜底模型:请在「AI 模型管理」启用一个对话模型,或配置环境变量 LLM_TYPE/LLM_MODEL/LLM_API_KEY'
            )
        return AiModelModel(
            modelId=0,
            provider=AiConfig.provider,
            modelCode=AiConfig.llm_model,
            apiKey=AiConfig.llm_api_key,
            baseUrl=AiConfig.llm_url or None,
            maxTokens=AiConfig.llm_max_tokens,
            # 兜底模型的推理/多模态能力由环境变量声明(LLM_REASONING / LLM_SUPPORT_IMAGES)
            supportReasoning='Y' if AiConfig.llm_reasoning else 'N',
            supportImages='Y' if AiConfig.llm_support_images else 'N',
        )

    ai_model = await AiModelDao.get_ai_model_detail_by_id(query_db, model_id)
    if not ai_model:
        raise ServiceException(message='模型不存在')
    model_config = AiModelModel(**CamelCaseUtil.transform_result(ai_model))
    if model_config.api_key:
        model_config.api_key = CryptoUtil.decrypt(model_config.api_key)
    return model_config


def make_model(model_config: AiModelModel, temperature: float, is_reasoning: bool = False) -> Any:
    """按模型配置造 agno 模型对象(含 Anthropic 禁并行工具调用的网关修复)。

    is_reasoning=True 且为 OpenAI 兼容网关时,显式在请求体注入思考开关:这类聚合网关
    (如本兜底的 deepseek-v4-pro)默认「不思考」,思考须 opt-in——经 agno 的 extra_body
    透传到下游 JSON 顶层。实测该网关接受 Anthropic 风格 {"thinking":{"type":"enabled"}}
    (reasoning_effort 被无视、enable_thinking 报 400)。仅在深度思考开启时注入,故
    LLM_REASONING=false / 前端关思考 时 is_reasoning 恒 False → 走默认快模式(首 token 快)。
    """
    # api_key 由调用方解密(DB 模型)或本就明文(环境变量兜底模型)后传入
    model = AiUtil.get_model_from_factory(
        provider=model_config.provider,
        model_code=model_config.model_code,
        model_name=model_config.model_name,
        api_key=model_config.api_key,
        base_url=model_config.base_url,
        temperature=temperature,
        max_tokens=model_config.max_tokens,
    )
    provider = (model_config.provider or '').lower()
    # OpenAI 兼容网关:开思考时显式注入 extra_body(Anthropic 自有 thinking 通道,此处不管)
    if is_reasoning and provider != 'anthropic':
        eb = dict(getattr(model, 'extra_body', None) or {})
        eb.setdefault('thinking', {'type': 'enabled'})
        model.extra_body = eb
    # Anthropic(经网关)在"并行工具调用 + 多个工具结果一次回灌"时,续轮会返回空 → 任务半截
    # 而止("调了两个工具就断")。禁用并行工具调用(强制模型一次只调一个),续轮即正常。
    # 该 tool_choice 形态为 Anthropic 专用;经 request_params 才会真正传到下游。
    if provider == 'anthropic':
        rp = dict(getattr(model, 'request_params', None) or {})
        rp.setdefault('tool_choice', {'type': 'auto', 'disable_parallel_tool_use': True})
        model.request_params = rp
        # agno 2.4.8 仅按 id 前缀白名单判定结构化输出支持(opus 只认 4-1/4-5),
        # 新版 opus-4-8 被误判为不支持 → 长期记忆抽取(用结构化输出)报错。实际支持,这里强制放行。
        model._supports_structured_outputs = lambda: True
        # 省 token:缓存稳定前缀(系统指令 + 工具定义)。每轮重发的大前缀命中缓存,输入费大降。
        # OpenAI 兼容(siliconflow/deepseek 等)是服务端自动前缀缓存,无需在此配置。
        for _attr in ('cache_system_prompt', 'cache_tools'):
            if hasattr(model, _attr):
                setattr(model, _attr, True)
    return model


def assemble_tools(
    artifacts: list | None,
    ui_actions: list | None,
    extra_tools: list | None,
    builtin_codes: list | None,
    kb_tool: Any,
    datasource_scope: list | None,
    datasource_query_enabled: bool,
    skills: list | None = None,
    metrics: list | None = None,
) -> list:
    """装配工具列表(内置工具集 + 知识库工具 + 已连接的 MCP 工具 + 技能加载工具)。供单 agent 与 Team leader/成员共用。

    builtin_codes=None → 全挂(普通对话);否则按所选挂(应用/成员)。code = toolkit 名。
    skills 非空时追加 SkillTools(load_skill),供 agent 按需拉取技能正文。
    """
    from module_ai.tools.data_agent_tools import DataAgentTools
    from module_ai.tools.sandbox_code_tools import SandboxCodeTools
    from module_ai.tools.task_agent_tools import TaskAgentTools

    builtin_map = {
        'data_explore': lambda: DataAgentTools(allowed_codes=datasource_scope, skills=skills),
        'sandbox_code': lambda: SandboxCodeTools(
            artifacts=artifacts, allowed_codes=datasource_scope, enable_datasource=datasource_query_enabled
        ),
        'task_propose': lambda: TaskAgentTools(ui_actions=ui_actions),
        'baidu_search': make_baidu_tools,  # 百度搜索(免鉴权、国内可达)
    }
    codes = list(builtin_map.keys()) if builtin_codes is None else [c for c in builtin_codes if c in builtin_map]
    # 单个内置工具构造失败(如可选依赖未装:baidusearch 等)只跳过并告警,不能让整段对话崩掉。
    tools: list = []
    for c in codes:
        try:
            tools.append(builtin_map[c]())
        except Exception as e:
            logger.warning(f'内置工具 {c} 加载失败,已跳过: {e}')
    if kb_tool is not None:
        tools.append(kb_tool)
    tools.extend(extra_tools or [])
    if skills:
        try:
            from module_ai.tools.skill_tools import SkillTools

            tools.append(SkillTools(skills=skills))
        except Exception as e:
            logger.warning(f'技能工具加载失败,已跳过: {e}')
    # 指标工具:有启用指标才挂(语义层),无则零开销
    if metrics:
        try:
            from module_ai.tools.metric_tools import MetricTools

            tools.append(MetricTools())
        except Exception as e:
            logger.warning(f'指标工具加载失败,已跳过: {e}')
    return tools


def tool_call_kwargs() -> dict:
    """agno 2.8 工具调用旋钮(env 可调,0=不启用,不改既有行为):

    - tool_call_limit:单轮工具调用上限,防弱模型工具暴走循环 / 失控成本;
    - max_tool_calls_from_history:载入上下文的历史工具调用对上限,控长会话 token。
    默认全关;要试就设 LLM_TOOL_CALL_LIMIT / LLM_MAX_TOOL_CALLS_FROM_HISTORY,再用 evals 对拍通过率。
    """
    from config.env import AiConfig

    kw: dict = {}
    if getattr(AiConfig, 'llm_tool_call_limit', 0):
        kw['tool_call_limit'] = int(AiConfig.llm_tool_call_limit)
    if getattr(AiConfig, 'llm_max_tool_calls_from_history', 0):
        kw['max_tool_calls_from_history'] = int(AiConfig.llm_max_tool_calls_from_history)
    return kw


def memory_kwargs(model_config: AiModelModel, enable_memory: bool) -> dict:
    """长期记忆(跨会话、按 user_id 沉淀):开启时返回 agno 记忆参数,否则 {}。

    用一个抽取模型(复用对话模型,温度 0 更稳),每轮后自动从对话抽取用户事实写入 ai_memories,
    并把该用户的记忆注入上下文。关闭时不挂,行为与既有一致。
    """
    if not enable_memory:
        return {}
    from agno.memory import MemoryManager

    # 记忆抽取用小 max_tokens:大 max_tokens(如 128k)会触发 Anthropic「Streaming is required」而失败
    mm_config = model_config.model_copy(update={'max_tokens': 4096})
    mm = MemoryManager(model=make_model(mm_config, 0), db=AiUtil.get_storage_engine())
    return {'memory_manager': mm, 'enable_user_memories': True, 'add_memories_to_context': True}


def build_run_kwargs(chat_req: AiChatRequestModel, user_config: AiChatConfigModel) -> dict[str, Any]:
    """
    构造Agent运行参数

    :param chat_req: 对话请求对象
    :param user_config: 用户配置对象
    :return: 运行参数字典
    """
    run_kwargs: dict[str, Any] = {'stream': True, 'stream_events': True}
    if not chat_req.images or not user_config.vision_enabled:
        return run_kwargs

    processed_images: list[Image] = []
    for img in chat_req.images:
        if img and img.startswith(UploadConfig.UPLOAD_PREFIX):
            relative_path = img[len(UploadConfig.UPLOAD_PREFIX) :]
            if relative_path.startswith('/'):
                relative_path = relative_path[1:]
            file_path = os.path.join(UploadConfig.UPLOAD_PATH, relative_path)
            abs_path = os.path.abspath(file_path)
            if os.path.exists(abs_path):
                processed_images.append(Image(filepath=abs_path))
    run_kwargs['images'] = processed_images
    return run_kwargs


def build_agent(
    model_config: AiModelModel,
    temperature: float,
    system_prompt: str | None,
    user_id: int,
    session_id: str,
    add_history: bool,
    num_history: int,
    artifacts: list | None = None,
    ui_actions: list | None = None,
    extra_tools: list | None = None,
    builtin_codes: list | None = None,
    kb_tool: Any = None,
    instructions: list | None = None,
    datasource_scope: list | None = None,
    datasource_query_enabled: bool = True,
    name: str | None = None,
    agent_id: str = 'chat-agent',
    enable_memory: bool = False,
    skills: list | None = None,
    metrics: list | None = None,
    question: str | None = None,
    is_reasoning: bool = False,
) -> Agent:
    """
    构建对话Agent对象

    builtin_codes: 选用的内置工具集 code(data_explore/sandbox_code/task_propose);None=全部(普通对话)。
    kb_tool: 应用绑定知识库时的检索工具闭包(make_kb_tool 产物),可空。
    extra_tools: 已连接的 MCP 工具实例。

    :param model_config: 模型配置对象
    :param temperature: 对话温度
    :param system_prompt: 系统提示词
    :param user_id: 用户ID
    :param session_id: 会话ID
    :param add_history: 是否附带历史消息
    :param num_history: 历史消息轮数
    :return: Agent对象
    """
    model = make_model(model_config, temperature, is_reasoning)
    storage = AiUtil.get_storage_engine()
    tools = assemble_tools(
        artifacts=artifacts,
        ui_actions=ui_actions,
        extra_tools=extra_tools,
        builtin_codes=builtin_codes,
        kb_tool=kb_tool,
        datasource_scope=datasource_scope,
        datasource_query_enabled=datasource_query_enabled,
        skills=skills,
        metrics=metrics,
    )
    # 普通对话注入数据 agent 工作流指令;并把「精简数据目录」前置进指令(减少 list_datasources 往返)。
    # 应用模式用应用自己的 prompt(instructions 非 None),不注入目录、避免人设被盖。
    from module_ai.tools.data_agent_tools import build_data_catalog

    if instructions is None:
        catalog = build_data_catalog(datasource_scope, question=question)
        agent_instructions = [catalog, *_DATA_AGENT_INSTRUCTIONS] if catalog else list(_DATA_AGENT_INSTRUCTIONS)
    else:
        # 应用模式:保留应用自己的 prompt(人设优先),仅当绑定了数据源时把精简目录追加在后面
        catalog = build_data_catalog(datasource_scope, question=question) if datasource_scope else ''
        agent_instructions = [*instructions, catalog] if catalog else list(instructions)
    # 可用技能清单(Agent Skills 渐进披露 L1):任务匹配时 agent 调 load_skill 拉完整正文
    from module_ai.tools.skill_tools import build_skill_catalog

    skill_catalog = build_skill_catalog(skills)
    if skill_catalog:
        agent_instructions = [*agent_instructions, skill_catalog]
    # 可用指标清单(语义层 L0):命中即用 query_metric 取权威一致的数(有指标才注入,无则零开销)
    from module_ai.tools.metric_tools import build_metric_catalog

    metric_catalog = build_metric_catalog(metrics)
    if metric_catalog:
        agent_instructions = [metric_catalog, *agent_instructions]

    # 稍弱模型:追加"稳妥执行"强化(别跳步/别凭记忆硬写/按工具返回写法调用)
    from ezdata.services.prompts import is_weak_model

    if is_weak_model(getattr(model_config, 'model_code', None)):
        agent_instructions = [*agent_instructions, _WEAK_AGENT_NUDGE]

    # 输入侧护栏(pre_hooks):进 LLM 前拦提示注入 / 高危写操作意图。命中抛 InputCheckError,
    # 由 stream_translator.stream_agent 兜住回友好提示。是输入层防线,与沙箱只读隔离叠加。
    from module_ai.guardrails import build_pre_hooks

    return Agent(
        model=model,
        id=agent_id,
        name=name,
        description=system_prompt or 'You are a helpful AI assistant.',
        instructions=agent_instructions,
        db=storage,
        user_id=str(user_id),
        session_id=session_id,
        add_history_to_context=add_history,
        num_history_runs=num_history,
        tools=tools,
        markdown=True,
        pre_hooks=build_pre_hooks(),
        **memory_kwargs(model_config, enable_memory),
        **tool_call_kwargs(),
    )


def build_team(
    members: list,
    leader_extra_tools: list,
    model_config: AiModelModel,
    temperature: float,
    system_prompt: str | None,
    session_id: str,
    add_history: bool,
    num_history: int,
    artifacts: list,
    ui_actions: list,
    enable_memory: bool = False,
) -> Any:
    """构建多 agent Team:协调者(leader)+ 成员(被引用的应用 agent)。

    leader 保留普通对话的全部内置工具(可自答也可委派);成员各自携带其应用配置的能力。
    stream_member_events=True 使成员的流式事件上抛,前端可实时看到成员干活并按成员归属展示。
    """
    from agno.team import Team

    model = make_model(model_config, temperature)
    storage = AiUtil.get_storage_engine()
    leader_tools = assemble_tools(
        artifacts=artifacts,
        ui_actions=ui_actions,
        extra_tools=leader_extra_tools,
        builtin_codes=None,
        kb_tool=None,
        datasource_scope=None,
        datasource_query_enabled=True,
    )
    instructions = [
        *_DATA_AGENT_INSTRUCTIONS,
        '你是协调者:既可直接回答,也可把子任务委派给团队成员(每个成员是某领域的专家助手)。',
        '当用户需求落在某成员专长时,用 delegate_task_to_member 委派给合适成员;'
        '涉及多个成员时分别委派,最后综合各成员结果给出完整回答。',
    ]
    if (model_config.provider or '').lower() == 'anthropic':
        pass  # leader/成员模型已各自在 make_model 里禁用并行工具调用
    return Team(
        model=model,
        name='主助手',
        members=members,
        tools=leader_tools,
        description=system_prompt or 'You are a helpful AI assistant.',
        instructions=instructions,
        db=storage,
        session_id=session_id,
        add_history_to_context=add_history,
        num_history_runs=num_history,
        markdown=True,
        stream_member_events=True,
        respond_directly=False,
        **memory_kwargs(model_config, enable_memory),
    )
