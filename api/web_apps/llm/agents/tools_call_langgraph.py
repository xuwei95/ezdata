# encoding: utf-8
"""
ToolsCallAgent - LangGraph 版本
使用 LangGraph StateGraph 替代传统 AgentExecutor
支持工具调用、对象序列化、流式输出
"""
from typing import TypedDict, List, Any, Union, Dict, Iterator
from collections.abc import Iterator as ABCIterator
import types
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.agents import AgentAction, AgentFinish
from web_apps.llm.utils.object_serializer import ObjectSerializer
from web_apps.llm.llm_utils import get_llm
from utils.common_utils import get_now_time


def is_iterator(obj):
    """
    检测对象是否是迭代器（包括生成器）

    Args:
        obj: 待检测的对象

    Returns:
        bool: 是否是迭代器
    """
    # 检查是否是生成器
    if isinstance(obj, types.GeneratorType):
        return True
    # 检查是否是迭代器（有 __iter__ 和 __next__ 方法）
    if isinstance(obj, ABCIterator):
        return True
    # 检查是否有迭代器的方法
    return hasattr(obj, '__iter__') and hasattr(obj, '__next__')


class ToolsCallState(TypedDict):
    """Agent 状态定义"""
    messages: List[BaseMessage]                     # 对话消息列表
    input: str                                       # 用户输入
    intermediate_steps: List[tuple]                 # 中间步骤 [(AgentAction, observation), ...]
    agent_outcome: Union[AgentAction, AgentFinish, None]  # Agent 决策结果
    output: Any                                      # 最终输出
    flow_data: List[Dict[str, Any]]                 # 流程追踪数据


