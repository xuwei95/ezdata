import json
import traceback
from langchain_core.messages import AIMessage, HumanMessage
from web_apps import app
from web_apps.llm.agents.data_extract_langgraph import DataExtractLangGraph as DataExtractAgent
from web_apps.llm.llm_utils import get_llm
from utils.common_utils import gen_json_response, gen_uuid, get_now_time, parse_json
from web_apps.rag.services.rag_service import get_knowledge
from web_apps.llm.tools import tools_map
from web_apps.llm.tools import get_tools
from web_apps.llm.tools.data_tools import get_chat_data_tools, get_chat_data_tool
from web_apps.llm.agents.tools_call_langgraph import ToolsCallAgent
from web_apps.llm.services.conversation_service import get_or_create_conversation, get_messages, add_message
from web_apps.llm.tools.memory_tools import get_memory_tools
from web_apps.llm.services.conversation_service import add_archival_memory


# 事件类型映射（统一管理）
EVENT_TYPE_MAP = {
    'text': "MESSAGE",
    'html': "HTML",
    'data': "DATATABLE",
    'step': "STEP",
    'flow': "STEP"
}


def format_stream_event(conversation_id, chunk, event_type=None):
    """
    统一的流式事件格式化函数

    Args:
        conversation_id: 会话ID
        chunk: 数据块（可以是 dict 或 str）
        event_type: 事件类型（如果为None，从chunk中推断）

    Returns:
        格式化的 SSE 事件字符串
    """
    if isinstance(chunk, dict):
        # Agent 输出格式: {'content': ..., 'type': ...}
        content = chunk.get('content', '')
        chunk_type = chunk.get('type', 'text')
        event = event_type or EVENT_TYPE_MAP.get(chunk_type, "MESSAGE")
    else:
        # 字符串内容
        content = chunk
        event = event_type or "MESSAGE"

    msg = {
        "conversationId": conversation_id,
        "data": {
            "message": content
        },
        "event": event
    }
    return f"data:{json.dumps(msg, ensure_ascii=False)}\n\n"


def format_end_event(conversation_id):
    """格式化结束事件"""
    msg = {
        "conversationId": conversation_id,
        "data": None,
        "event": "MESSAGE_END"
    }
    return f"data:{json.dumps(msg, ensure_ascii=False)}\n\n"


