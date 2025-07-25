import json
from langchain_core.messages import AIMessage, HumanMessage
from web_apps import app
from web_apps.llm.agents.data_extract_agent import DataExtractAgent
from web_apps.llm.llm_utils import get_llm
from utils.common_utils import gen_json_response, gen_uuid, get_now_time, parse_json
from web_apps.rag.services.rag_service import get_knowledge
from web_apps.llm.tools import tools_map
from web_apps.llm.tools import get_tools
from web_apps.llm.tools.data_tools import get_chat_data_tools, get_chat_data_tool
from web_apps.llm.agents.tools_call_agent import ToolsCallAgent
from web_apps.llm.services.conversation_service import get_or_create_conversation, get_messages, add_message
from web_apps.llm.tools.memory_tools import get_memory_tools
from web_apps.llm.services.conversation_service import add_archival_memory


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


def generate_history_summary(messages, llm=None):
    if llm is None:
        llm = get_llm()
    history_text = "\n".join([f"{m['question']}\n{m['answer']}" for m in messages])
    return llm.invoke(
        "请将以下对话历史压缩成一段保留核心事实的摘要，"
        "用第三人称表述且保留数据细节：\n" + history_text
    ).content

def generate_prompt(content):
    llm = get_llm()
    prompt = f"请为以下内容:\n{content}\n\n生成一个详细格式的llm prompt,只返回prompt，不要其他内容"
    for c in llm.stream(prompt):
        msg = {
            "conversationId": '',
            "data": {
                "message": c.content
            },
            "event": "MESSAGE"
        }
        t = f"data:{json.dumps(msg, ensure_ascii=False)}"
        yield f"{t}\n\n"
    msg = {
        "conversationId": '',
        "data": None,
        "event": "MESSAGE_END"
    }
    t = f"data:{json.dumps(msg, ensure_ascii=False)}"
    yield f"{t}\n\n"


class ChatHandler:
    def __init__(self, req_dict):
        self.req_dict = req_dict
        self.conversation_id = req_dict.get('conversationId', '')
        self.chat_config = parse_json(req_dict.get('chatConfig'), {})
        self.message = req_dict.get('message', '')
        self.metadata = json.loads(self.chat_config.get('metadata', '{}'))
        self.llm = get_llm({'conversation_id': self.conversation_id, **self.metadata})
        self.system_prompt = self.chat_config.get('prompt', '')
        self.history_size = self.chat_config.get('msgNum', 3)

    def prepare_context(self, user_info = None):
        if user_info is None:
            user_info = {'id': 0, 'user_name': 'test'}
        """准备聊天上下文，返回(prompt, llm, agent_enable, tools)"""
        # 处理数据对话配置
        datamodelIds = self.chat_config.get('datamodelIds', 'e222b61c62be4d09908a5bc94aebf22d')
        knowledgeIds = self.chat_config.get('knowledgeIds', '')
        toolIds = self.chat_config.get('toolIds', '')
        # 处理知识库
        knowledge = ''
        if knowledgeIds != '':
            rag_metadata = parse_json({'daset_id': knowledgeIds}, {'dataset_id': '1'})
            if datamodelIds:
                rag_metadata['datamodel_id'] = datamodelIds
            if self.metadata.get('topNumber'):
                rag_metadata['k'] = self.metadata.get('topNumber')
            if self.metadata.get('similarity'):
                rag_metadata['score_threshold'] = self.metadata.get('similarity')
            knowledge = get_knowledge(self.message, metadata=rag_metadata)
        # 处理记忆配置
        memory_enable = self.metadata.get('multiSession', '0') == '1'
        core_memory = ''
        chat_history = []

        if memory_enable:
            # 获取对话历史
            conversation = get_or_create_conversation(
                self.conversation_id,
                {'user_id': user_info.get('id'), 'user_name': user_info.get('username')}
            )
            core_memory = conversation.core_memory
            history_messages, _ = get_messages(self.conversation_id, page=1, size=self.history_size)
            for msg in history_messages:
                chat_history.extend([HumanMessage(content=msg["question"]), AIMessage(content=msg["answer"])])
        # 构建prompt各部分
        knowledge_section = f"结合知识库信息，回答用户的问题，若知识库中无相关信息，请尝试直接回答。\n知识库：{knowledge}\n" if knowledge else ''
        core_memory_section = f"[核心记忆]\n{core_memory}\n\n" if core_memory else ''
        history_section = format_history(chat_history) if chat_history else ""
        history_part = f"对话历史：\n{history_section}\n\n" if history_section else ""
        system_part = f"System: {self.system_prompt}\n\n"  if self.system_prompt else ''
        prompt = (
            f"{system_part}"
            f"{core_memory_section}"
            f"{history_part}"
            f"{knowledge_section}"
            "当前对话：\n"
            f"Human: {self.message}\n"
            "AI:"
        )
        # 处理工具配置
        tools = []
        agent_enable = toolIds != ''
        # 数据对话工具
        if datamodelIds:
            datamodel_ids = datamodelIds.split(',') if isinstance(datamodelIds, str) else datamodelIds
            tools += get_chat_data_tools(datamodel_ids)
            agent_enable = True
        # 记忆工具
        if memory_enable:
            tools += get_memory_tools(self.conversation_id)
            agent_enable = True
        # 其他工具
        tools += get_tools(toolIds)
        return prompt, self.llm, agent_enable, tools

    def handle_chat_close(self, answer):
        if answer != '':
            add_message(self.conversation_id, self.message, answer)
            memory_enable = self.metadata.get('multiSession', '0') == '1'
            if memory_enable:
                history_messages, total = get_messages(self.conversation_id, page=1, size=self.history_size)
                # 当消息总数达到分页尺寸倍数时触发归档
                if total > self.history_size and total % self.history_size == 0:
                    archived_messages, _ = get_messages(
                        self.conversation_id,
                        page=2,
                        size=self.history_size
                    )
                    if archived_messages:
                        # 生成结构化摘要
                        summary = generate_history_summary(archived_messages, self.llm)
                        # 添加记忆到归档存储
                        add_archival_memory(self.conversation_id, summary)