class ToolsCallAgent:
    """
    工具调用 Agent - LangGraph 实现

    特性：
    - 使用 LangGraph StateGraph 进行工作流编排
    - 支持对象序列化/反序列化（处理不可序列化对象）
    - 支持流式和同步两种执行模式
    - 兼容原有接口格式
    """

    def __init__(self, tools, llm=None, system_prompt=''):
        """
        初始化 Agent

        Args:
            tools: 工具列表
            llm: 语言模型实例，默认使用 get_llm()
            system_prompt: 系统提示词
        """
        self.llm = llm or get_llm()
        self.tools = {tool.name: tool for tool in tools}
        self.system_prompt = system_prompt + "\n在调用工具时，若遇到 object(<class 'XXX'>):XXX 形式变量，代表无法序列化的代指变量，传给后续工具时请保持此输入字符串"
        self.serializer = ObjectSerializer()
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """
        创建 LangGraph 工作流

        工作流结构：
        agent → (continue) → tools → (continue/end)
             → (end) → END            ↓
                                    agent/END
        """
        workflow = StateGraph(ToolsCallState)

        # 添加节点
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tools_node)

        # 设置入口
        workflow.set_entry_point("agent")

        # 条件路由：agent 决定是继续调用工具还是结束
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )

        # 工具执行后也需要条件路由：检查是否 return_direct
        workflow.add_conditional_edges(
            "tools",
            self._should_continue,
            {
                "continue": "agent",
                "end": END
            }
        )

        return workflow.compile()

    def _agent_node(self, state: ToolsCallState) -> ToolsCallState:
        """
        Agent 决策节点：使用 LLM 进行推理和决策

        1. 将系统提示和历史消息传递给 LLM
        2. LLM 决定是调用工具还是直接回答
        3. 解析 LLM 响应为 AgentAction 或 AgentFinish
        """
        messages = state["messages"]

        # 添加系统提示（仅在第一次）
        if len(messages) == 1 and not any(isinstance(m, SystemMessage) for m in messages):
            system_msg = SystemMessage(content=self.system_prompt)
            messages = [system_msg] + messages

        # 绑定工具到 LLM
        llm_with_tools = self.llm.bind_tools(list(self.tools.values()))

        # 调用 LLM
        response = llm_with_tools.invoke(messages)

        # 解析响应
        agent_outcome = self._parse_response(response)

        # 更新消息列表（避免重复添加）
        new_messages = messages + [response] if response not in messages else messages

        return {
            **state,
            "messages": new_messages,
            "agent_outcome": agent_outcome
        }

    def _tools_node(self, state: ToolsCallState) -> ToolsCallState:
        """
        工具执行节点：执行工具并处理序列化

        1. 反序列化工具输入（还原对象引用）
        2. 执行工具
        3. 序列化工具输出（转换为引用字符串）
        4. 检查是否是 return_direct 工具
        5. 记录流程追踪数据
        """
        agent_outcome = state["agent_outcome"]

        if not isinstance(agent_outcome, AgentAction):
            return state

        tool_name = agent_outcome.tool
        tool_input = agent_outcome.tool_input

        # 反序列化输入（关键步骤1：将引用字符串还原为对象）
        real_input = self.serializer.de_serialize_value(tool_input)

        # 记录工具调用
        flow_data = state.get("flow_data", [])
        flow_data.append({
            'content': {
                'title': f"调用工具:{tool_name}",
                'content': f"{{'tool': '{tool_name}', 'input': {tool_input}}}",
                'time': get_now_time(res_type='datetime')
            },
            'type': 'flow'
        })

        # 执行工具
        tool = self.tools.get(tool_name)
        if tool:
            try:
                observation = tool.invoke(real_input)
            except Exception as e:
                observation = f"工具执行错误: {str(e)}"
        else:
            observation = f"工具 {tool_name} 不存在"

        # 序列化输出（关键步骤2：将对象转换为引用字符串）
        serialized_obs = self.serializer.serialize_value(observation)

        # 记录工具结果
        flow_data.append({
            'content': {
                'title': f"获取工具{tool_name}调用结果",
                'content': f"{{'tool': '{tool_name}', 'result': {serialized_obs}}}",
                'time': get_now_time(res_type='datetime')
            },
            'type': 'flow'
        })

        # 创建工具消息
        tool_call_id = getattr(agent_outcome, 'tool_call_id', f"call_{tool_name}")
        tool_message = ToolMessage(
            content=str(serialized_obs),
            tool_call_id=tool_call_id
        )

        # 检查是否是 return_direct 工具（直接返回结果）
        new_agent_outcome = state.get("agent_outcome")
        if tool and getattr(tool, 'return_direct', False):
            # 工具设置了 return_direct，直接返回结果作为最终输出
            new_agent_outcome = AgentFinish(
                return_values={"output": serialized_obs},
                log=f"Tool {tool_name} returned directly"
            )

        return {
            **state,
            "messages": state["messages"] + [tool_message],
            "intermediate_steps": state["intermediate_steps"] + [(agent_outcome, serialized_obs)],
            "flow_data": flow_data,
            "agent_outcome": new_agent_outcome  # 更新 agent_outcome
        }

    def _should_continue(self, state: ToolsCallState) -> str:
        """
        判断是否继续执行工具

        返回 "continue" 如果需要调用工具
        返回 "end" 如果已完成
        """
        agent_outcome = state["agent_outcome"]

        if isinstance(agent_outcome, AgentFinish):
            return "end"
        return "continue"

    def _parse_response(self, response: BaseMessage) -> Union[AgentAction, AgentFinish]:
        """
        解析 LLM 响应为 AgentAction 或 AgentFinish

        检查响应中是否包含工具调用：
        - 有工具调用 → AgentAction
        - 无工具调用 → AgentFinish
        """
        # 检查是否有工具调用
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_call = response.tool_calls[0]
            return AgentAction(
                tool=tool_call['name'],
                tool_input=tool_call['args'],
                log=str(response),
                tool_call_id=tool_call.get('id', '')
            )

        # 无工具调用，返回最终结果
        return AgentFinish(
            return_values={"output": response.content},
            log=str(response)
        )

    def run(self, prompt: str):
        """
        同步执行 Agent

        Args:
            prompt: 用户输入提示词

        Returns:
            Agent 的最终输出（已反序列化）
        """
        initial_state = {
            "messages": [HumanMessage(content=prompt)],
            "input": prompt,
            "intermediate_steps": [],
            "agent_outcome": None,
            "output": None,
            "flow_data": []
        }

        try:
            result = self.workflow.invoke(initial_state)

            # 反序列化最终输出
            agent_outcome = result.get("agent_outcome")
            if isinstance(agent_outcome, AgentFinish):
                output = agent_outcome.return_values.get("output", "")
            else:
                output = ""

            output = self.serializer.de_serialize_value(output)

            return output
        finally:
            # 清理对象映射
            self.serializer.clear()

    def chat(self, prompt: str):
        """
        流式执行 Agent

        Args:
            prompt: 用户输入提示词

        Yields:
            流式输出数据，格式：
            - {'content': {...}, 'type': 'flow'} - 流程步骤
            - {'content': str, 'type': 'text'} - 文本输出
            - {'content': Any, 'type': 'html'/'data'} - 结构化输出
        """
        initial_state = {
            "messages": [HumanMessage(content=prompt)],
            "input": prompt,
            "intermediate_steps": [],
            "agent_outcome": None,
            "output": None,
            "flow_data": []
        }

        # 用于跟踪已输出的 flow_data，避免重复
        yielded_flow_count = 0

        try:
            for chunk in self.workflow.stream(initial_state):
                # 处理 agent 决策节点的输出（普通对话直接返回的情况）
                if 'agent' in chunk:
                    agent_state = chunk['agent']
                    agent_outcome = agent_state.get('agent_outcome')

                    # 如果 agent 直接返回结果（不调用工具），输出结果
                    if isinstance(agent_outcome, AgentFinish):
                        output = agent_outcome.return_values.get("output", "")
                        output = self.serializer.de_serialize_value(output)

                        # 处理不同类型的输出
                        # 1. 迭代器输出
                        if is_iterator(output):
                            for item in output:
                                yield item
                        # 2. 已格式化的输出
                        elif isinstance(output, dict) and 'content' in output and 'type' in output:
                            yield output
                        # 3. 普通文本输出
                        else:
                            yield {'content': output, 'type': 'text'}

                # 处理工具执行节点的输出
                if 'tools' in chunk:
                    tools_state = chunk['tools']
                    flow_data = tools_state.get('flow_data', [])

                    # 只输出新增的 flow_data
                    for flow_item in flow_data[yielded_flow_count:]:
                        yield flow_item
                        yielded_flow_count += 1

                    # 检查工具节点是否产生了 AgentFinish（return_direct 的情况）
                    agent_outcome = tools_state.get('agent_outcome')
                    if isinstance(agent_outcome, AgentFinish):
                        output = agent_outcome.return_values.get("output", "")
                        output = self.serializer.de_serialize_value(output)

                        # 处理不同类型的输出
                        # 1. 迭代器输出（如 DataChatAgent.chat 返回）
                        if is_iterator(output):
                            for item in output:
                                yield item
                        # 2. 已格式化的输出
                        elif isinstance(output, dict) and 'content' in output and 'type' in output:
                            yield output
                        # 3. 普通文本输出
                        else:
                            yield {'content': output, 'type': 'text'}

                # 处理最终结果（从 __end__ 节点，多轮工具调用后的最终输出）
                if '__end__' in chunk:
                    final_state = chunk['__end__']
                    agent_outcome = final_state.get('agent_outcome')

                    if isinstance(agent_outcome, AgentFinish):
                        output = agent_outcome.return_values.get("output", "")
                        output = self.serializer.de_serialize_value(output)

                        # 处理不同类型的输出
                        # 1. 迭代器输出（如 DataChatAgent.chat 返回）
                        if is_iterator(output):
                            for item in output:
                                yield item
                        # 2. 已格式化的输出
                        elif isinstance(output, dict) and 'content' in output and 'type' in output:
                            yield output
                        # 3. 普通文本输出
                        else:
                            yield {'content': output, 'type': 'text'}
        finally:
            # 清理对象映射
            self.serializer.clear()


