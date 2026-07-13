import asyncio
import json
import os
import uuid
from collections.abc import AsyncGenerator, AsyncIterator
from datetime import datetime
from typing import TYPE_CHECKING, Any

from agno.agent import Agent
from agno.db.base import SessionType
from agno.media import Image
from agno.run.agent import RunEvent, RunOutput, RunOutputEvent
from agno.run.cancel import acancel_run
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from config.env import UploadConfig
from exceptions.exception import ServiceException
from module_ai.dao.ai_chat_dao import AiChatConfigDao
from module_ai.dao.ai_model_dao import AiModelDao
from module_ai.entity.do.ai_chat_do import AiChatConfig
from module_ai.entity.vo.ai_chat_vo import (
    AgentDataModel,
    AiChatConfigModel,
    AiChatRequestModel,
    AiChatSessionBaseModel,
    AiChatSessionModel,
    ChatMessageModel,
    MessageMetrics,
    SessionDataModel,
    SessionMetricsModel,
)
from module_ai.entity.vo.ai_model_vo import AiModelModel
from utils.ai_util import AiUtil
from utils.common_util import CamelCaseUtil
from utils.crypto_util import CryptoUtil
from utils.log_util import logger

if TYPE_CHECKING:
    from agno.models.message import Message
    from agno.run.team import TeamRunOutput
    from agno.run.workflow import WorkflowRunOutput
    from agno.session import Session


def _short(v: Any, n: int = 300) -> str:
    """转字符串并截断(仅用于过程展示,不影响给 LLM 的内容)。"""
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
    return s if len(s) <= n else s[:n] + '…'


def _short_args(args: Any, n: int = 600) -> Any:
    """工具参数逐值截断(code 等长参数防刷屏)。"""
    if not isinstance(args, dict):
        return _short(args, n)
    return {k: (_short(v, n) if isinstance(v, str) else v) for k, v in args.items()}


# 数据 agent 工作流指令:约束"取数前先查知识库里验证过的解法",让收藏的解法被真正复用。
# 这是工具用法层面的固定规则(由我们提供的工具决定),与用户自定义 system_prompt 叠加生效。
_DATA_AGENT_INSTRUCTIONS: list[str] = [
    '你是 ezdata 的数据分析助手:可发现数据源、查表结构、检索数据源知识库,并在沙箱里跑取数/计算代码、产出结论与图表表格。',
    '取数工作流(务必按序,目标是尽量少绕圈、少调工具):',
    '1. 先看上面「数据源与关键表」目录判断目标数据源编码;目录已能认出源/表时,不要再调 list_datasources。'
    '   仅当目录里没有、或拿不准时,才用 list_datasources 认源。',
    '2. 【关键·先查解法】在写任何取数代码、甚至查表结构之前,先调用 '
    'search_datasource_knowledge(datasource_code, query=用户的原始问题),查该源是否已有”验证过的解法”'
    '(标注 QA 的历史问答,answer 即可直接运行的取数/分析代码):',
    '   - 命中可复用解法:**直接复用、或仅按本次差异微调后运行**,不要从零重写,也不必再逐个 get_table_schema;',
    '   - 未命中:才进入第 3 步自行发现+编写。',
    '3. 没有可用解法时:用 get_table_schema 查清目标表字段/调用参数 → run_datasource_query 编写取数代码。',
    '3.5 【出图优先用 plot_chart】用户要图表时,优先调 plot_chart(datasource_code, native=单条只读查询, chart_type, x, ys, ...):'
    '把聚合做进查询里(SQL→GROUP BY、ES→aggs、Mongo→$group),对应度量的 agg 填 none;'
    '产出的图用户可一键「存为看板」复用。仅当需要复杂多步 pandas 加工时,才改用 run_datasource_query 里 pyecharts 画(那类图仅展示、不可存看板)。',
    '4. 取数/计算成功后正常作答;无需声称”已存入知识库”(由用户点”收藏到知识库”决定)。',
    '一句话:先复用已验证解法,不行再发现现写;能省一轮工具调用就省一轮。',
    '取数注意(尤其 Elasticsearch 源):'
    '① 对文本字段做 terms 聚合/精确匹配/排序,务必用带 .keyword 的子字段(如 industry.keyword),'
    'get_table_schema 已会列出可用的 .keyword 字段,直接用列出的名字,别对 text 主字段聚合(会报错或聚到分词上);'
    '② 取时间序列/明细(如个股日线)务必显式写足 size(如 size:300),ES 默认只回 10 条,否则图表/结论会残缺;'
    '③ 需要 Top-N 时在沙箱代码里排序切片(sorted(...)[:N])后再产出,不要依赖结果摘要去“目测”前几名。',
    '任务管理:用户要「改某个已有任务」(调定时频率、启用/停用、改名)→ find_tasks 搜出 task_id → propose_task_update 弹修改表单;'
    '要「原样复制」→ find_tasks → propose_task_copy;要「照某任务改动代码/配置后新建」→ find_tasks → get_task_detail 看清其代码/配置 → 改好后用对应 '
    'propose_* 新建(代码取数用 propose_code_extract_task);全新任务直接用 propose_data_integration_task/code_extract/python/shell。均只弹表单交用户确认,不擅自落库。',
    '定时 cron 用 **7 段 Quartz**(秒 分 时 日 月 周 年),北京时区(Asia/Shanghai),须与前端 cron 组件完全一致:'
    '① 步进用 `0/N`(从0起每N),**不要用 `*/N`**(组件会解析成 NaN);② 星期**只用数字**,Quartz 约定 周日=1..周六=7(周一到周五=2-6,别用 MON-FRI 名称、别用 0);'
    '③ 年固定写 `*`;④ 日与星期二选一,定了星期则"日"写 ?。'
    '例:每20分钟 `0 0/20 * * * ? *`;每天8点 `0 0 8 * * ? *`;交易时段(周一到周五9-15点)每5分钟 `0 0/5 9-15 ? * 2-6 *`。',
]

