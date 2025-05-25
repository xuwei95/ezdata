import collections
import random
import requests
import datetime
import pandas as pd
from langchain.tools import Tool, StructuredTool
from langchain.agents import initialize_agent
from langchain.agents import load_tools
from langchain.agents import AgentType
from pydantic import BaseModel, Field
from langchain.chat_models import ChatOpenAI
from langchain_experimental.sql import SQLDatabaseChain

llm = ChatOpenAI(
    # model_name='gpt-4',
    # openai_api_key='REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69',
    model_name='gpt-3.5-turbo',
    openai_api_key='REDACTEDo8aZGU6ZubkRrCWcOYZxT3BlbkFJlMjU6aW5NfWevtcvw8od',
    openai_api_base='https://api.openai-proxy.com/v1'
)
res = llm.invoke('hello')
print(res)