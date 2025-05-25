from langchain.chat_models import ChatOpenAI
from etl.utils import get_reader
import inspect

llm = ChatOpenAI(
    # model_name='gpt-4',
    # openai_api_key='REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69',
    model_name='gpt-3.5-turbo',
    openai_api_key='REDACTEDo8aZGU6ZubkRrCWcOYZxT3BlbkFJlMjU6aW5NfWevtcvw8od',
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
# reader_info = {
#         'model_id': model_id,
#         'extract_rules': parse_json(query_info.get('extract_rules', [])),
#         'search_text': query_info.get('search_text', ''),
#         'search_type': query_info.get('search_type', '')
#     }
# flag, reader = get_reader_model(extract_info)
flag, reader = get_reader(reader_info)
print(flag, reader)
# 获取对象的描述
object_description = reader.__doc__
print("对象描述：")
print(object_description)

# # 获取对象的变量和变量类型
# object_variables = reader.__dict__
# print("对象变量和类型：")
# for variable_name, variable_value in object_variables.items():
#     variable_type = type(variable_value).__name__
#     print(f"{variable_name}: {variable_type}")
#     print('------------------------------------')
#
# # 获取对象变量的描述
# print("对象变量的描述：")
# for variable_name, variable_value in object_variables.items():
#     variable_description = inspect.getdoc(getattr(reader, variable_name))
#     if variable_description:
#         print(f"{variable_name}: {variable_description}")
#         print('------------------------------------')
reader_prompt = f"""
我有一个数据读取对象reader，对象描述为：
{object_description}
"""
query_prompt = '返回日期大于2023-01-01的数据'
prompt_text = f"""
{reader_prompt}
数据读取需求:{query_prompt}
帮我使用该reader对象完善以下python函数，实现以上数据读取需求,只返回python代码
def read_data(reader, page_size=10000):
    '''
    读取数据，返回数据框列表
    :param reader: 数据读取对象
    '''
    dfs = []
    # 读取逻辑
    return dfs
"""
print(prompt_text)
res = llm.invoke(prompt_text)
print(res.content)

# gen_code = f"""
# def read_data(reader, page_size=10000):
#     '''
#     读取数据，返回数据框列表
#     :param reader: 数据读取对象
#     '''
#     dfs = []
#     table = reader.table
#     with reader.db_engine.connect() as conn:
#         query = table.select().limit(10)
#         result = conn.execute(query)
#         for row in result:
#             df = dict(row)
#             dfs.append(df)
#     return dfs
# """
# res = exec(gen_code)
# print(res)
# res = read_data(reader, page_size=10000)
# print(res)

