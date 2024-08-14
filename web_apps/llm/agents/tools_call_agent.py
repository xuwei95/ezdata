from web_apps.llm.utils import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, initialize_agent, AgentExecutor
from utils.common_utils import get_now_time


class ToolsCallAgent:

    def __init__(self, tools, llm=None):
        if llm is not None:
            self.llm = llm
        else:
            self.llm = get_llm()
        # 对有function call 功能llm使用function call 否则使用react agent
        if hasattr(self.llm, "bind_tools"):
            pre_prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个有用的助手"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            function_call_agent = create_tool_calling_agent(self.llm, tools, pre_prompt)
            self.agent_executor = AgentExecutor(agent=function_call_agent, tools=tools, verbose=True)
        else:
            self.agent_executor = initialize_agent(tools=tools, llm=self.llm,
                                                   agent="structured-chat-zero-shot-react-description",
                                                   verbose=True)

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
                data = {'content': chunk['output'], 'type': 'text'}
                yield data


if __name__ == '__main__':
    import json
    from pydantic import BaseModel, Field
    from langchain_core.tools import Tool, StructuredTool, tool


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


    tools = [
        StructuredTool(
            name="add",
            func=add,
            args_schema=AddInputSchema,
            description="将 'x' 和 'y' 相加。",
        ),
        multiply,
        exponentiate,
        Tool(
            name="weather_function",
            func=weather_function,
            description="查询location城市天气",
        )
    ]
    agent = ToolsCallAgent(tools=tools)
    # res = agent.run('3*3=?')
    # print(res)
    # res = agent.run('无锡天气')
    # print(res)
    res = agent.chat('3的5次方加上5乘以3')
    # res = agent.chat('无锡天气')
    for chunk in res:
        print(chunk)
