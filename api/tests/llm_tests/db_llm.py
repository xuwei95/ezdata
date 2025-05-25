# 使用自然语言查询一个 SQLite 数据库，我们将使用旧金山树木数据集
# Don't run following code if you don't run sqlite and follow db
from langchain import OpenAI, SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
openai_api_key = 'REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69'
llm = OpenAI(temperature=0, api_key=openai_api_key)

db = SQLDatabase.from_uri(f"mysql+pymysql://root:ezdata123@110.40.157.36:3306/ezdata")

db_chain = SQLDatabaseChain(llm=llm, database=db, verbose=True)
result = db_chain.run("select name from user")
print(result)