# 用户可在「工具」下拉里自选、按需挂载的内置工具集 code(其余内置工具由平台按能力自动挂载:
# data_explore/sandbox_code 由「数据分析」数据源选择控制,不在此白名单)。
_PASSTHROUGH_BUILTIN = {'task_propose', 'baidu_search'}


def _make_baidu_tools() -> Any:
    """百度搜索工具集(懒加载:缺依赖时仅此工具不可用,不影响其它工具装配)。"""
    from agno.tools.baidusearch import BaiduSearchTools

    return BaiduSearchTools()


class AiChatService:
    """
    AI对话服务层
    """

    @classmethod
    def _resolve_temperature(cls, user_config: AiChatConfigModel, model_config: AiModelModel) -> float:
        """
        解析温度配置，优先级为 用户配置 > 模型配置

        :param user_config: 用户配置对象
        :param model_config: 模型配置对象
        :return: 解析后的温度值
        """
        temperature = user_config.temperature or model_config.temperature
        return temperature

    @classmethod
    def _resolve_is_reasoning(cls, chat_req: AiChatRequestModel, model_config: AiModelModel) -> bool:
        """
        解析深度思考开关，结合请求参数与模型配置确定最终是否开启

        :param chat_req: 对话请求对象
        :param model_config: 模型配置对象
        :return: 是否开启深度思考
        """
        if model_config.support_reasoning != 'Y':
            return False
        return bool(chat_req.is_reasoning)

    @classmethod
    def _resolve_history_config(cls, user_config: AiChatConfigModel) -> tuple[bool, int]:
        """
        解析历史消息配置，确定是否附带历史以及轮数

        :param user_config: 用户配置对象
        :return: (是否附带历史, 历史轮数)
        """
        add_history = user_config.add_history_to_context == '0'
        # 默认历史轮数由 10 降到 5:取数会话大部分价值在当前任务,过多历史(含肥工具结果)每轮重发很费 token。
        # 用户仍可在对话设置里自行调高。
        num_history = user_config.num_history_runs or 5

        return bool(add_history), int(num_history)

    @staticmethod
    def _rebuild_blocks(m: 'Message', tool_results: dict[str, Any]) -> list[dict] | None:
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

    @classmethod
    async def _resolve_chat_model_config(cls, query_db: AsyncSession, model_id: int) -> AiModelModel:
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

    @classmethod
    def _build_agent(
        cls,
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
        model = cls._make_model(model_config, temperature)
        storage = AiUtil.get_storage_engine()
        tools = cls._assemble_tools(
            artifacts=artifacts,
            ui_actions=ui_actions,
            extra_tools=extra_tools,
            builtin_codes=builtin_codes,
            kb_tool=kb_tool,
            datasource_scope=datasource_scope,
            datasource_query_enabled=datasource_query_enabled,
        )
        # 普通对话注入数据 agent 工作流指令;并把「精简数据目录」前置进指令(减少 list_datasources 往返)。
        # 应用模式用应用自己的 prompt(instructions 非 None),不注入目录、避免人设被盖。
        from module_ai.tools.data_agent_tools import build_data_catalog

        if instructions is None:
            catalog = build_data_catalog(datasource_scope)
            agent_instructions = [catalog, *_DATA_AGENT_INSTRUCTIONS] if catalog else _DATA_AGENT_INSTRUCTIONS
        else:
            # 应用模式:保留应用自己的 prompt(人设优先),仅当绑定了数据源时把精简目录追加在后面
            catalog = build_data_catalog(datasource_scope) if datasource_scope else ''
            agent_instructions = [*instructions, catalog] if catalog else instructions

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
            **cls._memory_kwargs(model_config, enable_memory),
        )

    @classmethod
    def _memory_kwargs(cls, model_config: AiModelModel, enable_memory: bool) -> dict:
        """长期记忆(跨会话、按 user_id 沉淀):开启时返回 agno 记忆参数,否则 {}。

        用一个抽取模型(复用对话模型,温度 0 更稳),每轮后自动从对话抽取用户事实写入 ai_memories,
        并把该用户的记忆注入上下文。关闭时不挂,行为与既有一致。
        """
        if not enable_memory:
            return {}
        from agno.memory import MemoryManager

        # 记忆抽取用小 max_tokens:大 max_tokens(如 128k)会触发 Anthropic「Streaming is required」而失败
        mm_config = model_config.model_copy(update={'max_tokens': 4096})
        mm = MemoryManager(model=cls._make_model(mm_config, 0), db=AiUtil.get_storage_engine())
        return {'memory_manager': mm, 'enable_user_memories': True, 'add_memories_to_context': True}

    @classmethod
    def _make_model(cls, model_config: AiModelModel, temperature: float) -> Any:
        """按模型配置造 agno 模型对象(含 Anthropic 禁并行工具调用的网关修复)。"""
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
        # Anthropic(经网关)在"并行工具调用 + 多个工具结果一次回灌"时,续轮会返回空 → 任务半截
        # 而止("调了两个工具就断")。禁用并行工具调用(强制模型一次只调一个),续轮即正常。
        # 该 tool_choice 形态为 Anthropic 专用;经 request_params 才会真正传到下游。
        if (model_config.provider or '').lower() == 'anthropic':
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

    @classmethod
    def _assemble_tools(
        cls,
        artifacts: list | None,
        ui_actions: list | None,
        extra_tools: list | None,
        builtin_codes: list | None,
        kb_tool: Any,
        datasource_scope: list | None,
        datasource_query_enabled: bool,
    ) -> list:
        """装配工具列表(内置工具集 + 知识库工具 + 已连接的 MCP 工具)。供单 agent 与 Team leader/成员共用。

        builtin_codes=None → 全挂(普通对话);否则按所选挂(应用/成员)。code = toolkit 名。
        """
        from module_ai.tools.data_agent_tools import DataAgentTools
        from module_ai.tools.sandbox_code_tools import SandboxCodeTools
        from module_ai.tools.task_agent_tools import TaskAgentTools

        builtin_map = {
            'data_explore': lambda: DataAgentTools(allowed_codes=datasource_scope),
            'sandbox_code': lambda: SandboxCodeTools(
                artifacts=artifacts, allowed_codes=datasource_scope, enable_datasource=datasource_query_enabled
            ),
            'task_propose': lambda: TaskAgentTools(ui_actions=ui_actions),
            'baidu_search': _make_baidu_tools,  # 百度搜索(免鉴权、国内可达)
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
        return tools

    @classmethod
    def _build_team(
        cls,
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

        model = cls._make_model(model_config, temperature)
        storage = AiUtil.get_storage_engine()
        leader_tools = cls._assemble_tools(
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
            pass  # leader/成员模型已各自在 _make_model 里禁用并行工具调用
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
            **cls._memory_kwargs(model_config, enable_memory),
        )

    @classmethod
    def _build_run_kwargs(
        cls,
        chat_req: AiChatRequestModel,
        user_config: AiChatConfigModel,
    ) -> dict[str, Any]:
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

    @classmethod
    def _convert_images_to_upload_paths(cls, images: list[Image] | None) -> list[str] | None:
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

    @classmethod
    async def _stream_agent(
        cls,
        agent: Agent,
        chat_req: AiChatRequestModel,
        run_kwargs: dict[str, Any],
        is_reasoning: bool,
        session_id: str,
        artifacts: list | None = None,
        ui_actions: list | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        将Agent输出流式转换为前端SSE消息

        :param agent: Agent实例
        :param chat_req: 对话请求对象
        :param run_kwargs: 运行参数字典
        :param is_reasoning: 是否输出推理内容
        :param session_id: 会话ID
        :return: SSE消息生成器
        """
        full_response = ''
        full_reasoning = ''
        arts = artifacts if artifacts is not None else []
        emitted = 0  # 已发出的产物游标
        acts = ui_actions if ui_actions is not None else []
        acts_emitted = 0  # 已发出的任务提议(ui_action)游标
        try:
            yield json.dumps({'session_id': session_id, 'type': 'meta'}) + '\n'

            response_stream: AsyncIterator[RunOutputEvent] = agent.arun(chat_req.message, **run_kwargs)

            async for chunk in response_stream:
                content = None
                reasoning = None

                # 事件归一:Team 的 leader 事件值带 "Team" 前缀(TeamRunContent…),成员(普通 Agent)事件不带。
                # 去前缀后按 RunEvent 值比对,使 Team 与单 Agent 共用同一套处理。
                ev = chunk.event
                ev_str = ev.value if hasattr(ev, 'value') else str(ev)
                base = ev_str[4:] if ev_str.startswith('Team') else ev_str
                # 成员归属:非 Team 前缀且带 agent_name 的事件来自某成员(多 agent 时),用于前端"谁在说"标签;
                # 单 agent 模式 leader 无 name → agent_name 为空,不影响既有行为。
                member = None if ev_str.startswith('Team') else getattr(chunk, 'agent_name', None)

                def _with_member(d: dict) -> dict:
                    if member:
                        d['agentName'] = member
                    return d

                if base == RunEvent.run_started.value and chunk.run_id:
                    yield json.dumps({'run_id': chunk.run_id, 'type': 'run_info'}) + '\n'

                # 工具调用过程(可观测):转发 start/end/error,前端渲染"执行过程"时间线
                tl = getattr(chunk, 'tool', None)
                if tl is not None:
                    if base == RunEvent.tool_call_started.value:
                        yield (
                            json.dumps(
                                _with_member(
                                    {
                                        'type': 'tool',
                                        'phase': 'start',
                                        'id': tl.tool_call_id,
                                        'name': tl.tool_name,
                                        'args': _short_args(tl.tool_args),
                                    }
                                ),
                                ensure_ascii=False,
                            )
                            + '\n'
                        )
                    elif base == RunEvent.tool_call_completed.value:
                        yield (
                            json.dumps(
                                _with_member(
                                    {
                                        'type': 'tool',
                                        'phase': 'end',
                                        'id': tl.tool_call_id,
                                        'name': tl.tool_name,
                                        'result': _short(tl.result, 300),
                                    }
                                ),
                                ensure_ascii=False,
                            )
                            + '\n'
                        )
                    elif base == RunEvent.tool_call_error.value:
                        yield (
                            json.dumps(
                                _with_member(
                                    {
                                        'type': 'tool',
                                        'phase': 'error',
                                        'id': tl.tool_call_id,
                                        'name': tl.tool_name,
                                        'error': _short(tl.tool_call_error or tl.result, 300),
                                    }
                                ),
                                ensure_ascii=False,
                            )
                            + '\n'
                        )

                if base == RunEvent.run_content.value:
                    content = chunk.content
                    if hasattr(chunk, 'reasoning_content') and chunk.reasoning_content:
                        reasoning = chunk.reasoning_content

                if reasoning and is_reasoning:
                    full_reasoning += reasoning
                    yield json.dumps({'content': reasoning, 'type': 'reasoning'}) + '\n'

                # 仅在最外层 Team/Agent 完成时报指标(成员完成不报,避免多次)
                if base == RunEvent.run_completed.value and not member and getattr(chunk, 'metrics', None):
                    yield (
                        json.dumps(
                            {'metrics': CamelCaseUtil.transform_result(chunk.metrics.to_dict()), 'type': 'metrics'}
                        )
                        + '\n'
                    )

                if content:
                    full_response += content
                    yield json.dumps(_with_member({'content': content, 'type': 'content'}), ensure_ascii=False) + '\n'

                # 增量排空结构化产物(图表/表格):工具产出后即推给前端渲染
                while emitted < len(arts):
                    yield json.dumps({'artifact': arts[emitted], 'type': 'artifact'}, ensure_ascii=False) + '\n'
                    emitted += 1

                # 增量排空任务提议(ui_action):工具产出后即推给前端渲染成确认表单卡片
                while acts_emitted < len(acts):
                    yield json.dumps({'action': acts[acts_emitted], 'type': 'ui_action'}, ensure_ascii=False) + '\n'
                    acts_emitted += 1

            # 兜底:最后一次工具调用后(run_completed 之后)产生的产物 / 提议
            while emitted < len(arts):
                yield json.dumps({'artifact': arts[emitted], 'type': 'artifact'}, ensure_ascii=False) + '\n'
                emitted += 1
            while acts_emitted < len(acts):
                yield json.dumps({'action': acts[acts_emitted], 'type': 'ui_action'}, ensure_ascii=False) + '\n'
                acts_emitted += 1
        except Exception as e:
            yield json.dumps({'error': str(e), 'type': 'error'}) + '\n'

    @classmethod
    async def chat_services(
        cls,
        query_db: AsyncSession,
        chat_req: AiChatRequestModel,
        user_id: int,
        app_config_override: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话

        :param query_db: orm对象
        :param chat_req: 对话请求对象
        :param user_id: 用户ID
        :return: 对话响应流
        """
        model_config = await cls._resolve_chat_model_config(query_db, chat_req.model_id)

        user_config = await cls.ai_chat_config_detail_services(query_db, user_id)

        session_id = chat_req.session_id
        if not session_id:
            session_id = str(uuid.uuid4())

        temperature = cls._resolve_temperature(user_config, model_config)
        is_reasoning = cls._resolve_is_reasoning(chat_req, model_config)
        add_history, num_history = cls._resolve_history_config(user_config)
        enable_memory = getattr(user_config, 'enable_memory', '1') == '0'  # 长期记忆开关(0=开),应用模式不启用
        system_prompt = user_config.system_prompt

        # —— AI 应用模式:带 app_id 时按应用配置覆盖(提示词/模型/参数/工具/知识库)——
        builtin_codes: list | None = None  # None=全部内置工具(普通对话)
        kb_tool = None
        mcp_configs: list[dict] = []
        app_instructions: list | None = None  # 应用模式置 [],用应用 prompt 作系统,不注入数据 agent 指令
        datasource_scope: list | None = None  # 应用「数据分析」选定的数据源;限定数据工具范围
        datasource_query_enabled = True  # 普通对话默认开放取数;应用模式按是否选了数据源决定
        app_cfg = None
        if app_config_override is not None:
            app_cfg = app_config_override  # 调试:用前端草稿配置(免保存)
        elif getattr(chat_req, 'app_id', None):
            from module_ai.service.ai_app_service import AiAppService

            app_cfg = await AiAppService.get_app_config(query_db, chat_req.app_id)
        if app_cfg:
            enable_memory = bool(app_cfg.get('enableMemory'))  # 应用自带的长期记忆开关(仍按 user_id 隔离)
            # 应用自带的上下文历史配置:覆盖调用者对话设置,使同一应用对所有用户/对外API行为一致
            add_history = bool(app_cfg.get('addHistory', True))
            num_history = int(app_cfg.get('numHistoryRuns') or 10)
            app_instructions = []  # 应用模式:仅用应用 prompt 作系统提示,不叠加数据 agent 工作流指令
            if (app_cfg.get('prompt') or '').strip():
                system_prompt = app_cfg['prompt']
            m = app_cfg.get('model') or {}
            if m.get('modelId') is not None:
                model_config = await cls._resolve_chat_model_config(query_db, m.get('modelId') or 0)
            if m.get('temperature') is not None:
                temperature = m['temperature']
            if m.get('maxTokens'):
                model_config.max_tokens = m['maxTokens']
            from module_ai.service.ai_tool_service import AiToolService

            resolved = await AiToolService.resolve_app_tools(query_db, app_cfg.get('toolIds') or [])
            # 工具区透传用户自选内置工具(task_propose/baidu_search…);sandbox_code 始终挂
            # (run_python_code 计算/绘图不碰数据源),但取数/数据探索由「数据分析」数据源选择控制。
            builtin_codes = [c for c in resolved['builtin_codes'] if c in _PASSTHROUGH_BUILTIN]
            builtin_codes = builtin_codes + ['sandbox_code']
            mcp_configs = resolved['mcp_configs']
            ds_codes = app_cfg.get('datasourceCodes') or []
            datasource_query_enabled = bool(ds_codes)
            if ds_codes:  # 选了数据源才开放数据探索/取数,且限定在所选源内
                builtin_codes = builtin_codes + ['data_explore']
                datasource_scope = ds_codes
            dsids = app_cfg.get('datasetIds') or []
            if dsids:
                from common.context import RequestContext
                from module_rag.agent_tools import make_kb_tool

                kb_tool = make_kb_tool(dataset_ids=dsids, tenant_id=RequestContext.get_effective_tenant_id())
        member_specs: list[dict] = []  # 多 agent:引用的应用作为 Team 成员的装配规格
        if not app_cfg:
            # 普通对话:MCP 工具来自用户对话设置
            mcp_configs = await cls._load_mcp_configs(query_db, user_config)
            # 多 agent:用户在对话设置里引用的应用 → 解析成 Team 成员
            for aid in cls._load_agent_app_ids(user_config):
                spec = await cls._resolve_app_agent_spec(query_db, aid, user_id, session_id, temperature)
                if spec:
                    member_specs.append(spec)

        artifacts: list = []  # 工具(沙箱)产出的图表/表格收集器,经 _stream_agent 推给前端渲染
        ui_actions: list = []  # 任务提议(确认表单)收集器,经 _stream_agent 推给前端渲染成卡片
        run_kwargs = cls._build_run_kwargs(chat_req, user_config)

        build_kwargs = dict(
            model_config=model_config,
            temperature=temperature,
            system_prompt=system_prompt,
            user_id=user_id,
            session_id=session_id,
            add_history=add_history,
            num_history=num_history,
            builtin_codes=builtin_codes,
            kb_tool=kb_tool,
            instructions=app_instructions,
            datasource_scope=datasource_scope,
            datasource_query_enabled=datasource_query_enabled,
            enable_memory=enable_memory,
        )
        stream_kwargs = dict(
            chat_req=chat_req,
            run_kwargs=run_kwargs,
            is_reasoning=is_reasoning,
            session_id=session_id,
            artifacts=artifacts,
            ui_actions=ui_actions,
        )

        # MCP 汇聚:主对话自身 + 所有成员应用的 MCP 配置,按 code 去重后一次性连接,再按 code 分发。
        # (MCP 连接须在同一 task 的 cancel scope 内,不能在成员运行中途现连)
        leader_mcp_codes = {c['code'] for c in mcp_configs}
        all_mcp_configs: list[dict] = list(mcp_configs)
        for spec in member_specs:
            all_mcp_configs += spec['mcp_configs']
        seen_codes: set = set()
        deduped_mcp: list[dict] = []
        for c in all_mcp_configs:
            if c['code'] in seen_codes:
                continue
            seen_codes.add(c['code'])
            deduped_mcp.append(c)
        all_mcp_configs = deduped_mcp

        def _runnable(extra_tools: list | None):
            """按已连接的 MCP 工具(带 _ezdata_code)装配可运行对象:无成员→单 Agent;有成员→Team。"""
            extra_tools = extra_tools or []
            if not member_specs:
                return cls._build_agent(
                    artifacts=artifacts, ui_actions=ui_actions, extra_tools=extra_tools, **build_kwargs
                )
            by = lambda codes: [t for t in extra_tools if getattr(t, '_ezdata_code', None) in codes]  # noqa: E731
            members = [
                cls._build_agent(
                    artifacts=artifacts,
                    ui_actions=ui_actions,
                    extra_tools=by({c['code'] for c in spec['mcp_configs']}),
                    **spec['build_kwargs'],
                )
                for spec in member_specs
            ]
            return cls._build_team(
                members=members,
                leader_extra_tools=by(leader_mcp_codes),
                model_config=model_config,
                temperature=temperature,
                system_prompt=system_prompt,
                session_id=session_id,
                add_history=add_history,
                num_history=num_history,
                artifacts=artifacts,
                ui_actions=ui_actions,
                enable_memory=enable_memory,
            )

        if not all_mcp_configs:
            # 无 MCP:直连路径(单 agent 保持既有行为不变;有成员则直接组 Team)
            async for chunk in cls._stream_agent(agent=_runnable([]), **stream_kwargs):
                yield chunk
            return

        # 有 MCP:在独立 worker task 内连 MCP + 跑 agent/Team,队列桥接给本生成器。
        # MCPTools 基于 anyio cancel scope,其进入/退出必须在同一 task;放进 worker 可避免与
        # 请求 DB 会话/生成器收尾跨 task 冲突("exit cancel scope in a different task")。
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        sentinel = object()

        async def _run_with_tools(extra_tools: list) -> None:
            async for chunk in cls._stream_agent(agent=_runnable(extra_tools), **stream_kwargs):
                await queue.put(chunk)

        async def _worker() -> None:
            try:
                logger.info(
                    f'[MCP worker] 启动,选中 {len(all_mcp_configs)} 个 MCP 工具,{len(member_specs)} 个成员 agent'
                )
                await cls._with_mcp_tools(all_mcp_configs, [], _run_with_tools)
                logger.info('[MCP worker] 正常结束')
            except Exception as e:
                logger.exception(f'[MCP worker] 异常: {e}')
                await queue.put(json.dumps({'error': str(e), 'type': 'error'}, ensure_ascii=False) + '\n')
            finally:
                await queue.put(sentinel)

        task = asyncio.create_task(_worker())
        emitted = 0
        stuck = False
        idle_timeout = 120  # 秒:超过此时长无任何输出则判定卡住(MCP/模型无响应),中断并报错而非冻结
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(queue.get(), timeout=idle_timeout)
                except asyncio.TimeoutError:
                    stuck = True
                    logger.warning(f'[MCP worker] {idle_timeout}s 无输出,判定卡住,中断(已输出 {emitted} 段)')
                    yield (
                        json.dumps(
                            {
                                'error': f'工具调用 {idle_timeout}s 无响应,已中断(可能是 MCP 服务或模型卡住,请重试或减少所选工具)',
                                'type': 'error',
                            },
                            ensure_ascii=False,
                        )
                        + '\n'
                    )
                    break
                if chunk is sentinel:
                    break
                emitted += 1
                yield chunk
            if not stuck:  # 正常结束:等 worker 收尾(它已 put sentinel,很快完成)
                await task
                logger.info(f'[MCP worker] 生成器完成,共输出 {emitted} 段')
        finally:
            if not task.done():
                logger.warning(f'[MCP worker] worker 未结束(已输出 {emitted} 段),取消')
                task.cancel()
                try:
                    await task
                except BaseException:
                    pass

    @classmethod
    def _load_agent_app_ids(cls, user_config: AiChatConfigModel) -> list[int]:
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

    @classmethod
    async def _resolve_app_agent_spec(
        cls,
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
        model_config = await cls._resolve_chat_model_config(query_db, m.get('modelId') or 0)
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
        )
        return {'build_kwargs': build_kwargs, 'mcp_configs': mcp_configs}

    @classmethod
    async def _load_mcp_configs(cls, query_db: AsyncSession, user_config: AiChatConfigModel) -> list[dict]:
        """按用户配置 mcp_tool_ids 取启用的 MCP 工具配置(只读 DB,不建连接)。"""
        raw = (getattr(user_config, 'mcp_tool_ids', None) or '').strip()
        if not raw:
            return []
        try:
            ids = [int(x) for x in raw.split(',') if x.strip()]
        except ValueError:
            return []
        from module_ai.service.ai_tool_service import AiToolService

        return await AiToolService.get_enabled_mcp_tools_by_ids(query_db, ids)

    @classmethod
    async def _with_mcp_tools(cls, configs: list[dict], connected: list, cb: Any) -> None:
        """递归地用**直接 async with** 逐个连上 MCP server,全部进入后在最内层调 cb(connected)。

        为何递归而非 AsyncExitStack:agno MCPTools 基于 anyio,经 AsyncExitStack 退出时
        stdio_client 的 cancel scope 会"跨 task"报错;直接嵌套 async with 进出都在本 task,稳。
        单个连接失败则跳过该工具、继续其余(已连的保持在外层 async with 帧内)。
        """
        if not configs:
            await cb(connected)
            return
        try:
            from agno.tools.mcp import MCPTools
        except Exception as e:
            logger.warning(f'MCP 依赖未安装,跳过 MCP 工具装配: {e}')
            await cb(connected)
            return
        from module_ai.service.ai_tool_service import AiToolService

        cfg, rest = configs[0], configs[1:]
        try:
            kwargs = AiToolService.build_mcp_kwargs(cfg['args'])
        except Exception as e:
            logger.warning(f'MCP 工具配置无效,跳过 {cfg.get("code")}: {e}')
            await cls._with_mcp_tools(rest, connected, cb)
            return
        try:
            async with MCPTools(**kwargs) as t:
                logger.info(f'MCP 工具已连接: {cfg["code"]} ({len(getattr(t, "functions", None) or {})} 个方法)')
                t._ezdata_code = cfg['code']  # 标记来源 code,便于多 agent 时按应用分发
                await cls._with_mcp_tools(rest, [*connected, t], cb)
        except Exception as e:
            logger.warning(f'MCP 工具连接失败,跳过 {cfg["code"]}: {e}')
            await cls._with_mcp_tools(rest, connected, cb)

    @classmethod
    async def ai_chat_config_detail_services(cls, query_db: AsyncSession, user_id: int) -> AiChatConfigModel:
        """
        获取用户配置

        :param query_db: orm对象
        :param user_id: 用户ID
        :return: 配置模型
        """
        chat_config = await AiChatConfigDao.get_chat_config_detail_by_user_id(query_db, user_id)
        result = AiChatConfigModel(**CamelCaseUtil.transform_result(chat_config)) if chat_config else AiChatConfig()

        return result

    @classmethod
    async def save_ai_chat_config_services(
        cls, query_db: AsyncSession, user_id: int, page_object: AiChatConfigModel
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

    @classmethod
    async def get_chat_session_list_services(
        cls, user_id: int, app_id: str | None = None
    ) -> list[AiChatSessionBaseModel]:
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

    @classmethod
    async def delete_chat_session_services(cls, session_id: str) -> CrudResponseModel:
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

    @classmethod
    async def get_chat_session_detail_services(cls, session_id: str) -> AiChatSessionModel:
        """
        获取会话消息详情

        :param session_id: 会话ID
        :return: 会话消息详情
        """
        storage = AiUtil.get_storage_engine()
        session: Session | None = await storage.get_session(session_id=session_id, session_type=SessionType.AGENT)

        if not session:
            raise ServiceException(message='会话不存在')

        session_data: dict[str, Any] = session.session_data
        agent_data: dict[str, Any] = session.agent_data
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
                    images=cls._convert_images_to_upload_paths(m.images),
                    metrics=metrics_model,
                    createdAt=datetime.fromtimestamp(m.created_at) if m.created_at else None,
                    reasoningContent=m.reasoning_content,
                    fromHistory=m.from_history,
                    stopAfterToolCall=m.stop_after_tool_call,
                    blocks=cls._rebuild_blocks(m, tool_results) if m.role == 'assistant' else None,
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
                    **CamelCaseUtil.transform_result(session_data.get('session_metrics'))
                ),
            ),
            agentData=AgentDataModel(**CamelCaseUtil.transform_result(agent_data)),
            messages=chat_messages,
        )

        return session_detail

    @classmethod
    async def cancel_run_services(cls, run_id: str) -> CrudResponseModel:
        """
        取消运行

        :param run_id: 运行ID
        :return: 取消结果
        """
        cancel_result = await acancel_run(run_id)
        if not cancel_result:
            raise ServiceException(message='取消运行失败')
        return CrudResponseModel(is_success=True, message='取消成功')

    @classmethod
    async def save_recipe_services(
        cls, query_db: AsyncSession, session_id: str, tool_call_id: str, operator: str
    ) -> dict:
        """把某次成功的取数调用(全量 code + 触发问题)存进该数据源专属知识库,作为带星 QA 解法。

        全量 code 从 agno 持久化的会话(ai_sessions)里按 tool_call_id 回查(流式事件里的 code 被截断,
        不能用)。下次同问 → retrieval 的 QA 精确命中直接返回这段 code。
        """
        storage = AiUtil.get_storage_engine()
        session: Session | None = await storage.get_session(session_id=session_id, session_type=SessionType.AGENT)
        if not session:
            raise ServiceException(message='会话不存在')

        # 在所有 run 里按 tool_call_id 找那次工具调用,顺带取该 run 的用户问题
        found_args: dict | None = None
        question: str = ''
        for run in session.runs or []:
            for t in getattr(run, 'tools', None) or []:
                if getattr(t, 'tool_call_id', None) == tool_call_id:
                    found_args = getattr(t, 'tool_args', None) or {}
                    question = (getattr(getattr(run, 'input', None), 'input_content', None) or '').strip()
                    break
            if found_args is not None:
                break
        if found_args is None:
            raise ServiceException(message='未找到该工具调用(请等本轮回答结束后再收藏)')

        code = (found_args.get('code') or '').strip()
        datasource_code = (found_args.get('datasource_code') or '').strip()
        if not (code and datasource_code):
            raise ServiceException(message='该调用不是数据源取数(无 code/数据源),暂不支持收藏')
        if not question:
            raise ServiceException(message='未取到本轮问题,无法作为解法收藏')

        from module_rag.entity.vo.rag_vo import ChunkSaveReq
        from module_rag.service.chunk_service import ChunkService
        from module_rag.service.dataset_service import DatasetService

        ds = await DatasetService.ensure_for_source(query_db, None, datasource_code, operator)
        dataset_id = ds['id']
        saved = await ChunkService.save(
            query_db,
            ChunkSaveReq(datasetId=dataset_id, chunkType='qa', question=question, answer=code),
            operator,
        )
        chunk_id = saved['id']
        await ChunkService.star(query_db, chunk_id, 1)
        return {
            'chunkId': chunk_id,
            'datasetName': ds.get('name'),
            'datasourceCode': datasource_code,
            'question': question,
        }

