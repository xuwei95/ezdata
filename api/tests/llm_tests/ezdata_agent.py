from langchain.chat_models import ChatOpenAI
from etl.utils import get_reader
from langchain.agents import Tool, initialize_agent, AgentType, BaseSingleActionAgent
import pandas as pd
import traceback
import time

llm = ChatOpenAI(
    # model_name='moonshot-v1-32k',
    # openai_api_key='REDACTEDdu5tyMlL0CXwifMsKiwo9SKrx2kA3NXhKLB570IHqSJbxy1D',
    # openai_api_base='https://api.moonshot.cn/v1'
    # model_name='gpt-4',
    # openai_api_key='REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69',
    model_name='gpt-3.5-turbo',
    # openai_api_key='REDACTEDo8aZGU6ZubkRrCWcOYZxT3BlbkFJlMjU6aW5NfWevtcvw8od',
    openai_api_key='REDACTED4OS4JM80BdFBpHa9GJmXT3BlbkFJoCFiS6qxVgubbfL6nJcL',
    openai_api_base='https://api.openai-proxy.com/v1'
)

reader_info = {
    'source': {
        "name": "test",
        "type": "mysql",
        "conn_conf": {
            "host": "110.40.157.36",
            "port": 3306,
            "username": "root",
            "password": "ezdata123",
            "database_name": "ezdata"
        },
        "ext_params": {}
    },
    'model': {
        "name": "task_instance",
        "type": "mysql_table",
        "model_conf": {
            "name": "task_instance",
        },
        "ext_params": {},
        "fields": []
    },
    'extract_info': {
        'batch_size': 1000,
        'extract_rules': [],
        'search_text': '',
        'search_type': ''
    }
}

flag, reader = get_reader(reader_info)
print(flag, reader)
flag, res = reader.connect()
print(flag, res)


class EzDataQueryTool:

    def __init__(self, reader):
        self.reader = reader
        self.question = ''
        self.query_code = ''
        self.error_returned = ''

    def get_datasource_metadata(self, prompt):
        '''
        获取待查询数据源中类型，表结构，字段等信息组成prompt
        '''
        print('-----------1-------------', prompt)
        _prompt = self.reader.get_metadata()
        time.sleep(30)
        return _prompt

    def gen_query_code(self, prompt):
        '''
        生成对应的reader取数python代码
        '''
        print('-----------2------------', prompt)
        _prompt = f"""
有一个数据读取对象reader，对象描述为：
{self.reader.__doc__}
使用该reader对象或其内部变量和参数，修改以下格式python函数代码实现数据读取需求,只需要返回此格式代码：

def read_data(reader, page_size=10000):
    '''
    使用reader读取数据，返回pandas DataFrame数据框列表
    :param reader: 数据读取对象
    '''
    dfs = []
    # 此处实现具体数据读取逻辑
    return dfs
        """
        print('-----------2end------------', _prompt)
        time.sleep(30)
        return _prompt

    def run_query_code(self, prompt):
        '''
        执行取数python代码，获取对应结果
        '''
        self.query_code = prompt
        print('-----------3------------', prompt)
        try:
            result = exec(self.query_code)
        except Exception as e:
            print(e)
            result = f'{traceback.format_exc()}  {e.__traceback__.tb_frame.f_globals["__file__"]},error line:{e.__traceback__.tb_lineno}'
            self.error_returned = result
        print('-----------3end------------', result)
        time.sleep(30)
        return result

    def query_exec_tracker(self, prompt):
        '''
        执行取数python代码，获取对应结果
        '''
        print('-----------4------------', prompt)
        _prompt = f'''
You generated this python code:
{self.query_code}

It fails with the following error:
{self.error_returned}

Fix the python code above and return the new python code:
        '''
        time.sleep(30)
        return _prompt


ezdata_query_tool = EzDataQueryTool(reader)
tools = [
    Tool(
        name="get_datasource_metadata_tool",
        description="获取待查询数据源的元数据信息的工具，比如数据库表结构，数据样例等信息",
        func=ezdata_query_tool.get_datasource_metadata
    ),
    Tool(
        name="gen_query_code_tool",
        description="这是一个生成数据查询代码的工具，根据数据读取对象reader的基础信息，包括有哪些参数变量，各变量类型和功能，可以使用哪些方法等信息，返回使用reader查询数据的python代码",
        func=ezdata_query_tool.gen_query_code
    ),
    Tool(
        name="run_query_data_tool",
        description="这是一个执行数据查询代码的工具，运行查询数据的python代码，返回查询结果",
        func=ezdata_query_tool.run_query_code
    ),
    Tool(
        name="query_exec_tracker_tool",
        description="这是一个修正错误数据查询代码的工具，若生成的查询代码运行错误，会提示错误信息并纠正错误，返回正确代码",
        func=ezdata_query_tool.query_exec_tracker
    ),
]
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
res = agent.run("查询表中开始时间大于2024-01-01的记录")
print('--------------------------------')
print(res)


# def llm_query_data(reader, llm, query_prompt, page_size=10000):
#     '''
#     todo: 使用llm查询数据
#     '''
#     flag, res_data = reader.read_page()
#     if not flag:
#         return False, res_data
#     dfs = [pd.DataFrame(res_data['data']['records'])]
#     llm_query_code = """
# flag, res_data = reader.read_page()
# if not flag:
#     return False, res_data
# dfs = [pd.DataFrame(res_data['data']['records'])]
#     """
#     return True, dfs, llm_query_code
