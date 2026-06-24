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
    '取数工作流(务必按序遵守):',
    '1. 用 list_datasources / get_table_schema 认清目标数据源编码与表结构。',
    '2. 【关键】在写任何取数代码之前,先调用 search_datasource_knowledge(datasource_code, query=用户的原始问题),'
    '查该数据源是否已有“验证过的解法”(标注为 QA 的历史问答,answer 即可直接运行的取数/分析代码)。',
    '   - 若检索结果里有可复用的解法代码:**优先直接复用它、或仅按本次差异微调**,不要从零重写;',
    '   - 仅当没有可用解法时,才用 run_datasource_query 自行编写取数代码。',
    '3. 取数/计算成功后正常作答;无需主动声称“已存入知识库”(由用户点“收藏到知识库”决定)。',
    '即:能复用知识库里已验证的解法时,绝不重复造轮子。',
]


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
        num_history = user_config.num_history_runs or 10

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
        for tc in (getattr(m, 'tool_calls', None) or []):
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
            blocks.append({'type': 'tool', 'id': tc_id, 'name': name, 'args': args,
                           'status': 'error' if err else 'done', 'result': result})
        return blocks or None

    @classmethod
    async def _resolve_chat_model_config(cls, query_db: AsyncSession, model_id: int) -> AiModelModel:
        """解析对话模型配置,返回 api_key 已为明文的 AiModelModel。

        model_id == 0 走环境变量兜底模型(AiConfig/LLM_*,api_key 明文);
        否则查库内模型并解密 api_key。
        """
        if model_id == 0:
            from config.env import AiConfig  # noqa: PLC0415

            if not AiConfig.enabled:
                raise ServiceException(
                    message='未配置兜底模型:请在「AI 模型管理」启用一个对话模型,或配置环境变量 LLM_TYPE/LLM_MODEL/LLM_API_KEY')
            return AiModelModel(
                modelId=0, provider=AiConfig.provider, modelCode=AiConfig.llm_model,
                apiKey=AiConfig.llm_api_key, baseUrl=AiConfig.llm_url or None,
                maxTokens=AiConfig.llm_max_tokens, supportReasoning='N', supportImages='N',
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
    ) -> Agent:
        """
        构建对话Agent对象

        :param model_config: 模型配置对象
        :param temperature: 对话温度
        :param system_prompt: 系统提示词
        :param user_id: 用户ID
        :param session_id: 会话ID
        :param add_history: 是否附带历史消息
        :param num_history: 历史消息轮数
        :return: Agent对象
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
        # Anthropic(经网关)在"并行工具调用 + 多个工具结果一次回灌"时,续轮会返回空 → 任务半截
        # 而止("调了两个工具就断")。禁用并行工具调用(强制模型一次只调一个),续轮即正常。
        # 该 tool_choice 形态为 Anthropic 专用;经 request_params 才会真正传到下游。
        if (model_config.provider or '').lower() == 'anthropic':
            rp = dict(getattr(model, 'request_params', None) or {})
            rp.setdefault('tool_choice', {'type': 'auto', 'disable_parallel_tool_use': True})
            model.request_params = rp
        storage = AiUtil.get_storage_engine()
        # 数据 agent 工具:探索(发现数据源/表结构/知识库) + 执行(沙箱跑 python 计算/取数)
        # 如需关闭,去掉 tools 参数即可
        from module_ai.tools.data_agent_tools import DataAgentTools  # noqa: PLC0415
        from module_ai.tools.sandbox_code_tools import SandboxCodeTools  # noqa: PLC0415
        from module_ai.tools.task_agent_tools import TaskAgentTools  # noqa: PLC0415

        return Agent(
            model=model,
            id='chat-agent',
            description=system_prompt or 'You are a helpful AI assistant.',
            instructions=_DATA_AGENT_INSTRUCTIONS,
            db=storage,
            user_id=str(user_id),
            session_id=session_id,
            add_history_to_context=add_history,
            num_history_runs=num_history,
            tools=[DataAgentTools(), SandboxCodeTools(artifacts=artifacts),
                   TaskAgentTools(ui_actions=ui_actions), *(extra_tools or [])],
            markdown=True,
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

                if chunk.event == RunEvent.run_started and chunk.run_id:
                    yield json.dumps({'run_id': chunk.run_id, 'type': 'run_info'}) + '\n'

                # 工具调用过程(可观测):转发 start/end/error,前端渲染"执行过程"时间线
                tl = getattr(chunk, 'tool', None)
                if tl is not None:
                    if chunk.event == RunEvent.tool_call_started:
                        yield json.dumps({'type': 'tool', 'phase': 'start', 'id': tl.tool_call_id,
                                          'name': tl.tool_name, 'args': _short_args(tl.tool_args)},
                                         ensure_ascii=False) + '\n'
                    elif chunk.event == RunEvent.tool_call_completed:
                        yield json.dumps({'type': 'tool', 'phase': 'end', 'id': tl.tool_call_id,
                                          'name': tl.tool_name, 'result': _short(tl.result, 300)},
                                         ensure_ascii=False) + '\n'
                    elif chunk.event == RunEvent.tool_call_error:
                        yield json.dumps({'type': 'tool', 'phase': 'error', 'id': tl.tool_call_id,
                                          'name': tl.tool_name, 'error': _short(tl.tool_call_error or tl.result, 300)},
                                         ensure_ascii=False) + '\n'

                if chunk.event == RunEvent.run_content:
                    content = chunk.content
                    if hasattr(chunk, 'reasoning_content') and chunk.reasoning_content:
                        reasoning = chunk.reasoning_content

                if reasoning and is_reasoning:
                    full_reasoning += reasoning
                    yield json.dumps({'content': reasoning, 'type': 'reasoning'}) + '\n'

                if chunk.event == RunEvent.run_completed and chunk.metrics:
                    yield (
                        json.dumps(
                            {'metrics': CamelCaseUtil.transform_result(chunk.metrics.to_dict()), 'type': 'metrics'}
                        )
                        + '\n'
                    )

                if content:
                    full_response += content
                    yield json.dumps({'content': content, 'type': 'content'}) + '\n'

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
        cls, query_db: AsyncSession, chat_req: AiChatRequestModel, user_id: int
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
        system_prompt = user_config.system_prompt

        artifacts: list = []  # 工具(沙箱)产出的图表/表格收集器,经 _stream_agent 推给前端渲染
        ui_actions: list = []  # 任务提议(确认表单)收集器,经 _stream_agent 推给前端渲染成卡片
        run_kwargs = cls._build_run_kwargs(chat_req, user_config)

        build_kwargs = dict(
            model_config=model_config, temperature=temperature, system_prompt=system_prompt,
            user_id=user_id, session_id=session_id, add_history=add_history, num_history=num_history,
        )
        stream_kwargs = dict(
            chat_req=chat_req, run_kwargs=run_kwargs, is_reasoning=is_reasoning,
            session_id=session_id, artifacts=artifacts, ui_actions=ui_actions,
        )

        # 用户在对话设置里勾选的 MCP 工具配置(此处用请求 DB 会话取,仅取配置不建连接)
        mcp_configs = await cls._load_mcp_configs(query_db, user_config)

        if not mcp_configs:
            # 无 MCP:原直连路径(保持既有行为不变)
            agent = cls._build_agent(artifacts=artifacts, ui_actions=ui_actions, **build_kwargs)
            async for chunk in cls._stream_agent(agent=agent, **stream_kwargs):
                yield chunk
            return

        # 有 MCP:在独立 worker task 内连 MCP + 跑 agent,队列桥接给本生成器。
        # MCPTools 基于 anyio cancel scope,其进入/退出必须在同一 task;放进 worker 可避免与
        # 请求 DB 会话/生成器收尾跨 task 冲突("exit cancel scope in a different task")。
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        sentinel = object()

        async def _run_with_tools(extra_tools: list) -> None:
            agent = cls._build_agent(artifacts=artifacts, ui_actions=ui_actions,
                                     extra_tools=extra_tools, **build_kwargs)
            async for chunk in cls._stream_agent(agent=agent, **stream_kwargs):
                await queue.put(chunk)

        async def _worker() -> None:
            try:
                logger.info(f'[MCP worker] 启动,选中 {len(mcp_configs)} 个 MCP 工具')
                await cls._with_mcp_tools(mcp_configs, [], _run_with_tools)
                logger.info('[MCP worker] 正常结束')
            except Exception as e:  # noqa: BLE001
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
                    yield json.dumps(
                        {'error': f'工具调用 {idle_timeout}s 无响应,已中断(可能是 MCP 服务或模型卡住,请重试或减少所选工具)',
                         'type': 'error'}, ensure_ascii=False) + '\n'
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
                except BaseException:  # noqa: BLE001 worker 取消时在自身 task 内收尾 MCP 连接
                    pass

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
        from module_ai.service.ai_tool_service import AiToolService  # noqa: PLC0415

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
            from agno.tools.mcp import MCPTools  # noqa: PLC0415
        except Exception as e:  # noqa: BLE001
            logger.warning(f'MCP 依赖未安装,跳过 MCP 工具装配: {e}')
            await cb(connected)
            return
        from module_ai.service.ai_tool_service import AiToolService  # noqa: PLC0415

        cfg, rest = configs[0], configs[1:]
        try:
            kwargs = AiToolService.build_mcp_kwargs(cfg['args'])
        except Exception as e:  # noqa: BLE001 配置错,跳过该工具
            logger.warning(f"MCP 工具配置无效,跳过 {cfg.get('code')}: {e}")
            await cls._with_mcp_tools(rest, connected, cb)
            return
        try:
            async with MCPTools(**kwargs) as t:
                logger.info(f"MCP 工具已连接: {cfg['code']} ({len(getattr(t, 'functions', None) or {})} 个方法)")
                await cls._with_mcp_tools(rest, [*connected, t], cb)
        except Exception as e:  # noqa: BLE001 连不上不阻断,跳过该工具继续其余
            logger.warning(f"MCP 工具连接失败,跳过 {cfg['code']}: {e}")
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
    async def get_chat_session_list_services(cls, user_id: int) -> list[AiChatSessionBaseModel]:
        """
        获取用户会话列表

        :param user_id: 用户ID
        :return: 用户会话列表
        """
        # 获取Agno会话列表
        storage = AiUtil.get_storage_engine()
        sessions: list[Session] = await storage.get_sessions(
            user_id=str(user_id),
            component_id='chat-agent',
            session_type=SessionType.AGENT,
        )

        result = []
        for s in sessions:
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
            for m in messages if m.role == 'tool' and getattr(m, 'tool_call_id', None)
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
    async def save_recipe_services(cls, query_db: AsyncSession, session_id: str,
                                   tool_call_id: str, operator: str) -> dict:
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
        for run in (session.runs or []):
            for t in (getattr(run, 'tools', None) or []):
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

        from module_rag.entity.vo.rag_vo import ChunkSaveReq  # noqa: PLC0415
        from module_rag.service.chunk_service import ChunkService  # noqa: PLC0415
        from module_rag.service.dataset_service import DatasetService  # noqa: PLC0415

        ds = await DatasetService.ensure_for_source(query_db, None, datasource_code, operator)
        dataset_id = ds['id']
        saved = await ChunkService.save(
            query_db,
            ChunkSaveReq(datasetId=dataset_id, chunkType='qa', question=question, answer=code),
            operator,
        )
        chunk_id = saved['id']
        await ChunkService.star(query_db, chunk_id, 1)
        return {'chunkId': chunk_id, 'datasetName': ds.get('name'), 'datasourceCode': datasource_code,
                'question': question}
