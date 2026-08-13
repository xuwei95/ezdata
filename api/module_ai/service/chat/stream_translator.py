"""把 agno 的运行事件流翻译成前端 SSE 消息(从 ai_chat_service 抽出)。

纯"事件→SSE"映射:归一 Team/单 Agent 事件、转发工具调用过程(start/end/error)、
推理/正文增量、指标,以及增量排空结构化产物(artifact)与任务提议(ui_action)。
不构造 agent、不查库;单 agent 与 Team 共用同一套处理。
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator, AsyncIterator
from typing import TYPE_CHECKING, Any

from agno.exceptions import InputCheckError
from agno.run.agent import RunEvent, RunOutputEvent

from utils.common_util import CamelCaseUtil

if TYPE_CHECKING:
    from agno.agent import Agent

    from module_ai.entity.vo.ai_chat_vo import AiChatRequestModel


def _short(v: Any, n: int = 300) -> str:
    """转字符串并截断(仅用于过程展示,不影响给 LLM 的内容)。"""
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
    return s if len(s) <= n else s[:n] + '…'


def _short_args(args: Any, n: int = 600) -> Any:
    """工具参数逐值截断(code 等长参数防刷屏)。"""
    if not isinstance(args, dict):
        return _short(args, n)
    return {k: (_short(v, n) if isinstance(v, str) else v) for k, v in args.items()}


async def stream_agent(
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
    except InputCheckError as e:
        # 输入侧护栏命中(提示注入/高危意图):回友好提示,当作助手正常拒答而非系统错误
        msg = getattr(e, 'message', None) or str(e)
        yield json.dumps({'content': msg, 'type': 'content'}, ensure_ascii=False) + '\n'
    except Exception as e:
        yield json.dumps({'error': str(e), 'type': 'error'}) + '\n'
