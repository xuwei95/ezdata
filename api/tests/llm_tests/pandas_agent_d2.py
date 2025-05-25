import pandas as pd
from web_apps.llm.agents.pandas_agent import MyPandasAgent, MyCorrectErrorPrompt, MyResponseParser
from langchain.chat_models import ChatOpenAI


llm = ChatOpenAI(
    # model_name='gpt-4',
    # openai_api_key='REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69',
    model_name='gpt-3.5-turbo',
    openai_api_key='REDACTEDo8aZGU6ZubkRrCWcOYZxT3BlbkFJlMjU6aW5NfWevtcvw8od',
    openai_api_base='https://api.openai-proxy.com/v1'
)

df = pd.read_excel('demo.xlsx')
agent = MyPandasAgent([df], config={
    "llm": llm,
    "enable_cache": False,
    "open_charts": False,
    "custom_whitelisted_dependencies": ["pyecharts"],
    "custom_prompts": {
        "correct_error": MyCorrectErrorPrompt(),
    },
    "response_parser": MyResponseParser
})
# question = "返回按月统计收盘价平均值的数据表格"
# question = "振幅最大是哪天，数值是多少"
# question = "根据数据绘制2023年5月份的收盘价随日期的趋势图，不需要展示数字"
# question = "根据数据，绘制k线图，k线图下方绘制macd图，最下方绘制交易量的柱状图(柱子上不要带数字)，注意三个图是分开的，不是整合在一张图里"
# question = "绘制布林带和收盘价的折线图"
# question = "收盘价有多少次跌穿布林带下轨，分别是什么时候和对应的值和布林带下轨值，返回统计表格"
# question = "数据的macd经过了几次金叉，分别是什么时候和对应的值和macd数值，返回统计表格"
# question = "绘制收盘价的折线图,数据点上不要写具体数字,并在macd金叉的数据点做上标记"
# question = "绘制收盘价的折线图,数据点上不要写具体数字"
# question = "根据数据，我有10000本金，给出一个最佳的买卖策略，允许多次买卖，返回每次买卖后的日期，动作，交易额，剩余本金"
# question = "根据数据，我有10000本金，按照macd金叉就买，死叉就卖进行交易，允许多次买卖，返回每次买卖后的日期，动作，交易额，剩余本金"
question = "根据收盘价的趋势使用周期预测算法预测后面30天的价格，返回原数据和预测数据的表格" #绘制趋势图，预测值用虚线表示，数据点不需要写数字
question_prompt = "在回答问题前，对回答格式有以下要求：\n" \
                  "1. 若不是返回数据，请使用中文回答对应问题。\n" \
                  "2. 如果问题是绘图相关需求，只允许使用pyecharts库绘制，" \
                  "请直接使用render_embed()函数返回对应html文本，禁止使用snapshot_相关函数，禁止使用.render()保存任何内容到本地。\n" \
                  "3. 如果问题是绘图相关需求，返回值result的type为string，不要返回plot\n" \
                  "4. 在生成代码时,保持使用原始数据，禁止使用mock数据\n" \
                  "基于以上要求，请回答以下问题：\n"
question = f"{question_prompt}{question}"
print(question)
response = agent.chat(question)
if isinstance(response, str) and '<!DOCTYPE html>' in response:
    f = open('2.html', 'w')
    f.write(response)
res = agent.last_code_executed
print(res)
explain = agent.explain()
print(explain)
print(response)