def format_error_event(conversation_id, error_message):
    """格式化错误事件"""
    msg = {
        "conversationId": conversation_id,
        "data": {
            "message": error_message
        },
        "event": "ERROR"
    }
    return f"data:{json.dumps(msg, ensure_ascii=False)}\n\n"


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
        self.conversation_id = req_dict.get('conversationId')
        if not self.conversation_id:
            self.conversation_id = gen_uuid()
        self.app_id = req_dict.get('appId', '')
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
        datamodelIds = self.chat_config.get('datamodelIds', '')
        knowledgeIds = self.chat_config.get('knowledgeIds', '')
        toolIds = self.chat_config.get('toolIds', '')
        # 处理知识库
        knowledge = ''
        if knowledgeIds != '':
            rag_metadata = parse_json({'dataset_id': knowledgeIds}, {'dataset_id': '1'})
            if datamodelIds:
                rag_metadata['datamodel_id'] = datamodelIds
            if self.metadata.get('topNumber'):
                rag_metadata['k'] = self.metadata.get('topNumber')
            if self.metadata.get('similarity'):
                rag_metadata['score_threshold'] = self.metadata.get('similarity')
            knowledge = get_knowledge(self.message, metadata=rag_metadata)
        # 处理记忆配置
        memory_enable = self.metadata.get('multiSession')
        core_memory = ''
        chat_history = []
        conversation = get_or_create_conversation(
            self.conversation_id,
            {'user_id': user_info.get('id'), 'user_name': user_info.get('username'), 'message': self.message, 'app_id': self.app_id}
        )
        # 获取对话历史
        history_messages, _ = get_messages(self.conversation_id, page=1, size=self.history_size)
        for msg in history_messages:
            chat_history.extend([HumanMessage(content=msg["question"]), AIMessage(content=msg["answer"])])
        if memory_enable:
            core_memory = conversation.core_memory
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
    流式对话 - 使用 LangGraph Agent 架构

    工作流程：
    1. 准备上下文（知识库、记忆、历史）
    2. 路由执行：
       - 如果有工具 → ToolsCallAgent (LangGraph)
       - 否则 → 直接 LLM 流式回答
    3. 统一格式化输出
    '''
    with app.app_context():
        chat_handler = ChatHandler(req_dict)
        conversation_id = chat_handler.conversation_id
        answer = ''

        try:
            # 1. 准备上下文
            prompt, llm, agent_enable, tools = chat_handler.prepare_context(user_info)

            # 2. 路由执行
            if agent_enable and tools:
                # Agent 模式：使用 LangGraph ToolsCallAgent
                agent = ToolsCallAgent(
                    tools=tools,
                    llm=llm,
                    system_prompt=chat_handler.system_prompt
                )

                for chunk in agent.chat(prompt):
                    # 收集文本答案（用于保存）
                    if chunk.get('type') == 'text':
                        answer += str(chunk.get('content', ''))

                    # 统一格式化输出
                    yield format_stream_event(conversation_id, chunk)

            else:
                # 直接 LLM 模式：流式回答
                for c in llm.stream(prompt):
                    answer += c.content
                    yield format_stream_event(conversation_id, c.content)

            # 3. 输出结束事件
            yield format_end_event(conversation_id)

        except Exception as e:
            # 错误处理
            error_msg = f"处理出错: {str(e)}\n{traceback.format_exc()}"
            yield format_error_event(conversation_id, error_msg)
        finally:
            # 保存对话历史和记忆
            chat_handler.handle_chat_close(answer)

def chat_run(req_dict, user_info=None):
    '''
    同步对话 - 返回完整结果（使用 LangGraph 架构）

    工作流程：
    1. 准备上下文（知识库、记忆、历史）
    2. 路由执行：
       - 如果有工具 → ToolsCallAgent (LangGraph)
       - 否则 → 直接 LLM 回答
    3. 返回统一格式结果
    '''
    with app.app_context():
        chat_handler = ChatHandler(req_dict)
        answer = ''

        try:
            # 1. 准备上下文
            prompt, llm, agent_enable, tools = chat_handler.prepare_context(user_info)

            # 2. 路由执行
            if agent_enable and tools:
                # Agent 模式：使用 LangGraph ToolsCallAgent
                agent = ToolsCallAgent(
                    tools=tools,
                    llm=llm,
                    system_prompt=chat_handler.system_prompt
                )
                output = agent.run(prompt)
            else:
                # 直接 LLM 模式
                output = llm.invoke(prompt).content

            # 3. 处理返回结果
            if isinstance(output, dict) and 'content' in output and 'type' in output:
                # Agent 返回的格式化结果
                if output['type'] == 'text':
                    answer = str(output['content'])
                return output
            else:
                # 字符串结果，转换为统一格式
                answer = str(output)
                return {'content': answer, 'type': 'text'}

        except Exception as e:
            error_msg = f'处理出错：{str(e)}\n{traceback.format_exc()}'
            return {'content': error_msg, 'type': 'text'}

        finally:
            # 保存对话历史
            chat_handler.handle_chat_close(answer)


def data_chat_generate(req_dict):
    '''
    数据对话 - 流式接口（使用 LangGraph 架构）

    工作流程：
    1. 验证 LLM 配置
    2. 准备数据工具和知识库
    3. 获取历史对话作为上下文
    4. 路由执行：
       - 如果有数据工具 → ToolsCallAgent (LangGraph) + DataChatTool
       - 否则 → 直接 LLM 回答
    5. 统一格式化输出
    '''
    with app.app_context():
        message = req_dict['message']
        model_id = req_dict.get('model_id', '')
        conversation_id = req_dict.get('conversationId')
        if not conversation_id:
            conversation_id = gen_uuid()
        try:
            # 1. 验证 LLM 配置
            _llm = get_llm()
            if _llm is None:
                yield format_error_event(conversation_id, '未找到对应llm配置!')
                return

            # 2. 准备数据工具
            data_tool = get_chat_data_tool(model_id, is_chat=True)

            if data_tool is None:
                # 无数据工具：直接 LLM 回答
                for c in _llm.stream(message):
                    yield format_stream_event(conversation_id, c.content)

            else:
                # 有数据工具：使用 Agent 模式

                # 2.2 检索知识库
                knowledge = get_knowledge(message, metadata={'datamodel_id': model_id})
                if knowledge:
                    # 2.1 输出检索步骤
                    search_step = {
                        'content': {
                        'title': '检索知识库',
                        'content': knowledge,
                        'time': get_now_time(res_type='datetime')
                        },
                        'type': 'flow'
                    }
                    yield format_stream_event(conversation_id, search_step)
                    data_tool.knowledge = knowledge

                # 2.3 获取历史对话作为上下文
                history_messages, _ = get_messages(conversation_id, page=1, size=3)
                history_context = ""
                if history_messages:
                    history_context = "\n### 对话历史\n"
                    for msg in history_messages:
                        history_context += f"human: {msg['question']}\nAI: {msg.get('answer', '')}\n"

                # 设置历史上下文
                data_tool.set_history_context(history_context)

                # 2.4 创建 Agent 并执行
                agent = ToolsCallAgent(
                    tools=[data_tool],
                    llm=_llm,
                    system_prompt=f"{history_context}\n你是一个数据分析助手，能够帮助用户分析数据。"
                )

                # 2.5 流式输出结果
                final_answer = ""
                for chunk in agent.chat(message):
                    # 收集最终答案用于保存历史记录
                    if chunk.get('type') == 'text':
                        final_answer += chunk.get('content', '')
                    yield format_stream_event(conversation_id, chunk)
                # 保存对话历史记录
                if final_answer == '' and data_tool._agent and data_tool._agent.answer != '':
                    final_answer = data_tool._agent.answer
                if final_answer:
                    add_message(conversation_id, message, final_answer)

            # 3. 输出结束事件
            yield format_end_event(conversation_id)

        except Exception as e:
            # 错误处理
            error_msg = f"数据对话处理出错: {str(e)}\n{traceback.format_exc()}"
            yield format_error_event(conversation_id, error_msg)
            raise e


if __name__ == '__main__':
    req_dict = {
        "conversationId": "test1111111",
        "message": '几点了', #"字典表中字典项最多的10个字典， 返回表格统计结果",
        'chatConfig': {
            "msgNum": 1,
            "prologue": None,
            # "knowledgeIds": "1",
            "modelId": "default",
            "presetQuestion": "",
            # "datamodelIds": "c20ae41fcaa74597ab83293add482ff0",
            "toolIds": "now_time,network_search",
            "metadata": '{"multiSession": true}'
        }
    }

    with app.app_context():
        # chat_run(req_dict, {})
        for i in chat_generate(req_dict, {}):
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
    #             res = chat_run(req_dict)
    #             print(res)
    #             import time
    #             time.sleep(3)
    #             # for i in chat_generate(req_dict, None):
    #             #     print(i)
