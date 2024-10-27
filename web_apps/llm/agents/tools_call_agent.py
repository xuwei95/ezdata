from langchain_core.prompts import ChatPromptTemplate
from langchain.agents.loading import AGENT_TO_CLASS
from langchain.agents.agent_types import AgentType
from langchain.agents import create_tool_calling_agent
from web_apps.llm.llm_utils import get_llm
from utils.common_utils import get_now_time
from web_apps.llm.agents.agent_exector import ToolsAgentExecutor


class ToolsCallAgent:

    def __init__(self, tools, llm=None):
        if llm is not None:
            self.llm = llm
        else:
            self.llm = get_llm()
        # 对有function call 功能llm使用function call 否则使用react agent
        try:
            pre_prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个有用的助手, 在调用工具时，若遇到 object(<class 'XXX'>):XXX 形式变量，代表无法序列化的代指变量，传给后续工具时请保持此输入字符串"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            self.agent = create_tool_calling_agent(self.llm, tools, pre_prompt)
        except NotImplementedError:
            agent_cls = AGENT_TO_CLASS[AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION]
            self.agent = agent_cls.from_llm_and_tools(
                self.llm,
                tools
            )
        self.agent_executor = ToolsAgentExecutor(agent=self.agent, tools=tools, verbose=True)

    def run(self, prompt):
        '''
        运行agent获取结果
        '''
        res = self.agent_executor.invoke({"input": prompt})
        return res['output']

    def chat(self, prompt):
        '''
        对话形式
        '''
        res = self.agent_executor.stream({"input": prompt})
        for chunk in res:
            if 'actions' in chunk:
                action = chunk['actions'][0]
                content = {
                    'tool': action.tool,
                    'input': action.tool_input
                }
                data = {'content': {'title': f"调用工具:{action.tool}", 'content': f"{content}",
                                    'time': get_now_time(res_type='datetime')}, 'type': 'flow'}
                yield data
            if 'steps' in chunk:
                step = chunk['steps'][0]
                step_message = step.messages[0]
                content = {
                    'tool': step_message.name,
                    'result': step_message.content
                }
                data = {'content': {'title': f"获取工具{step_message.name}调用结果", 'content': f"{content}",
                                    'time': get_now_time(res_type='datetime')}, 'type': 'flow'}
                yield data
            if 'output' in chunk:
                data = {'content': {'title': f"处理完成", 'content': f"处理完成",
                                    'time': get_now_time(res_type='datetime')}, 'type': 'flow'}
                yield data
                output = chunk['output']
                if isinstance(output, dict) and 'content' in output and 'type' in output:
                    # 若是其他agent的输出格式，直接返回
                    yield output
                else:
                    data = {'content': chunk['output'], 'type': 'text'}
                    yield data


if __name__ == '__main__':
    import json
    from pydantic import BaseModel, Field
    from langchain_core.tools import Tool, StructuredTool, tool
    import requests


    @tool
    def get_url_content(url: str) -> str:
        '''
        请求url, 获取内容结果
        :param url:
        :param retry:
        :return:
        '''
        try:
            res = requests.get(url)
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


    def add(x: float, y: float) -> float:
        """将 'x' 和 'y' 相加。"""
        return x + y


    class AddInputSchema(BaseModel):
        """Input schema for the add function."""
        x: float = Field(description="The first number to add.")
        y: float = Field(description="The second number to add.")


    @tool
    def multiply(x: float, y: float) -> float:
        """将 'x' 乘以 'y'。"""
        return x * y


    @tool
    def exponentiate(x: float, y: float) -> float:
        """将 'x' 乘以 'y' 的指数。"""
        return x ** y


    def weather_function(location: str) -> str:
        """查询location城市天气"""
        match location:
            case "无锡" | "wuxi" | "Wuxi":
                weather = "晴天"
            case "苏州" | "suzhou":
                weather = "多云"
            case "常州" | "changzhou":
                weather = "雨"
            case _:
                weather = "不清楚"

        weather_answer = [
            {"天气": weather}
        ]

        return json.dumps(weather_answer)


    @tool
    def get_llm_tool() -> object:
        '''
        返回一个大语言模型对象
        '''
        return get_llm()


    @tool
    def parse_content(llm, content: str) -> dict:
        """
        使用大语言模型解析总结内容结果
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
    tools = [
        StructuredTool(
            name="add",
            func=add,
            args_schema=AddInputSchema,
            description="将 'x' 和 'y' 相加。"
        ),
        multiply,
        exponentiate,
        Tool(
            name="weather_function",
            func=weather_function,
            description="查询location城市天气",
        ),
        get_url_content,
        parse_content
    ]
    agent = ToolsCallAgent(tools=tools)
    # res = agent.run('3*3=?')
    # print(res)
    # res = agent.run('无锡天气')
    # print(res)
    # res = agent.chat('3的5次方加上5乘以3')
    # res = agent.chat('无锡天气')
    res = agent.chat('https://akshare.akfamily.xyz/data/bond/bond.html 获取其内容,并解析其内容')
    for chunk in res:
        print(chunk)