if __name__ == '__main__':
    # 测试示例
    import json
    from pydantic import BaseModel, Field
    from langchain_core.tools import Tool, StructuredTool, tool
    import requests


    @tool
    def get_url_content(url: str) -> str:
        '''
        请求url, 获取内容结果
        :param url:
        :return:
        '''
        try:
            res = requests.get(url, timeout=10)
            return res.text
        except Exception as e:
            return f"请求失败：{e}"


    @tool
    def parse_content(content: str) -> dict:
        '''
        解析内容结果
        :return:
        '''
        try:
            return {
                'type': 'agent_output',
                'output': content
            }
        except Exception as e:
            return {
                'type': 'function error',
                'output': f"{e}"
            }


    @tool
    def multiply(x: float, y: float) -> float:
        """将 'x' 乘以 'y'。"""
        return x * y


    @tool
    def exponentiate(x: float, y: float) -> float:
        """将 'x' 乘以 'y' 的指数。"""
        return x ** y


    @tool
    def get_llm_tool() -> object:
        '''
        返回一个大语言模型对象（测试对象序列化）
        '''
        return get_llm()


    @tool
    def parse_content_with_llm(llm, content: str) -> dict:
        """
        使用大语言模型解析总结内容结果（测试对象传递）
        llm: BaseChatModel  # 大语言模型对象
        content: '待解析的内容字符串'
        """
        try:
            prompt = f"总结以下内容，转为200字左右文案\n{content[:1000]}"
            result = llm.invoke(prompt)
            return {
                'type': 'agent_output',
                'output': result.content
            }
        except Exception as e:
            return {
                'type': 'function_error',
                'output': f"{e}"
            }


    # 测试基础工具调用
    print("=" * 50)
    print("测试1: 基础数学计算")
    print("=" * 50)
    tools = [multiply, exponentiate]
    agent = ToolsCallAgent(tools=tools)
    res = agent.run('3的5次方加上5乘以3')
    print(f"结果: {res}")

    # 测试流式输出
    print("\n" + "=" * 50)
    print("测试2: 流式输出")
    print("=" * 50)
    for chunk in agent.chat('计算 10 的 2 次方乘以 5'):
        print(chunk)

    # 测试对象序列化
    print("\n" + "=" * 50)
    print("测试3: 对象序列化（LLM 对象传递）")
    print("=" * 50)
    tools = [get_llm_tool, parse_content_with_llm]
    agent = ToolsCallAgent(tools=tools)
    res = agent.chat('获取一个大语言模型对象，然后用它总结这段话：人工智能正在改变世界')
    for chunk in res:
        print(chunk)

    print("\n测试完成！")
