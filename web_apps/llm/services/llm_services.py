import json
from langchain_core.messages import AIMessage, HumanMessage
from web_apps import app
from web_apps.llm.agents.data_extract_agent import DataExtractAgent
from web_apps.llm.llm_utils import get_llm
from utils.common_utils import gen_json_response, gen_uuid, get_now_time, parse_json
from utils.auth import get_auth_token_info
from web_apps.rag.services.rag_service import get_knowledge
from web_apps.llm.tools import tools_map
from web_apps.llm.tools import get_tools
from web_apps.llm.tools.data_tools import get_chat_data_tools, get_chat_data_tool
from web_apps.llm.agents.tools_call_agent import ToolsCallAgent
from web_apps.llm.services.conversation_service import get_or_create_conversation, get_messages, add_message
from web_apps.llm.tools.memory_tools import get_memory_tools


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


def format_history(messages):
    history_str = []
    for msg in messages:
        prefix = "Human" if isinstance(msg, HumanMessage) else "AI"
        history_str.append(f"{prefix}: {msg.content}")
    return "\n".join(history_str[-6:])  # 保留最近3轮对话（每轮2条）


def prepare_chat_context(req_dict, is_web=True):
    message = req_dict.get('message', '')
    conversation_id = req_dict.get('topicId', '')
    chat_config = parse_json(req_dict.get('chatConfig'), {})
    data_chat_config = parse_json(chat_config.get('data_chat'), {})
    data_chat_enable = data_chat_config.get('enable', False)
    # 查询知识库，若有相关知识，改写prompt
    knowledge = ''
    rag_config = parse_json(chat_config.get('rag'), {})
    rag_enable = rag_config.get('enable', False)
    if rag_enable:
        rag_metadata = parse_json(chat_config.get('rag'), {'dataset_id': '1'})
        if data_chat_enable:
            # 若开启数据对话，将相应数据模型加入知识查询列表
            rag_metadata['datamodel_id'] = data_chat_config.get('datamodel_id', '')
        knowledge = get_knowledge(message, metadata=rag_metadata)
    llm = get_llm({'conversation_id': conversation_id})
    # 记忆相关配置
    core_memory = ''
    memory_config = parse_json(chat_config.get('memory'), {})
    memory_enable = memory_config.get('enable', True)
    # 构建对话历史（LangChain 消息对象格式）
    chat_history = []
    if memory_enable:
        if is_web:
            user_info = get_auth_token_info()
        else:
            user_info = {
                'user_id': 0,
                'user_name': 'test'
            }
        user_name = user_info.get('username')
        user_id = user_info.get('id')
        meta_data = {
            'user_id': user_id,
            'user_name': user_name
        }
        conversation = get_or_create_conversation(conversation_id, meta_data)
        core_memory = conversation.core_memory
        # 获取历史消息（最近的3条）
        history_messages = get_messages(conversation_id, size=3)
        # 转换为 LangChain Message 对象
        for msg in history_messages:
            chat_history.append(HumanMessage(content=msg["question"]))
            chat_history.append(AIMessage(content=msg["answer"]))
    # 处理知识库部分
    if knowledge != '':
        knowledge_section = f"结合知识库信息，回答用户的问题，若知识库中无相关信息，请尝试直接回答。\n知识库：{knowledge}\n"
    else:
        knowledge_section = ''
    # 处理核心记忆部分
    if core_memory != '':
        core_memory_section = f"[核心记忆]\n{core_memory}\n\n"
    else:
        core_memory_section = ''
    history_section = format_history(chat_history) if chat_history else ""
    history_part = (
        f"对话历史：\n{history_section}\n\n"
        if history_section
        else ""
    )
    # 组合最终提示
    prompt = (
        f"{core_memory_section}"
        f"{history_part}"
        f"{knowledge_section}"
        "当前对话：\n"
        f"Human: {message}\n"
        "AI:"
    )
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
    if memory_enable:
        # 若开启记忆模块，添加记忆工具
        agent_enable = True
        memory_tools = get_memory_tools(conversation_id)
        tools = tools + memory_tools
    return prompt, llm, agent_enable, tools, conversation_id


