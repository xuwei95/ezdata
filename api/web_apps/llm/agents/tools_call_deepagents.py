# encoding: utf-8
"""
ToolsCallAgent - DeepAgents 版本
使用 deepagents 框架实现工具调用，简化工作流编排
"""
import types
from typing import Any, Dict, List, Union
from collections.abc import Iterator as ABCIterator
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from deepagents import create_deep_agent
from web_apps.llm.utils.object_serializer import ObjectSerializer
from web_apps.llm.llm_utils import get_llm
from utils.common_utils import get_now_time


def is_iterator(obj):
    if isinstance(obj, types.GeneratorType):
        return True
    if isinstance(obj, ABCIterator):
        return True
    return hasattr(obj, '__iter__') and hasattr(obj, '__next__')


class ToolsCallDeepAgent:
    """
    工具调用 Agent - DeepAgents 实现

    特性：
    - 使用 deepagents 框架简化工作流编排
    - 支持对象序列化/反序列化（处理不可序列化对象）
    - 支持流式和同步两种执行模式
    - 兼容原有接口格式
    - 更简洁的代码结构
    """

    def __init__(self, tools: List[BaseTool], llm=None, system_prompt=''):
        """
        初始化 Agent

        Args:
            tools: 工具列表
            llm: 语言模型实例，默认使用 get_llm()
            system_prompt: 系统提示词
        """
        self.llm = llm or get_llm()
        self.tools = {tool.name: tool for tool in tools}
        self.system_prompt = system_prompt + "\n在调用工具时，若遇到 object(<class 'XXX'>):XXX 形式变量，代表无法序列化的代指变量，传给后续工具时保持此输入字符串"
        self.serializer = ObjectSerializer()

        # 创建 deepagent
        self.agent = self._create_agent()

    def _create_agent(self):
        """
        创建 DeepAgents 实例，所有工具先用序列化包装器包裹
        """
        wrapped_tools = [self._wrap_tool_with_serialization(t) for t in self.tools.values()]

        agent = create_deep_agent(
            model=self.llm,
            tools=wrapped_tools,
            system_prompt=self.system_prompt,
            middleware=[],  # 禁用默认中间件
        )
        return agent

    def _wrap_tool_with_serialization(self, tool: BaseTool) -> BaseTool:
        """
        包装工具，自动处理对象序列化/反序列化（参考 LangGraph _tools_node 实现）

        - 反序列化输入：将 LLM 传入的引用字符串还原为真实对象
        - 序列化输出：将不可 JSON 化的对象/生成器转换为引用字符串
        """
        from langchain_core.tools import StructuredTool

        original_tool = tool
        serializer = self.serializer

        def wrapped_func(**kwargs):
            # 关键步骤 1：反序列化输入（引用字符串 → 真实对象）
            real_input = serializer.de_serialize_value(kwargs)

            # 执行原始工具
            try:
                observation = original_tool.invoke(real_input)
            except Exception as e:
                observation = f"工具执行错误: {str(e)}"

            # 关键步骤 2：序列化输出（对象/生成器 → 引用字符串）
            serialized_obs = serializer.serialize_value(observation)
            return str(serialized_obs)

        return StructuredTool.from_function(
            func=wrapped_func,
            name=tool.name,
            description=tool.description,
            args_schema=getattr(tool, 'args_schema', None),
            return_direct=getattr(tool, 'return_direct', False),
        )

    def _add_flow_data(self, flow_data_list: List[Dict], title: str, content: Any):
        """
        添加流程追踪数据

        Args:
            flow_data_list: 流程数据列表
            title: 标题
            content: 内容
        """
        flow_data_list.append({
            'content': {
                'title': title,
                'content': content,
                'time': get_now_time(res_type='datetime')
            },
            'type': 'flow'
        })

    def _extract_tool_info(self, tool_call: Dict) -> tuple:
        """
        从工具调用中提取工具名称和参数

        Args:
            tool_call: 工具调用字典

        Returns:
            (工具名称, 参数字符串)
        """
        tool_name = tool_call.get('name', '')
        args = tool_call.get('args', {})
        args_str = str(args)
        if len(args_str) > 300:
            args_str = args_str[:300] + '...'
        return tool_name, args_str

    def run(self, prompt: str) -> Any:
        """
        同步执行 Agent

        Args:
            prompt: 用户输入提示词

        Returns:
            Agent 的最终输出（已反序列化）
        """
        try:
            # 调用 deepagent
            result = self.agent.invoke({"messages": [HumanMessage(content=prompt)]})

            # 提取最终输出
            output = self._extract_final_output(result)

            # 反序列化输出
            if output:
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
        flow_data_list = []
        yielded_flow_count = 0
        extra_chunks = []   # 子 Agent 工具（如 DataChatDeepAgentTool）的中间状态

        try:
            # 流式调用 deepagent
            for event in self.agent.stream(
                {"messages": [HumanMessage(content=prompt)]},
                stream_mode=["updates", "messages"],
            ):
                event_type, data = event
                # 处理消息流（token 级别）
                if event_type == "messages":
                    msg_chunk, metadata = data

                    # 处理 AI 消息（文本内容）
                    if isinstance(msg_chunk, AIMessage):
                        content = msg_chunk.content

                        # 处理结构化 content（Claude extended thinking）
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict):
                                    btype = block.get('type')
                                    if btype == 'thinking':
                                        thinking = block.get('thinking', '') or block.get('thinking_delta', '')
                                        if thinking:
                                            self._add_flow_data(flow_data_list, '思考中', thinking)
                                    elif btype == 'text':
                                        text = block.get('text', '')
                                        if text:
                                            yield {'content': text, 'type': 'text'}
                        # 处理纯文本内容（部分推理模型 reasoning 放在 additional_kwargs）
                        elif isinstance(content, str):
                            reasoning = (msg_chunk.additional_kwargs.get('reasoning_content')
                                         or msg_chunk.additional_kwargs.get('thinking'))
                            if reasoning:
                                yield {'content': reasoning, 'type': 'thinking'}
                            elif content:
                                yield {'content': content, 'type': 'text'}

                # 处理状态更新（工具调用等）
                elif event_type == "updates":
                    for node_name, node_output in data.items():
                        if not isinstance(node_output, dict):
                            continue

                        # 处理工具调用
                        messages = node_output.get("messages", [])
                        if hasattr(messages, 'value'):
                            messages = messages.value
                        if not isinstance(messages, list):
                            continue

                        for msg in messages:
                            # 处理 AI 消息（工具调用请求）
                            if isinstance(msg, AIMessage):
                                for tc in (msg.tool_calls or []):
                                    tool_name, args_str = self._extract_tool_info(tc)

                                    # 跳过 write_todos（deepagents 内置）
                                    if tc['name'] == 'write_todos':
                                        todos = tc.get('args', {}).get('todos', [])
                                        todo_str = '\n'.join(
                                            f"[{t.get('status', 'pending')}] {t.get('content', '')}"
                                            for t in todos
                                        )
                                        self._add_flow_data(flow_data_list, '规划任务', todo_str)
                                    else:
                                        self._add_flow_data(
                                            flow_data_list,
                                            '调用工具',
                                            f"工具: {tool_name}\n参数: {args_str}"
                                        )

                            # 处理工具消息（工具执行结果）
                            elif isinstance(msg, ToolMessage):
                                if msg.name != 'write_todos':  # 跳过 write_todos
                                    # 检查工具是否有待输出的子 Agent 中间状态
                                    tool_obj = self.tools.get(msg.name)
                                    pending = getattr(tool_obj, '_pending_chunks', None)
                                    if pending:
                                        # 将子 Agent 中间状态加入待 yield 队列
                                        extra_chunks.extend(pending)
                                        tool_obj._pending_chunks = []
                                    else:
                                        # 尝试反序列化，若结果为生成器则加入 extra_chunks
                                        deserialized = self.serializer.de_serialize_value(msg.content)
                                        if is_iterator(deserialized):
                                            extra_chunks.append(deserialized)
                                        else:
                                            content_str = str(msg.content)
                                            preview = content_str[:300] + '...' if len(content_str) > 300 else content_str
                                            self._add_flow_data(flow_data_list, '工具返回', preview)

                        # yield 新增的 flow_data
                        new_items = flow_data_list[yielded_flow_count:]
                        for item in new_items:
                            yield item
                            yielded_flow_count += 1

                        # yield 子 Agent 的中间状态（在流程步骤之后）
                        for item in extra_chunks:
                            yield from self._yield_output(item)
                        extra_chunks = []

        finally:
            # 清理对象映射
            self.serializer.clear()

        # yield 剩余的 flow_data
        for item in flow_data_list[yielded_flow_count:]:
            yield item

    def _yield_output(self, output):
        """
        统一处理单个输出（参考 ToolsCallAgent 的生成器处理逻辑）：
        - 生成器/迭代器 → 递归 yield 每一项
        - 已格式化 dict  → 直接 yield
        - 其他          → 包装为 text 类型 yield
        """
        if is_iterator(output):
            for item in output:
                yield from self._yield_output(item)
        elif isinstance(output, dict) and 'content' in output and 'type' in output:
            yield output
        elif output:
            yield {'content': str(output), 'type': 'text'}

    def _extract_final_output(self, result: Dict) -> Any:
        """
        从 agent 结果中提取最终输出

        Args:
            result: agent 返回的结果字典

        Returns:
            提取的输出内容
        """
        # 检查 messages 中的最后一条消息
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]

            # 如果是 AIMessage 且有内容
            if isinstance(last_message, AIMessage):
                content = last_message.content
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # 提取 text block
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            return block.get('text', '')

        # 默认返回空字符串
        return ""


if __name__ == '__main__':
    # 测��示例
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
    def multiply(x: float, y: float) -> str:
        """将 'x' 乘以 'y'。返回结果字符串。"""
        return str(x * y)


    @tool
    def exponentiate(x: float, y: float) -> str:
        """将 'x' 乘以 'y' 的指数。返回结果字符串。"""
        return str(x ** y)


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
                'type': 'function error',
                'output': f"{e}"
            }


    # 测试基础工具调用
    print("=" * 50)
    print("测试1: 基础数学计算")
    print("=" * 50)
    tools = [multiply, exponentiate]
    agent = ToolsCallDeepAgents(tools=tools)
    res = agent.run('3的5次方加上5乘以3')
    print(f"结果: {res}")

    # 测试流式输出
    print("\n" + "=" * 50)
    print("测试2: 流式输出")
    print("=" * 50)
    for chunk in agent.chat('计算 10 的 2 次方乘以 5'):
        print(chunk)

    print("\n测试完成！")
