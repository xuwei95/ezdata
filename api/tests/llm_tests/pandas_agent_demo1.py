from langchain.llms import OpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
import pandas as pd
# 设置 OpenAI API 密钥
openai_api_key = 'REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69'
llm = OpenAI(temperature=0, model_name='gpt-3.5-turbo', api_key=openai_api_key)  # 初始化LLM模型
df = pd.read_excel('demo.xlsx')
print(df)
agent = create_pandas_dataframe_agent(llm, df, verbose=True)
# response = agent.run("请画一下收盘价的趋势图,横坐标为日期")
# print(response)
# response = agent.run("介绍下数据结构？")
# print(response)
a = df.head()
b = str(a)
print(b)
