import pandas as pd
from web_apps.llm.agents.data_extract_agent import DataExtractAgent
from web_apps.llm.agents.data_analysis_agent import DataAnalysisAgent
from web_apps.llm.utils import get_llm
from utils.etl_utils import get_reader_model
from utils.common_utils import gen_json_response, parse_json


def llm_query_data(reader, llm, query_prompt, max_size=10000):
    '''
    使用llm查询数据
    '''
    agent = DataExtractAgent(llm, reader)
    res = agent.run(query_prompt)
    llm_result = agent.llm_result
    return True, res, llm_result


def gen_query_info_dfs(query_info, llm):
    '''
    根据查询信息生成dataframe数据框
    '''
    model_id = query_info.get('id')
    pagesize = int(query_info.get('pagesize', 10000))
    ai_query = query_info.get('ai_query', False)
    query_prompt = query_info.get('query_prompt', '')
    extract_info = {
        'model_id': model_id,
        'extract_rules': parse_json(query_info.get('extract_rules', [])),
        'search_text': query_info.get('search_text', ''),
        'search_type': query_info.get('search_type', '')
    }
    flag, reader = get_reader_model(extract_info)
    if not flag:
        return False, reader, ''
    if ai_query and query_prompt != '':
        _flag, res, llm_result = llm_query_data(reader, llm, query_prompt, max_size=pagesize)
        return True, res['value'], llm_result
    else:
        flag, res_data = reader.read_page(pagesize=pagesize)
        if not flag:
            return False, res_data, ''
        dfs = [pd.DataFrame(res_data['data']['records'])]
        return True, dfs, ''


def parse_output(result, llm_result='', llm_query_result=''):
    '''
    解析返回结果
    '''
    res_data = {
        'text': '',
        'data': [],
        'html': '',
    }
    result_text = f"""
{llm_query_result}
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
    flag, dfs, llm_query_result = gen_query_info_dfs(query_info, _llm)
    if not flag:
        res_data = {
            'text': f'数据抽取错误:{dfs}',
            'data': [],
            'html': '',
        }
        return gen_json_response(data=res_data)
    print(dfs)
    agent = DataAnalysisAgent(_llm, dfs)
    result = agent.run(question)
    llm_result = agent.llm_result
    response = parse_output(result, llm_result, llm_query_result)
    return response


