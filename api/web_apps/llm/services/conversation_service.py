from web_apps import db
from utils.common_utils import gen_uuid, parse_json, get_now_time
from config import ES_CONF, SYS_CONF
from etl.libs.es import EsClient
from etl.utils.es_query_tool import EsQueryTool
from web_apps.llm.db_models import Conversation
from web_apps.rag.utils import vector_index


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
        user_id=meta_data.get('user_id', 0),
        app_id=meta_data.get('app_id', ''),
        user_name=meta_data.get('user_name', ''),
        core_memory='',
        mode=meta_data.get('mode', 'console'),
    )
    db.session.add(conv)
    db.session.commit()
    return conv


def add_message(conversation_id, question, answer) -> dict:
    """添加用户消息并生成回答"""
    # 获取会话
    conv = get_or_create_conversation(conversation_id)
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


def get_messages(conversation_id, page: int = 1, size: int = 20):
    """获取指定会话的消息历史"""
    try:
        es_client = EsClient(**ES_CONF)
        es_query_tool = EsQueryTool(
            {'index_name': SYS_CONF.get('LLM_MESSAGE_INDEX', 'llm_messages'), 'contain[conversation_id]': conversation_id, 'sort[created_at]': 'desc', 'page': page,
             'pagesize': size})
        res = es_query_tool.query(es=es_client)
        if res['code'] == 200:
            res['data']['records'] = res['data']['records'][::-1]
            return res['data']['records'], res['data']['total']
    except Exception as e:
        print(f"Failed to get messages: {e}")
    return [], 0


def get_core_memory(conversation_id) -> str:
    """获取核心记忆"""
    conv = db.session.query(Conversation).filter_by(id=conversation_id).first()
    return conv.core_memory if conv else ''


def add_core_memory(conversation_id, memory) -> str:
    """添加核心记忆"""
    conv = get_or_create_conversation(conversation_id)
    conv.core_memory = f"{conv.core_memory}\n{memory.strip()}"
    db.session.add(conv)
    db.session.commit()
    return conv.core_memory


def replace_core_memory(conversation_id, old_content, new_content) -> str:
    """更新核心记忆"""
    conv = get_or_create_conversation(conversation_id)
    current_value = conv.core_memory
    if old_content not in current_value:
        return f"Old content '{old_content}' not found in memory"
    new_value = current_value.replace(str(old_content), str(new_content))
    conv.core_memory = new_value
    db.session.add(conv)
    db.session.commit()
    return conv.core_memory


def add_archival_memory(conversation_id, content):
    '''
    添加归档记忆
    '''
    vector_index.add_texts([content], metadatas=[{'conversation_id': conversation_id}], ids=[gen_uuid()])
    return '归档记忆添加成功'


def search_archival_memory(conversation_id, query):
    '''
    查询归档记忆
    '''
    search_kwargs = {
        'filter': {'conversation_id': conversation_id},
        'score_threshold': 0,
        'k': 1,
        'retrieval_type': 'vector'
    }
    kwargs = {
        'search_kwargs': search_kwargs,
        'search_type': 'similarity_score_threshold'
    }
    docs = vector_index.search(query, **kwargs)
    return '\n'.join([d.page_content for d in docs])
