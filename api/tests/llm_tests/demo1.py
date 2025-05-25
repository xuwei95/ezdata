import openai

# 设置 OpenAI API 密钥
openai.api_key = 'REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69'
# openai.api_key = 'REDACTEDqLeIE1jcqOyZJW0Lz6m4T3BlbkFJDHr4p4fcdxfGBXuwcsY4'

# 定义聊天对话
chat_history = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Who won the world series in 2020?"},
    # {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
    {"role": "user", "content": "Where was it played?"}
]

# 发送聊天请求
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=chat_history
)

# 提取助手的回复
assistant_reply = response['choices'][0]['message']['content']

print("Assistant: " + assistant_reply)
