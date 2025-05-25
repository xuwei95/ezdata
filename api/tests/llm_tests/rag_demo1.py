from langchain import PromptTemplate
# 设置 OpenAI API 密钥
openai_api_key = 'REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69'
# openai_api_key = 'REDACTEDlQ4aZhsmdAZH8Ibb42mET3BlbkFJQwLbOLT135eKm5bnEgvO'
from langchain.chat_models import ChatOpenAI


llm = ChatOpenAI(
    # model_name='gpt-4',
    # openai_api_key='REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69',
    model_name='gpt-3.5',
    openai_api_key='REDACTEDo8aZGU6ZubkRrCWcOYZxT3BlbkFJlMjU6aW5NfWevtcvw8od',
    openai_api_base='https://api.openai-proxy.com/v1'
)

# 创建模板
template = """
请回答以下问题
{text}
"""

# 创建一个 Lang Chain Prompt 模板，稍后可以插入值
prompt = PromptTemplate(
    input_variables=["text"],
    template=template,
)

confusing_text = """
你是gpt4吗
"""

print("------- Prompt Begin -------")
# 打印模板内容
final_prompt = prompt.format(text=confusing_text)
print(final_prompt)
print("------- Prompt End -------")

output = llm.stream(final_prompt)
print(output)
for i in output:
    print(i)

