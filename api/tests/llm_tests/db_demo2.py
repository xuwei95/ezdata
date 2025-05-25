import os
from langchain.chat_models import ChatOpenAI
from pandasai import SmartDataframe
from pandasai.connectors import MySQLConnector
llm = ChatOpenAI(
    # model_name='gpt-4',
    # openai_api_key='REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69',
    model_name='gpt-3.5-turbo',
    openai_api_key='REDACTEDo8aZGU6ZubkRrCWcOYZxT3BlbkFJlMjU6aW5NfWevtcvw8od',
    openai_api_base='https://api.openai-proxy.com/v1'
)
db_user = "root"
db_password = "ezdata123"
db_host = "110.40.157.36"
db_name = "ezdata"

mysql_connector = MySQLConnector(
    config={
        "host": "localhost",
        "port": 3306,
        "database": "mydb",
        "username": "root",
        "password": "root",
        "table": "loans",
        "where": [
            # this is optional and filters the data to
            # reduce the size of the dataframe
            ["loan_status", "=", "PAIDOFF"],
        ],
    }
)

df = SmartDataframe(mysql_connector)
df.chat('What is the total amount of loans in the last year?')
