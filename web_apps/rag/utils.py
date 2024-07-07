from langchain.embeddings import DashScopeEmbeddings
from web_apps.rag.vector_index.es_vector_index import EsVectorIndex
from config import SYS_CONF

# rag相关配置
# embeddings
EMBEDDING_TYPE = SYS_CONF.get('EMBEDDING_TYPE', 'dashscope')
EMBEDDING_API_KEY = SYS_CONF.get('EMBEDDING_API_KEY', '')
# 向量存储
VECTOR_STORE_TYPE = SYS_CONF.get('VECTOR_STORE_TYPE', 'elasticsearch')


def get_embeddings():
    if EMBEDDING_TYPE == 'dashscope':
        embeddings = DashScopeEmbeddings(dashscope_api_key=EMBEDDING_API_KEY)
        return embeddings
    return None


def get_vector_index():
    embeddings = get_embeddings()
    if VECTOR_STORE_TYPE == 'elasticsearch':
        return EsVectorIndex(embeddings)
    return None