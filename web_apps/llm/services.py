import pandas as pd
from pandasai import SmartDataframe
from web_apps.llm.agents.pandas_agent import MyPandasAgent, MyCorrectErrorPrompt, MyResponseParser
from web_apps.llm.utils import get_llm
from utils.etl_utils import get_reader_model
from utils.common_utils import gen_json_response, parse_json


def gen_query_info_df(query_info):
    '''
    根据查询信息生成dataframe数据框
    '''
    model_id = query_info.get('id')
    pagesize = int(query_info.get('pagesize', 10000))
    extract_info = {
        'model_id': model_id,
        'extract_rules': parse_json(query_info.get('extract_rules', [])),
        'search_text': query_info.get('search_text', ''),
        'search_type': query_info.get('search_type', '')
    }
    flag, reader = get_reader_model(extract_info)
    if not flag:
        return False, reader
    flag, res_data = reader.read_page(pagesize=pagesize)
    if not flag:
        return False, res_data
    df = pd.DataFrame(res_data['data']['records'])
    return True, df


def parse_output(result, last_code, explanation):
    '''
    解析返回结果
    '''
    res_data = {
        'text': '',
        'data': [],
        'html': '',
    }
    result_text = f"""
{explanation}
根据以上解释，我生成了以下代码并执行:

```python
{last_code}
```

最终结果如下:

"""
    if isinstance(result, str):
        if '<!DOCTYPE html>' in result:
            res_data['html'] = result
        else:
            result_text += str(result)
    if isinstance(result, SmartDataframe):
        df = result.dataframe
        df.fillna("", inplace=True)
        data_li = df.to_dict(orient='records')
        res_data['data'] = data_li
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
    flag, df = gen_query_info_df(query_info)
    if not flag:
        res_data = {
            'text': f'数据查询错误:{df}',
            'data': [],
            'html': '',
        }
        return gen_json_response(data=res_data)
    print(df)
    agent = MyPandasAgent([df], config={
        "llm": _llm,
        "enable_cache": False,
        "open_charts": False,
        "custom_whitelisted_dependencies": ["pyecharts"],
        "custom_prompts": {
            "correct_error": MyCorrectErrorPrompt(),
        },
        "response_parser": MyResponseParser
    })
    question_prompt = "在回答问题前，对回答格式有以下要求：\n" \
                      "1. 若不是返回数据，请使用中文回答对应问题。\n" \
                      "2. 如果问题是绘图相关需求，只允许使用pyecharts库绘制，请直接使用render_embed()函数返回对应html文本\n" \
                      "3. 如果问题是绘图相关需求，禁止使用snapshot_，.render()等保存图像相关函数保存任何内容到本地。\n" \
                      "4. 在生成代码时,保持使用原始数据，禁止使用mock数据\n" \
                      "基于以上要求，请回答以下问题：\n"
    question = f"{question_prompt}{question}"
    result = agent.chat(question)
    last_code = agent.last_code_executed
    explanation = agent.explain()
    response = parse_output(result, last_code, explanation)
    return response


