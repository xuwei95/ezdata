import json
from web_apps import app
from web_apps.llm.agents.data_chat_agent import DataChatAgent
from web_apps.llm.agents.data_extract_agent import DataExtractAgent
from web_apps.llm.llm_utils import get_llm
from utils.etl_utils import get_reader_model
from utils.common_utils import gen_json_response, gen_uuid, get_now_time, parse_json
from web_apps.rag.services.rag_service import get_star_qa_answer, get_knowledge
from web_apps.llm.tools import tools_map
from web_apps.llm.tools import get_tools
from web_apps.llm.tools.data_tools import get_chat_data_tools
from web_apps.llm.agents.tools_call_agent import ToolsCallAgent


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


def chat_generate(req_dict):
    with app.app_context():
        message = req_dict.get('message', '')
        topic_id = req_dict.get('topicId', '')
        chat_config = parse_json(req_dict.get('chatConfig'), {})
        prompt = message
        data_chat_config = parse_json(chat_config.get('data_chat'), {})
        data_chat_enable = data_chat_config.get('enable', False)
        # 查询知识库，若有相关知识，改写prompt
        rag_config = parse_json(chat_config.get('rag'), {})
        rag_enable = rag_config.get('enable', False)
        if rag_enable:
            rag_metadata = parse_json(chat_config.get('rag'), {'dataset_id': '1'})
            if data_chat_enable:
                # 若开启数据对话，将相应数据模型加入知识查询列表
                rag_metadata['datamodel_id'] = data_chat_config.get('datamodel_id', '')
            knowledge = get_knowledge(message, metadata=rag_metadata)
            if knowledge != '':
                prompt = f"结合知识库信息，回答用户的问题,若知识库中无相关信息，请尝试直接回答。\n知识库：{knowledge}\n用户问题：{message}\n回答："
        llm = get_llm(conversation_id=topic_id)
        # 判断是否使用工具调用
        agent_config = parse_json(chat_config.get('agent'), {})
        agent_enable = agent_config.get('enable', False)
        tools = agent_config.get('tools', [])
        tools = get_tools(tools)
        if data_chat_enable:
            # 若开启数据对话，将数据对话工具加入工具列表
            agent_enable = True
            datamodel_id = data_chat_config.get('datamodel_id', '')
            datamodel_ids = datamodel_id.split(',') if isinstance(datamodel_id, str) else datamodel_id
            data_chat_tools = get_chat_data_tools(datamodel_ids)
            tools = tools + data_chat_tools
        if agent_enable and tools != []:
            # agent工具调用模式
            agent = ToolsCallAgent(tools, llm=llm)
            for chunk in agent.chat(prompt):
                t = f"id:{topic_id}\ndata:{json.dumps(chunk, ensure_ascii=False)}"
                yield f"{t}\n\n"
        else:
            # 直接使用llm回答
            for c in llm.stream(prompt):
                data = {'content': c.content, 'type': 'text'}
                t = f"id:{topic_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
                yield f"{t}\n\n"
        yield f"id:[DONE]\ndata:[DONE]\n\n"


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


if __name__ == '__main__':
    req_dict = {
        "message": '查询sys_dict 表前10条数据',
        "chatConfig": {
            "rag": {
                "enable": True,
                "dataset_id": ["1"],
                "k": 3,
                "retrieval_type": "vector",
                "score_threshold": 0.1,
                "rerank": "0",
                "rerank_score_threshold": 0
            },
            "agent": {
                "enable": False,
                "tools": []
            },
            "data_chat": {
                "enable": True,
                "datamodel_id": ["8a862fdf980245459ac9ef89734c166f", "22016439fbd0431887641544a0cf5cf4"]
            }
        }
    }
    for i in chat_generate(req_dict):
        print(i)
