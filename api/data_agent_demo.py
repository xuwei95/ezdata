#!/usr/bin/env python3
"""数据 Agent Demo —— 自然语言问数据,Agent 自主走完闭环并出结果。

闭环:发现数据源 → 查表结构 → 查业务口径(知识库) → 写取数代码 → 沙箱执行 → 出结论/表格/图表。

直接跑(后端容器内):
    docker exec -it ezdata-backend-dev python data_agent_demo.py
    docker exec -it ezdata-backend-dev python data_agent_demo.py "你的问题"

依赖:已配置 LLM(环境变量 LLM_* 兜底模型 或 库内启用模型)、SANDBOX_ENABLED=true、demo_mysql 数据源。
"""

from __future__ import annotations

import sys

from agno.agent import Agent

from config.env import AiConfig
from module_ai.tools.data_agent_tools import DataAgentTools
from module_ai.tools.sandbox_code_tools import SandboxCodeTools
from utils.ai_util import AiUtil

SYSTEM_PROMPT = """你是数据分析助手。回答数据问题时严格按步骤,并简要说明你在做什么:
1. list_datasources 看有哪些数据源(数据源多时可传 codes 只看指定的)
2. get_table_schema(datasource_code, tables) 查相关表的字段(先不传 tables 看表名,再传具体表查字段)
3. search_datasource_knowledge(datasource_code, query) 查字段业务口径(如金额单位、状态码含义)——务必查,避免口径错误
4. run_datasource_query(datasource_code, code) 写 Python 取数并加工:
   - code 中用 handler.query(sql, None, limit) 取数(返回 list[dict])
   - 用 pandas 加工;把结果赋给 result 变量
   - 结论用 {'type':'string','value':'...'};表格用 {'type':'dataframe','value':pd.DataFrame(...)};
     图表用 pyecharts,{'type':'html','value':chart.render_embed()}
注意业务口径(如金额单位是分要换算成元)。最后用中文自然语言总结结论。"""


def build_model():
    """构造模型:优先环境变量兜底模型(api_key 明文)。"""
    if not AiConfig.enabled:
        sys.exit('未配置 LLM:请设置环境变量 LLM_TYPE/LLM_MODEL/LLM_API_KEY,或在「AI 模型管理」启用一个模型')
    return AiUtil.get_model_from_factory(
        provider=AiConfig.provider,
        model_code=AiConfig.llm_model,
        model_name=None,
        api_key=AiConfig.llm_api_key,
        base_url=AiConfig.llm_url or None,
        temperature=0.2,
        max_tokens=AiConfig.llm_max_tokens or 4096,
    )


def _event_name(ev) -> str:  # noqa: ANN001
    e = getattr(ev, 'event', '')
    return getattr(e, 'value', e)


def run_demo(question: str) -> None:
    agent = Agent(
        model=build_model(),
        description=SYSTEM_PROMPT,
        tools=[DataAgentTools(), SandboxCodeTools()],
        markdown=False,
    )
    print('\n' + '=' * 72)
    print(f'❓ 问题: {question}')
    print('=' * 72)

    for ev in agent.run(question, stream=True, stream_events=True):
        name = _event_name(ev)
        if name == 'ToolCallStarted':
            tool = getattr(ev, 'tool', None)
            tn = getattr(tool, 'tool_name', '?') if tool else '?'
            ta = getattr(tool, 'tool_args', '') if tool else ''
            print(f'\n\n🔧 调用工具 {tn}  参数={ta}')
        elif name == 'ToolCallCompleted':
            tool = getattr(ev, 'tool', None)
            res = str(getattr(tool, 'result', '') if tool else '')
            print(f'   ↳ 返回: {res[:400]}{"…" if len(res) > 400 else ""}')
        elif name == 'ToolCallError':
            tool = getattr(ev, 'tool', None)
            print(f'   ✗ 工具错误: {getattr(tool, "result", "") if tool else ev}')
        elif name in ('RunContent', 'RunIntermediateContent'):
            print(getattr(ev, 'content', '') or '', end='', flush=True)
        elif name in ('RunError', 'RunCancelled'):
            print(f'\n‼️ {name}: {getattr(ev, "content", "") or getattr(ev, "error", ev)}')

    print('\n\n' + '=' * 72)
    print('✅ Agent 已完成(以上为完整过程:发现数据源 → 查表结构 → 查业务口径 → 取数加工 → 自我纠错 → 结论)')
    print('=' * 72 + '\n')


if __name__ == '__main__':
    q = sys.argv[1] if len(sys.argv) > 1 else (
        'demo_mysql 数据源的 demo_orders 表,已支付订单的总金额是多少元?'
        '另外按 status 统计各状态的订单数,用柱状图展示。'
    )
    run_demo(q)
