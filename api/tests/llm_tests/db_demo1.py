import os
from langchain.agents import *
from langchain.llms import OpenAI
from langchain.sql_database import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
llm = ChatOpenAI(
    # model_name='gpt-4',
    # openai_api_key='REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69',
    model_name='gpt-3.5-turbo-16k-0613',
    openai_api_key='REDACTEDo8aZGU6ZubkRrCWcOYZxT3BlbkFJlMjU6aW5NfWevtcvw8od',
    openai_api_base='https://api.openai-proxy.com/v1'
)
db_user = "root"
db_password = "ezdata123"
db_host = "110.40.157.36"
db_name = "test"
db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True
)
result = agent_executor.run("查找sys_dict_item表中属于sys_dict表中告警等级字典的字典项并返回")
print(result)
