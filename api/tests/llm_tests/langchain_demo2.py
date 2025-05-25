from langchain.llms import OpenAI, ChatGLM
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate
# 设置 OpenAI API 密钥
# openai_api_key = 'REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69'
openai_api_key = 'REDACTEDo8aZGU6ZubkRrCWcOYZxT3BlbkFJlMjU6aW5NfWevtcvw8od'
llm = OpenAI(temperature=0, model_name='gpt-3.5-turbo', api_key=openai_api_key, api_base='https://api.openai-proxy.com/v1')  # 初始化LLM模型
llm = ChatOpenAI(
            model_name='gpt-3.5-turbo',
            openai_api_key=openai_api_key,
            openai_api_base='https://api.openai-proxy.com/v1'
        )
# 创建模板
template = """
请回答以下问题：
{text}
"""

# 创建一个 Lang Chain Prompt 模板，稍后可以插入值
prompt = PromptTemplate(
    input_variables=["text"],
    template=template,
)
confusing_text = """
1/0等于多少
"""
print("------- Prompt Begin -------")
# 打印模板内容
final_prompt = prompt.format(text=confusing_text)
print(final_prompt)

print("------- Prompt End -------")


output = llm(final_prompt)
print(output)

