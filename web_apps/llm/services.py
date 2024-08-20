import json
from web_apps import app
from web_apps.llm.agents.data_chat_agent import DataChatAgent
from web_apps.llm.agents.data_extract_agent import DataExtractAgent
from web_apps.llm.utils import get_llm
from utils.etl_utils import get_reader_model
from utils.common_utils import gen_json_response, gen_uuid, get_now_time
from web_apps.rag.services.rag_service import get_star_qa_answer, get_knowledge
from web_apps.llm.tools import tools_map


def get_tool_list():
    '''
    获取工具列表
    '''
    result = []
    for k, v in tools_map.items():
        dic = {
            'name': v['name'],
            'value': k
        }
        result.append(dic)
    return gen_json_response(data=result)


def llm_query_data(reader, llm, query_prompt):
    '''
    使用llm查询数据
    '''
    agent = DataExtractAgent(llm, reader)
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


def data_chat_generate(req_dict):
    '''
    数据对话-流式接口
    '''
    with app.app_context():
        message = req_dict['message']
        model_id = req_dict.get('model_id', '')
        topic_id = req_dict.get('topicId', gen_uuid())
        _llm = get_llm()
        if _llm is None:
            data = {'content': '未找到对应llm配置!', 'type': 'text'}
            t = f"id:{topic_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
            yield f"{t}\n\n"
            yield f"id:[ERR]\ndata:[ERR]\n\n"
            return
        flag, reader = get_reader_model({'model_id': model_id})
        if not flag:
            data = {'content': '未找到数据读取对象!', 'type': 'text'}
            t = f"id:{topic_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
            yield f"{t}\n\n"
            yield f"id:[ERR]\ndata:[ERR]\n\n"
        else:
            data = {'content': {'title': '检索知识库', 'content': '正在检索知识库', 'time': get_now_time(res_type='datetime')},
                    'type': 'flow'}
            t = f"id:{topic_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
            yield f"{t}\n\n"
            # 查询知识库中是否有已标记的正确答案
            answer = get_star_qa_answer(message, metadata={'datamodel_id': model_id})
            # 检索知识库中相关知识
            knowledge = get_knowledge(message, metadata={'datamodel_id': model_id})
            agent = DataChatAgent(_llm, reader, knowledge=knowledge, answer=answer)
            for data in agent.chat(message):
                t = f"id:{topic_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
                yield f"{t}\n\n"
            yield f"id:[DONE]\ndata:[DONE]\n\n"
