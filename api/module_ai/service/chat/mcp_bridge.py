"""MCP 工具的连接生命周期与队列桥接(从 ai_chat_service 抽出)。

三件事:
- load_mcp_configs:按用户配置只读取 MCP 工具配置(不建连接);
- with_mcp_tools:递归 async with 逐个连上 MCP server(anyio cancel scope 必须同 task,故不用 AsyncExitStack);
- stream_with_mcp_bridge:在独立 worker task 内连 MCP + 跑 agent/Team,经队列桥接给外层生成器,
  含 idle 超时保护与收尾取消。

⚠️ 脆弱点:MCPTools 基于 anyio cancel scope,其进入/退出、以及在其作用域内的 agent.arun,
必须都发生在同一个 task 内,否则报 "exit cancel scope in a different task"。故连接与运行都塞进
worker task,外层生成器只从队列取。改动此文件务必保持这一 task 边界不变。
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any

from utils.log_util import logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from module_ai.entity.vo.ai_chat_vo import AiChatConfigModel


async def load_mcp_configs(query_db: AsyncSession, user_config: AiChatConfigModel) -> list[dict]:
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


async def with_mcp_tools(configs: list[dict], connected: list, cb: Any) -> None:
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
        await with_mcp_tools(rest, connected, cb)
        return
    try:
        async with MCPTools(**kwargs) as t:
            logger.info(f'MCP 工具已连接: {cfg["code"]} ({len(getattr(t, "functions", None) or {})} 个方法)')
            t._ezdata_code = cfg['code']  # 标记来源 code,便于多 agent 时按应用分发
            await with_mcp_tools(rest, [*connected, t], cb)
    except Exception as e:
        logger.warning(f'MCP 工具连接失败,跳过 {cfg["code"]}: {e}')
        await with_mcp_tools(rest, connected, cb)


async def stream_with_mcp_bridge(
    all_mcp_configs: list[dict],
    member_count: int,
    run_stream: Callable[[list], AsyncGenerator[str, None]],
    *,
    idle_timeout: int = 120,
) -> AsyncGenerator[str, None]:
    """有 MCP 时的流式桥接:在独立 worker task 内连 MCP + 跑 agent/Team,队列桥接给本生成器。

    run_stream(extra_tools): 给定已连接的 MCP 工具(带 _ezdata_code),返回逐块 SSE 的异步生成器。
    其首次迭代(即 agent/Team 的构造与 arun)发生在 worker task 内、MCPTools async with 作用域中——
    这是 anyio cancel scope 同 task 约束的关键,勿改。

    idle_timeout 秒内无任何输出则判定卡住(MCP/模型无响应),中断并报错而非冻结。
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=256)
    sentinel = object()

    async def _run_with_tools(extra_tools: list) -> None:
        async for chunk in run_stream(extra_tools):
            await queue.put(chunk)

    async def _worker() -> None:
        try:
            logger.info(
                f'[MCP worker] 启动,选中 {len(all_mcp_configs)} 个 MCP 工具,{member_count} 个成员 agent'
            )
            await with_mcp_tools(all_mcp_configs, [], _run_with_tools)
            logger.info('[MCP worker] 正常结束')
        except Exception as e:
            logger.exception(f'[MCP worker] 异常: {e}')
            await queue.put(json.dumps({'error': str(e), 'type': 'error'}, ensure_ascii=False) + '\n')
        finally:
            await queue.put(sentinel)

    task = asyncio.create_task(_worker())
    emitted = 0
    stuck = False
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
