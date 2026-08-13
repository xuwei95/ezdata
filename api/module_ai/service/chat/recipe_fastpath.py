"""Recipe 快路:⭐收藏的已验证解法的"确定性执行缓存"(从 ai_chat_service 抽出)。

问题一字不差命中某数据源专属库里带星的 QA 解法时,绕开模型直接在沙箱跑那段取数代码,
成功即秒回(零 token)、失败则回退模型。以及把成功取数调用⭐收藏成解法(save_recipe_services)。

这一整块与"活体 agent 编排"松耦合:chat_services 在装配 agent 之前先探一次快路(lookup→stream),
命中直跑成功就 persist 落会话并 return,不进模型。对外 save_recipe_services 由 AiChatService 门面委派。
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from agno.db.base import SessionType
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from utils.ai_util import AiUtil
from utils.log_util import logger

if TYPE_CHECKING:
    from agno.session import Session

    from module_ai.entity.vo.ai_chat_vo import AiChatRequestModel

# 回退哨兵:stream_recipe_fastpath 执行失败时 yield 此对象,chat_services 见到即回退到模型。
RECIPE_FALLBACK = object()


async def recipe_fastpath_lookup(
    query_db: AsyncSession, chat_req: AiChatRequestModel, datasource_scope: list | None
) -> tuple[str, str] | None:
    """Recipe 快路查询:问题**一字不差**命中某数据源专属库里⭐收藏的解法(QA,question_hash=md5)
    → 返回 (可直跑取数代码, 数据源编码);未命中/被关/多模态 → None(照常走模型)。

    这是"确定性执行缓存":精确命中即确定,故可绕开模型直跑;非精确不进此路,避免误判。
    """
    from config.env import AiConfig

    if not getattr(AiConfig, 'llm_recipe_fastpath', True):
        return None
    if getattr(chat_req, 'images', None):  # 多模态需模型
        return None
    q = (chat_req.message or '').strip()
    if not q:
        return None
    from sqlalchemy import select

    from module_data.entity.do.data_do import DataSource
    from module_rag.entity.do.rag_do import RagChunk, RagDataset
    from module_rag.runtime_util import md5

    stmt = (
        select(RagChunk.answer, DataSource.code)
        .join(RagDataset, RagDataset.id == RagChunk.dataset_id)
        .join(DataSource, DataSource.id == RagDataset.source_id)
        .where(
            RagChunk.chunk_type == 'qa',
            RagChunk.star_flag == 1,  # 只有⭐标星的 QA(收藏的已验证解法)才走快路;普通/导入 QA 不绕开模型
            RagChunk.question_hash == md5(q),
            RagDataset.status == 1,
        )
    )
    if datasource_scope:
        stmt = stmt.where(DataSource.code.in_(list(datasource_scope)))
    row = (await query_db.execute(stmt.limit(1))).first()
    if not row or not (row[0] and row[1]):
        return None
    return row[0], row[1]


async def stream_recipe_fastpath(
    session_id: str, code: str, datasource_code: str, datasource_scope: list | None, out: dict | None = None
) -> AsyncGenerator[Any, None]:
    """流式执行命中的解法(不经模型):meta → 命中提示 → 沙箱直跑 → 成功吐 artifact+结果+metrics;
    失败/异常则吐提示并 yield `RECIPE_FALLBACK`,由 chat_services 回退到模型继续。
    沙箱执行沿用 SandboxCodeTools.run_datasource_query(只读护栏 + egress 白名单 + 图表可存看板)。
    out(可选可变字典):成功时写入 out['answer']=结果文本,供 chat_services 落会话记录。"""
    from fastapi.concurrency import run_in_threadpool

    from module_ai.tools.sandbox_code_tools import SandboxCodeTools

    yield json.dumps({'session_id': session_id, 'type': 'meta'}) + '\n'
    yield json.dumps({'content': '🔖 命中已验证解法,直接执行(未经模型)…\n', 'type': 'content'}, ensure_ascii=False) + '\n'
    arts: list = []
    try:
        tools = SandboxCodeTools(artifacts=arts, allowed_codes=datasource_scope, enable_datasource=True)
        text = await run_in_threadpool(tools.run_datasource_query, datasource_code, code)
    except Exception as e:
        logger.warning(f'[recipe-fastpath] 执行异常,回退模型: {e}')
        yield json.dumps({'content': '解法执行异常,转由模型继续处理…\n', 'type': 'content'}, ensure_ascii=False) + '\n'
        yield RECIPE_FALLBACK
        return
    _FAIL_PREFIX = ('执行失败', '查询失败', '调用沙箱失败', '数据源解析失败', '查询未执行', '该应用未授权')
    if isinstance(text, str) and text.startswith(_FAIL_PREFIX):
        logger.info(f'[recipe-fastpath] 解法执行失败,回退模型: {text[:80]}')
        yield json.dumps({'content': '已验证解法这次没跑通,转由模型继续处理…\n', 'type': 'content'}, ensure_ascii=False) + '\n'
        yield RECIPE_FALLBACK
        return
    # 成功:先排空图表/表格产物,再吐结果文本 + 快路 metrics(标注未经模型、零 token)
    for a in arts:
        yield json.dumps({'artifact': a, 'type': 'artifact'}, ensure_ascii=False) + '\n'
    if text:
        yield json.dumps({'content': str(text), 'type': 'content'}, ensure_ascii=False) + '\n'
    yield json.dumps({'metrics': {'fastPath': True, 'inputTokens': 0, 'outputTokens': 0, 'totalTokens': 0}, 'type': 'metrics'}) + '\n'
    if out is not None:
        out['answer'] = str(text) if text else ''  # 供上层落会话记录
    logger.info(f'[recipe-fastpath] 命中直跑成功: ds={datasource_code}')


async def persist_fastpath_turn(session_id: str, user_id: int, question: str, answer: str) -> None:
    """把 recipe 快路这一轮(用户问题 + 助手答案)落进 agno 会话,保证 transcript 与下一轮历史一致。
    用 agno 原生 AgentSession/RunOutput/RunInput/Message 构造,schema 正确;失败只告警、不影响本轮。
    (图表 artifact 的历史回放属增量,B 版先落文字。)"""
    try:
        import time
        import uuid as _uuid

        from agno.db.base import SessionType
        from agno.models.message import Message
        from agno.run.agent import RunInput, RunOutput
        from agno.run.base import RunStatus
        from agno.session import AgentSession

        storage = AiUtil.get_storage_engine()
        uid = str(user_id)
        ts = int(time.time())
        sess = await storage.get_session(session_id=session_id, session_type=SessionType.AGENT, user_id=uid)
        if sess is None:
            sess = await storage.get_session(session_id=session_id, session_type=SessionType.AGENT)
        if sess is None:
            # agent_id='chat-agent' 使会话进入普通对话列表(get_sessions 按 component_id 过滤);
            # session_data/agent_data 置空 dict,对齐 agno 正常会话、避免 transcript 读取 NoneType。
            sess = AgentSession(
                session_id=session_id, user_id=uid, agent_id='chat-agent',
                runs=[], session_data={}, agent_data={}, created_at=ts, updated_at=ts,
            )
        run = RunOutput(
            run_id=str(_uuid.uuid4()),
            session_id=session_id,
            user_id=uid,
            agent_id='chat-agent',  # 关键:AgentSession.from_dict 只保留 run dict 里含 agent_id 的 run,否则反序列化丢弃
            input=RunInput(input_content=question),
            content=answer,
            created_at=ts,
            status=RunStatus.completed,  # 关键:非 completed 的 run 会在反序列化时被 agno 过滤掉
            messages=[
                Message(role='user', content=question, created_at=ts),
                Message(role='assistant', content=answer, created_at=ts),
            ],
        )
        if sess.runs is None:
            sess.runs = []
        sess.runs.append(run)
        sess.updated_at = ts
        await storage.upsert_session(sess)
        logger.info(f'[recipe-fastpath] 已落会话: session={session_id} runs={len(sess.runs)}')
    except Exception as e:
        logger.warning(f'[recipe-fastpath] 落会话失败(不影响本轮): {e}')


async def save_recipe_services(query_db: AsyncSession, session_id: str, tool_call_id: str, operator: str) -> dict:
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
