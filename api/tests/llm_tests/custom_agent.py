from langchain.tools import BaseTool
from math import pi
from typing import Union
class CircumferenceTool(BaseTool):
	# tool名称
    name = "Circumference calculator"
    # 描述此工具能做什么，当LLM语义匹配到该description时，就会执行此tool
    description = "use this tool when you need to calculate a circumference using the radius of a circle"
	# 调用run 时执行此函数
    def _run(self, radius: Union[int, float]):
        return float(radius)*2.0*pi
    # 异步用
    def _arun(self, radius: Union[int, float]):
        raise NotImplementedError("This tool does not support async")


import os
from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'OPENAI_API_KEY'
# initialize LLM (we use ChatOpenAI because we'll later define a `chat` agent)
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    temperature=0,
    model_name='gpt-3.5-turbo'
)
# 缓存 initialize conversational memory
conversational_memory = ConversationBufferWindowMemory(
    memory_key='chat_history',
    k=5,
    return_messages=True
)

from langchain.agents import initialize_agent
tools = [CircumferenceTool()]
# initialize agent with tools
agent = initialize_agent(
    agent='chat-conversational-react-description',
    tools=tools,
    llm=llm,
    verbose=True,
    max_iterations=3,
    early_stopping_method='generate',
    memory=conversational_memory
)
agent("can you calculate the circumference of a circle that has a radius of 7.81mm")


