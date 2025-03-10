from web_apps import db
from utils.common_utils import gen_json_response, gen_uuid, parse_json, get_now_time
from config import ES_CONF, SYS_CONF
from ezetl.libs.es import EsClient
from ezetl.utils.es_query_tool import EsQueryTool
from web_apps.llm.db_models import Conversation


def get_or_create_conversation(conversation_id, meta_data={}) -> Conversation:
    """获取会话"""
    if conversation_id in ['', None]:
        conversation_id = gen_uuid()
    else:
        conv = db.session.query(Conversation).filter_by(id=conversation_id).first()
        if conv:
            return conv
    conv = Conversation(
        id=conversation_id,
        user_id=meta_data['user_id'],
        app_id=meta_data.get('app_id', ''),
        user_name=meta_data.get('user_name', ''),
        core_memory='',
        mode=meta_data.get('mode', 'console'),
    )
    db.session.add(conv)
    db.session.commit()
    return conv


def add_message(self, conversation_id, question, answer) -> dict:
    """添加用户消息并生成回答"""
    # 获取会话
    conv = self.get_or_create_conversation()
    if not conv:
        raise ValueError("Conversation not found")

    # 存储到ES
    message_doc = {
        "conversation_id": conversation_id,
        "question": question,
        "answer": answer,
        "created_at": get_now_time()
    }
    es_client = EsClient(**ES_CONF)
    es_client.add_data_bulk(SYS_CONF.get('LLM_MESSAGE_INDEX', 'llm_messages'), [message_doc])

    return message_doc


def get_messages(conversation_id, size: int = 20) -> list:
    """获取指定会话的消息历史"""
    es_client = EsClient(**ES_CONF)
    es_query_tool = EsQueryTool(
        {'index_name': SYS_CONF.get('LLM_MESSAGE_INDEX', 'llm_messages'), 'contain[conversation_id]': conversation_id, 'sort[@created_at]': 'desc', 'page': 1,
         'pagesize': size})
    res = es_query_tool.query(es=es_client)
    if res['code'] == 200:
        res['data']['records'] = res['data']['records'][::-1]
    return res


def add_core_memory(conversation_id, memory) -> str:
    """添加核心记忆"""
    conv = get_or_create_conversation(conversation_id)
    conv.core_memory = f"{conv.core_memory}\n {get_now_time()}: {memory.strip()}"
    db.session.add(conv)
    db.session.commit()
    return conv.core_memory


def replace_core_memory(conversation_id, memory) -> str:
    """更新核心记忆"""
    conv = get_or_create_conversation(conversation_id)
    conv.core_memory = f"{memory.strip()}"
    db.session.add(conv)
    db.session.commit()
    return conv.core_memory
