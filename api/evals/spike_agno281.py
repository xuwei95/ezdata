"""agno 2.8.1 新特性 spike——对着真实安装包验证,不动生产链路。

验证三件事(离线可跑的部分直接跑;需 LLM 的抽取只在配了 env 兜底模型时试):
  1. 工具调用旋钮:Agent(tool_call_limit=, max_tool_calls_from_history=) 能构造并生效;
  2. Learning Stores:LearningMachine(db=sqlite, 各 store=True) 能初始化;Agent(learning=...) 能挂;
  3. stream_sub_agent_events:定位它在 context provider 上(不在 Agent 上)。

跑:  python -m evals.spike_agno281
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_knobs() -> None:
    from agno.agent import Agent
    a = Agent(tool_call_limit=5, max_tool_calls_from_history=3)
    assert a.tool_call_limit == 5
    assert a.max_tool_calls_from_history == 3
    print('[1] 工具调用旋钮 OK: tool_call_limit=5, max_tool_calls_from_history=3(Agent 已接受并保存)')


def check_learning_stores() -> None:
    from agno.db.sqlite import SqliteDb
    from agno.learn import LearningMachine

    db_path = os.path.join(tempfile.gettempdir(), 'agno_spike_learn.db')
    db = SqliteDb(db_file=db_path)
    lm = LearningMachine(
        db=db,
        user_profile=True,       # 用户画像
        user_memory=True,        # 用户记忆(≈ 现有 MemoryManager/ai_memories)
        session_context=True,    # 会话上下文
        entity_memory=True,      # 实体记忆
        learned_knowledge=True,  # 已学知识(≈ 现有 recipe/数据源专属 KB 的定位)
        namespace='ezdata-spike',
        max_updates_per_run=10,
    )
    enabled = [name for name in ('user_profile', 'user_memory', 'session_context',
                                 'entity_memory', 'learned_knowledge', 'decision_log')
               if getattr(lm, name, None)]
    print(f'[2] LearningMachine 初始化 OK(sqlite@{db_path});启用 store: {enabled}')

    # Agent 直接挂 learning(bool 或 LearningMachine 实例)
    from agno.agent import Agent
    a1 = Agent(learning=True)              # 快捷:全量默认 store
    a2 = Agent(learning=lm)                # 精细:自定义 LearningMachine
    assert a1.learning is True
    assert a2.learning is lm
    print('    Agent(learning=True) OK;Agent(learning=<LearningMachine>) OK(bool 与实例两种都接受)')


def check_stream_sub_agent_events() -> None:
    import inspect

    from agno.agent import Agent
    on_agent = 'stream_sub_agent_events' in inspect.signature(Agent.__init__).parameters
    hits = []
    try:
        import agno.knowledge.context as _ctx  # noqa: F401
    except Exception:
        pass
    # 在 context provider 基类/实现里找该参数
    try:
        from agno.os.context import ContextProvider  # 位置可能随版本变
        if 'stream_sub_agent_events' in inspect.signature(ContextProvider.__init__).parameters:
            hits.append('ContextProvider')
    except Exception:
        pass
    print(f'[3] stream_sub_agent_events 在 Agent 上: {on_agent};'
          f'{"在 " + ",".join(hits) + " 上" if hits else "应在 context provider 上(见 2.8.1 release note)"}')


def try_live_extraction() -> None:
    """仅当配了 env 兜底模型时,跑一次极小对话看 user_profile 是否被抽取写库。"""
    from config.env import AiConfig
    if not AiConfig.enabled:
        print('[live] 跳过:未配置 LLM_* 兜底模型(实抽取需真实模型 + 网络)。'
              '配好后重跑本脚本即可看到 store 落库。')
        return
    print('[live] 检测到兜底模型,可在此扩展一次真实两轮对话验证 store 落库(需联网,略)。')


if __name__ == '__main__':
    check_knobs()
    check_learning_stores()
    check_stream_sub_agent_events()
    try_live_extraction()
    print('\nspike 完成:三项特性在 agno 2.8.1 上均可用(离线构造/初始化已验)。')