def chat_generate(req_dict, is_web=True):
    '''
    流式对话
    '''
    message = req_dict['message']
    prompt, llm, agent_enable, tools, conversation_id = prepare_chat_context(req_dict, is_web)
    answer = ''
    if agent_enable and tools != []:
        # agent工具调用模式
        agent = ToolsCallAgent(tools, llm=llm)
        for chunk in agent.chat(prompt):
            if chunk['type'] == 'text':
                answer += chunk['content']
            t = f"id:{conversation_id}\ndata:{json.dumps(chunk, ensure_ascii=False)}"
            yield f"{t}\n\n"
    else:
        # 直接使用llm回答
        for c in llm.stream(prompt):
            data = {'content': c.content, 'type': 'text'}
            answer += c.content
            t = f"id:{conversation_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
            yield f"{t}\n\n"
    add_message(conversation_id, message, answer)
    yield f"id:[DONE]\ndata:[DONE]\n\n"


def chat_run(req_dict):
    '''
    返回对话结果
    '''
    prompt, llm, agent_enable, tools, _ = prepare_chat_context(req_dict)
    if agent_enable and tools != []:
        # agent工具调用模式
        agent = ToolsCallAgent(tools, llm=llm)
        output = agent.run(prompt)
    else:
        # 直接使用llm回答
        output = llm.invoke(prompt).content
    if isinstance(output, dict) and 'content' in output and 'type' in output:
        # 若是其他agent的输出格式，直接返回
        return output
    else:
        return {'content': output, 'type': 'text'}


def data_chat_generate(req_dict):
    '''
    数据对话-流式接口
    '''
    message = req_dict['message']
    model_id = req_dict.get('model_id', '')
    conversation_id = req_dict.get('topicId', gen_uuid())
    _llm = get_llm()
    if _llm is None:
        data = {'content': '未找到对应llm配置!', 'type': 'text'}
        t = f"id:{conversation_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
        yield f"{t}\n\n"
        yield f"id:[ERR]\ndata:[ERR]\n\n"
        return
    data_tool = get_chat_data_tool(model_id, is_chat=True)
    if data_tool is None:
        for c in _llm.stream(message):
            data = {'content': c.content, 'type': 'text'}
            t = f"id:{conversation_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
            yield f"{t}\n\n"
    else:
        data = {'content': {'title': '检索知识库', 'content': '正在检索知识库', 'time': get_now_time(res_type='datetime')},
                'type': 'flow'}
        t = f"id:{conversation_id}\ndata:{json.dumps(data, ensure_ascii=False)}"
        yield f"{t}\n\n"
        # 检索知识库中相关知识
        knowledge = get_knowledge(message, metadata={'datamodel_id': model_id})
        data_tool.knowledge = knowledge
        agent = ToolsCallAgent([data_tool], llm=_llm)
        for chunk in agent.chat(message):
            t = f"id:{conversation_id}\ndata:{json.dumps(chunk, ensure_ascii=False)}"
            yield f"{t}\n\n"
    yield f"id:[DONE]\ndata:[DONE]\n\n"


if __name__ == '__main__':
    req_dict = {
        'topicId': 'test0002',# '8a862fdf980245459ac9ef89734c1601',
        "message": '9.11和9.9哪个大',# '我喜欢弹钢琴',  # 查询sys_dict 表前10条数据
        "chatConfig": {
            "rag": {
                "enable": False,
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
                "enable": False,
                "datamodel_id": ["8a862fdf980245459ac9ef89734c166f", "22016439fbd0431887641544a0cf5cf4"]
            },
            "memory": {
                "enable": True
            }
        }
    }
    with app.app_context():
        for i in chat_generate(req_dict, False):
            print(i)
        req_dict['message'] = '我刚才说了啥'
        for i in chat_generate(req_dict, False):
            print(i)
