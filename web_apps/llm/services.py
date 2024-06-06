import pandas as pd
from web_apps.llm.agents.data_chat_agent import DataChatAgent
from web_apps.llm.utils import get_llm
from utils.etl_utils import get_reader_model
from utils.common_utils import gen_json_response, parse_json


def llm_query_data(reader, llm, query_prompt, max_size=10000):
    '''
    使用llm查询数据
    '''
    agent = DataChatAgent(llm, reader)
    res = agent.run(query_prompt)
    llm_result = agent.llm_result
    return True, res, llm_result


def parse_chat_output(result, llm_result=''):
    '''
    解析llm返回结果
    '''
    res_data = {
        'text': '',
        'data': [],
        'html': '',
    }
    result_text = f"""
{llm_result}

最终结果如下:

"""
    if result['type'] == 'html':
        res_data['html'] = result['value']
    elif result['type'] == 'dataframe':
        df = result['value']
        df.fillna("", inplace=True)
        data_li = df.to_dict(orient='records')
        res_data['data'] = data_li
    else:
        result_text += result['value']
    res_data['text'] = result_text
    return gen_json_response(data=res_data)


def data_chat(req_dict):
    '''
    数据对话功能函数
    '''
    question = req_dict['question']
    query_info = req_dict.get('query_info')
    _llm = get_llm()
    if _llm is None:
        res_data = {
            'text': '未找到对应llm配置!',
            'data': [],
            'html': '',
        }
        return gen_json_response(data=res_data)
    model_id = query_info.get('id')
    extract_info = {
        'model_id': model_id
    }
    flag, reader = get_reader_model(extract_info)
    if not flag:
        res_data = {
            'text': '未找到数据读取对象!',
            'data': [],
            'html': '',
        }
        return gen_json_response(data=res_data)
    agent = DataChatAgent(_llm, reader)
    result = agent.run(question)
    llm_result = agent.llm_result
    response = parse_chat_output(result, llm_result)
    return response


