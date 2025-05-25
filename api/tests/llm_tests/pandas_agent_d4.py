import pandas as pd
from web_apps.llm.agents.pandas_agent import MyPandasAgent, MyCorrectErrorPrompt, MyResponseParser, MyQueryExecTracker
from langchain_community.llms import Xinference
llm = Xinference(
    server_url="http://127.0.0.1:9997",
    model_uid='751cea20-bb49-11ee-a46c-3710ec43af95'
)
df = pd.read_excel('test_data.xlsx')
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
question = "收货人有多少种姓"
# question = "按图书编号分组统计数量，只统计top5，其他归为一类叫其它，画出饼图"
# question = "按收货地址的省份分组统计数量，只统计top5，其他归为一类叫其它，返回统计表格"
# question = "按快递公司分组统计数量，画出统计图"
question_prompt = "在回答问题前，对回答格式有以下要求：\n" \
                  "1. 若不是返回数据，请使用中文回答对应问题。\n" \
                  "2. 如果问题是绘图相关需求，只允许使用pyecharts库绘制，请直接使用render_embed()函数返回对应html文本\n" \
                  "3. 如果问题是绘图相关需求，禁止使用snapshot_，.render()等保存图像相关函数保存任何内容到本地。\n" \
                  "4. 在生成代码时,保持使用原始数据，禁止使用mock数据\n" \
                  "基于以上要求，请回答以下问题：\n"
question = f"{question_prompt}{question}"
print(question)
response = agent.chat(question)
print(response)
if isinstance(response, str) and '<!DOCTYPE html>' in response:
    f = open('3.html', 'w')
    f.write(response)
res = agent.last_code_executed
print(res)
response = agent.explain()
print(response)