def chat_generate(req_dict, user_info=None):
    '''
    流式对话
    '''
    with app.app_context():
        chat_handler = ChatHandler(req_dict)
        conversation_id = chat_handler.conversation_id
        answer = ''
        try:
            prompt, llm, agent_enable, tools = chat_handler.prepare_context(user_info)
            if agent_enable and tools != []:
                # agent工具调用模式
                agent = ToolsCallAgent(tools, llm=llm)
                for chunk in agent.chat(prompt):
                    if chunk['type'] == 'text':
                        answer += chunk['content']
                    event_type_map = {
                        'text': "MESSAGE",
                        'html': "HTML",
                        'data': "DATATABLE",
                        'step': "STEP",
                        'flow': "STEP"
                    }
                    msg = {
                        "conversationId": conversation_id,
                        "data": {
                            "message": chunk['content']
                        },
                        "event": event_type_map.get(chunk['type'], "MESSAGE")
                    }
                    t = f"data:{json.dumps(msg, ensure_ascii=False)}"
                    yield f"{t}\n\n"
            else:
                # 直接使用llm回答
                for c in llm.stream(prompt):
                    answer += c.content
                    msg = {
                        "conversationId": conversation_id,
                        "data": {
                            "message": c.content
                        },
                        "event": "MESSAGE"
                    }
                    t = f"data:{json.dumps(msg, ensure_ascii=False)}"
                    yield f"{t}\n\n"
            msg = {
                "conversationId": conversation_id,
                "data": None,
                "event": "MESSAGE_END"
            }
            t = f"data:{json.dumps(msg, ensure_ascii=False)}"
            yield f"{t}\n\n"

        except Exception as e:
            msg = {
                "conversationId": conversation_id,
                "data": {
                    "message": str(e)
                },
                "event": "ERROR"
            }
            yield f"data:{json.dumps(msg, ensure_ascii=False)}\n\n"
        finally:
            chat_handler.handle_chat_close(answer)

def chat_run(req_dict, user_info=None):
    '''
    返回对话结果
    '''
    with app.app_context():
        chat_handler = ChatHandler(req_dict)
        answer = ''
        try:
            prompt, llm, agent_enable, tools = chat_handler.prepare_context(user_info)
            if agent_enable and tools != []:
                # agent工具调用模式
                agent = ToolsCallAgent(tools, llm=llm)
                output = agent.run(prompt)
            else:
                # 直接使用llm回答
                output = llm.invoke(prompt).content
            if isinstance(output, dict) and 'content' in output and 'type' in output:
                if output['type'] == 'text':
                    answer += output['content']
                # 若是其他agent的输出格式，直接返回
                return output
            else:
                answer = output
                return {'content': output, 'type': 'text'}
        except Exception as e:
            return {'content': f'处理出错：{e}', 'type': 'text'}
        finally:
            chat_handler.handle_chat_close(answer)


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
        'topicId': 'test0007',  # '8a862fdf980245459ac9ef89734c1601',
        "message": '9.11和9.9哪个大',  # '我喜欢弹钢琴',  # 查询sys_dict 表前10条数据
        "chatConfig": {
            # "rag": {
            #     "enable": False,
            #     "dataset_id": ["1"],
            #     "k": 3,
            #     "retrieval_type": "vector",
            #     "score_threshold": 0.1,
            #     "rerank": "0",
            #     "rerank_score_threshold": 0
            # },
            # "agent": {
            #     "enable": False,
            #     "tools": []
            # },
            # "data_chat": {
            #     "enable": False,
            #     "datamodel_id": ["8a862fdf980245459ac9ef89734c166f", "22016439fbd0431887641544a0cf5cf4"]
            # },
            # "memory": {
            #     "enable": True
            # }
        }
    }
    with app.app_context():
        # chat_run(req_dict, False)
        for i in chat_generate(req_dict, False):
            print(i)
    #     messages = '''
    # 我的爱好是弹琴。
    # 我在阿里巴巴干活
    # 我喜欢吃西瓜。
    # 帮我写一句给朋友的生日祝福语，简短一点。
    # 今天下午吃什么水果好？
    # 我在哪里上班
    # 我最近跳槽去了美团。
    # 我还喜欢吃桃子和苹果。
    # 我不喜欢吃椰子。
    # 我在哪里上班
    # 你知道我有什么乐器爱好吗？
    #         '''
    #     messages = messages.split('\n')
    #     for message in messages:
    #         if message != '':
    #             req_dict['message'] = message
    #             for i in chat_generate(req_dict, False):
    #                 print(i)
