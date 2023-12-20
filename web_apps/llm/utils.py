from langchain.chat_models import ChatOpenAI
from config import SYS_CONF

# llm相关配置
LLM_TYPE = SYS_CONF.get('LLM_TYPE', 'openai')
LLM_URL = SYS_CONF.get('LLM_URL', 'https://api.openai.com/v1')
LLM_API_KEY = SYS_CONF.get('LLM_API_KEY', '')
LLM_MODEL = SYS_CONF.get('LLM_MODEL', '')


def get_llm():
    if LLM_TYPE == 'openai':
        return ChatOpenAI(
            model_name=LLM_MODEL,
            openai_api_key=LLM_API_KEY,
            openai_api_base=LLM_URL
        )
    return None
