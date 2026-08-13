import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_ai.entity.vo.ai_chat_vo import (
    AiChatConfigModel,
    AiChatRequestModel,
)
from module_ai.entity.vo.ai_model_vo import AiModelModel
from module_ai.service.chat import agent_factory, app_spec, recipe_fastpath, session_store, stream_translator
from module_ai.service.chat.prompts import (
    _PASSTHROUGH_BUILTIN,
    _SCOPED_ASK_INSTRUCTIONS,
    _default_builtin_codes,
)
from utils.log_util import logger

# 本文件已瘦身为「编排门面」。实现分布在 chat/ 包:
# - prompts.py:提示词/意图常量 + _default_builtin_codes
# - recipe_fastpath.py:Recipe 快路(含回退哨兵 RECIPE_FALLBACK)
# - stream_translator.py:agno 事件流 → 前端 SSE(stream_agent + _short/_short_args)
# - agent_factory.py:模型/工具/agent/team 构造(make_model/assemble_tools/build_agent/build_team…)
# - app_spec.py:AI 应用 → Team 成员装配规格
# - session_store.py:会话与用户对话配置读写
# AiChatService 保留编排(chat_services/scoped_ask_stream)+ 请求侧配置解析,其余经 staticmethod 委派。


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

    @classmethod
    async def scoped_ask_stream(
        cls,
        query_db: AsyncSession,
        *,
        question: str,
        datasource_code: str,
        table: str,
        columns: list[str] | None,
        business: str | None,
        user_id: int,
        session_id: str | None = None,
        model_id: int = 0,
        is_reasoning: bool = False,
    ) -> AsyncGenerator[str, None]:
        """「AI 洞察」:锁定单张表的交互式问数流(复用 agent + artifact 通道,多轮靠 session 历史)。

        与主对话 chat_services 隔离:独立 agent_id='model-ask' + 独立 session_id 命名空间,不走 recipe/记忆/MCP。
        model_id=0 走环境变量兜底 LLM(与「AI 生成查询/图表」一致,零配置)。
        """
        if not (question or '').strip():
            raise ServiceException(message='请输入问题')
        model_config = await cls._resolve_chat_model_config(query_db, model_id)
        session_id = session_id or f'model-ask-{datasource_code}-{user_id}-{uuid.uuid4()}'
        col_line = ', '.join(str(c) for c in (columns or []) if c) or '(未知)'
        system_prompt = (
            f'你是数据分析助手,专注数据源「{datasource_code}」的表「{table}」。'
            f'该表字段: {col_line}。业务说明: {(business or "").strip() or "(暂无)"}。'
            '用户会针对这张表提问,请用工具查数/画图作答。'
        )
        chat_req = AiChatRequestModel(
            sessionId=session_id, modelId=model_id, message=question, isReasoning=is_reasoning
        )
        artifacts: list = []
        ui_actions: list = []
        agent = cls._build_agent(
            model_config=model_config,
            temperature=model_config.temperature,
            system_prompt=system_prompt,
            user_id=user_id,
            session_id=session_id,
            add_history=True,
            num_history=5,
            artifacts=artifacts,
            ui_actions=ui_actions,
            builtin_codes=['data_explore', 'sandbox_code'],
            instructions=[_SCOPED_ASK_INSTRUCTIONS],
            datasource_scope=[datasource_code],
            datasource_query_enabled=True,
            agent_id='model-ask',
            enable_memory=False,
            question=question,
            is_reasoning=is_reasoning,
        )
        async for chunk in stream_translator.stream_agent(
            agent=agent,
            chat_req=chat_req,
            run_kwargs={'stream': True, 'stream_events': True},
            is_reasoning=is_reasoning,
            session_id=session_id,
            artifacts=artifacts,
            ui_actions=ui_actions,
        ):
            yield chunk

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

        # —— Recipe 快路:问题一字不差命中⭐收藏的解法 → 沙箱直跑一次(不经模型),失败/异常再回退模型 ——
        # 放在 agent 装配之前:命中即秒回、省下模型与工具的一整轮开销;未命中/跑挂则 fall through 到下方正常流程。
        if datasource_query_enabled:
            _hit = await recipe_fastpath.recipe_fastpath_lookup(query_db, chat_req, datasource_scope)
            if _hit:
                _fell_back = False
                _out: dict = {}
                async for _sse in recipe_fastpath.stream_recipe_fastpath(
                    session_id, _hit[0], _hit[1], datasource_scope, _out
                ):
                    if _sse is recipe_fastpath.RECIPE_FALLBACK:
                        _fell_back = True
                        break
                    yield _sse
                if not _fell_back:
                    # 落会话记录(transcript + 下一轮历史一致);失败只告警,不影响已返回结果
                    await recipe_fastpath.persist_fastpath_turn(
                        session_id, user_id, chat_req.message, _out.get('answer', '')
                    )
                    return  # 命中直跑成功 → 本轮结束,不进模型

        artifacts: list = []  # 工具(沙箱)产出的图表/表格收集器,经 _stream_agent 推给前端渲染
        ui_actions: list = []  # 任务提议(确认表单)收集器,经 _stream_agent 推给前端渲染成卡片
        run_kwargs = cls._build_run_kwargs(chat_req, user_config)

        # Agent Skills:应用取其绑定的 skillIds;普通对话取全部启用技能。预加载正文供 load_skill 按需返回。
        from module_ai.service.ai_skill_service import AiSkillService

        skill_ids = (app_cfg.get('skillIds') if app_cfg else None) or None
        skills = await AiSkillService.resolve_agent_skills(query_db, skill_ids, scope_codes=datasource_scope)

        # 指标层(语义层 L0):启用的指标注入目录 + 挂 query_metric;数据分析关闭(应用未选源)则不挂
        metrics = []
        if datasource_query_enabled:
            from module_data.service.metric_service import MetricService

            metrics = await MetricService.resolve_agent_metrics(query_db)

        # 普通对话:task_propose 按任务意图条件挂载(省其大 docstring 的每轮重发);应用模式沿用 app 配置
        if not app_cfg and builtin_codes is None:
            builtin_codes = _default_builtin_codes(chat_req.message)

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
            skills=skills,
            metrics=metrics,
            question=chat_req.message,
            is_reasoning=is_reasoning,
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
            async for chunk in stream_translator.stream_agent(agent=_runnable([]), **stream_kwargs):
                yield chunk
            return

        # 有 MCP:在独立 worker task 内连 MCP + 跑 agent/Team,队列桥接给本生成器。
        # MCPTools 基于 anyio cancel scope,其进入/退出必须在同一 task;放进 worker 可避免与
        # 请求 DB 会话/生成器收尾跨 task 冲突("exit cancel scope in a different task")。
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        sentinel = object()

        async def _run_with_tools(extra_tools: list) -> None:
            async for chunk in stream_translator.stream_agent(agent=_runnable(extra_tools), **stream_kwargs):
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

    # —— 构造工厂 / 应用装配:实现在 chat.agent_factory / chat.app_spec,此处委派 ——
    # (_resolve_chat_model_config 亦被 module_ai/module_data 外部直接调用,委派保其可达)
    _resolve_chat_model_config = staticmethod(agent_factory.resolve_chat_model_config)
    _build_agent = staticmethod(agent_factory.build_agent)
    _build_team = staticmethod(agent_factory.build_team)
    _build_run_kwargs = staticmethod(agent_factory.build_run_kwargs)
    _load_agent_app_ids = staticmethod(app_spec.load_agent_app_ids)
    _resolve_app_agent_spec = staticmethod(app_spec.resolve_app_agent_spec)

    # —— 会话 / 用户对话配置读写:实现在 chat.session_store,此处委派以保持公开 API(controller 调用面)不变 ——
    ai_chat_config_detail_services = staticmethod(session_store.ai_chat_config_detail_services)
    save_ai_chat_config_services = staticmethod(session_store.save_ai_chat_config_services)
    get_chat_session_list_services = staticmethod(session_store.get_chat_session_list_services)
    delete_chat_session_services = staticmethod(session_store.delete_chat_session_services)
    get_chat_session_detail_services = staticmethod(session_store.get_chat_session_detail_services)
    cancel_run_services = staticmethod(session_store.cancel_run_services)

    # —— Recipe 收藏:实现在 chat.recipe_fastpath,此处委派以保持公开 API(controller 调用面)不变 ——
    save_recipe_services = staticmethod(recipe_fastpath.save_recipe_services)

