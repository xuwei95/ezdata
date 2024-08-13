from langchain_community.embeddings import DashScopeEmbeddings
from web_apps.rag.vector_index.es_vector_index import EsVectorIndex
from web_apps.rag.text_index.es_text_index import EsTextIndex
from web_apps.rag.embedding.cached_embedding import CacheEmbeddings
from web_apps.rag.rerank.rerank import RerankRunner
from web_apps.rag.rerank.dashscope_rerank import DashScopeRerankModel
from config import SYS_CONF

# embeddings
EMBEDDING_TYPE = SYS_CONF.get('EMBEDDING_TYPE', 'dashscope')
# 知识存储
VECTOR_STORE_TYPE = SYS_CONF.get('VECTOR_STORE_TYPE', 'elasticsearch')
TEXT_STORE_TYPE = SYS_CONF.get('TEXT_STORE_TYPE', 'elasticsearch')
# rerank
RERANK_TYPE = SYS_CONF.get('RERANK_TYPE', 'dashscope')


def get_embeddings():
    embeddings = None
    if EMBEDDING_TYPE == 'dashscope':
        embeddings = DashScopeEmbeddings(dashscope_api_key=SYS_CONF.get('DASHSCOPE_API_KEY'),
                                         model=SYS_CONF.get('EMBEDDING_MODEL', 'text-embedding-v1'))
    if str(SYS_CONF.get('EMBEDDING_CACHE')) == '1' and embeddings is not None:
        embeddings = CacheEmbeddings(embeddings)
    return embeddings


def get_vector_index():
    embeddings = get_embeddings()
    if VECTOR_STORE_TYPE == 'elasticsearch':
        return EsVectorIndex(embeddings)
    return None


def get_text_index():
    if TEXT_STORE_TYPE == 'elasticsearch':
        return EsTextIndex()
    return None


def get_rerank_runner():
    rerank_model = None
    if RERANK_TYPE == 'dashscope':
        rerank_model = DashScopeRerankModel(SYS_CONF.get('DASHSCOPE_API_KEY'))
    if rerank_model:
        rerank_runner = RerankRunner(rerank_model)
        return rerank_runner
    return None


vector_index = get_vector_index()
text_index = get_text_index()
rerank_runner = get_rerank_runner()
