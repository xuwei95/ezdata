import re
import ast
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessageChunk
from langchain_community.chat_models.tongyi import ChatTongyi
from web_apps.llm.llms.dify_llm import DifyChatModel
from web_apps.llm.llms.gradio_llm import GradioChatModel
from config import SYS_CONF


class ReasoningChatOpenAI(ChatOpenAI):
    """ChatOpenAI subclass that captures reasoning_content (DeepSeek R1, QwQ, etc.)
    into additional_kwargs so downstream code can display thinking steps."""

    def _convert_chunk_to_generation_chunk(self, chunk, default_chunk_class, base_generation_info):
        gen_chunk = super()._convert_chunk_to_generation_chunk(chunk, default_chunk_class, base_generation_info)
        if gen_chunk is None:
            return gen_chunk
        choices = chunk.get('choices', [])
        if choices:
            delta = choices[0].get('delta', {})
            reasoning = delta.get('reasoning_content')
            if reasoning and isinstance(gen_chunk.message, AIMessageChunk):
                gen_chunk.message.additional_kwargs['reasoning_content'] = reasoning
        return gen_chunk

# llm相关配置
LLM_TYPE = SYS_CONF.get('LLM_TYPE', 'openai')
LLM_URL = SYS_CONF.get('LLM_URL', 'https://api.openai.com/v1')
LLM_API_KEY = SYS_CONF.get('LLM_API_KEY', '')
LLM_MODEL = SYS_CONF.get('LLM_MODEL', '')


def get_llm(llm_config=None):
    """
    创建 LLM 实例，所有参数从 llm_config 读取，未配置时 fallback 到环境变量。
    支持字段：
      provider_type, model, api_key, base_url  —— 连接信息
      temperature, top_p/topP, max_tokens/maxTokens  —— 生成参数
      conversation_id  —— dify 专用
    """
    if llm_config is None:
        llm_config = {}
    _type = llm_config.get('provider_type') or LLM_TYPE
    _model = llm_config.get('model') or LLM_MODEL
    _key = llm_config.get('api_key') or LLM_API_KEY
    _url = llm_config.get('base_url') or LLM_URL
    _temperature = llm_config.get('temperature', 0.5)
    _top_p = llm_config.get('top_p', llm_config.get('topP', 0.8))
    _max_tokens = llm_config.get('max_tokens', llm_config.get('maxTokens', 4000))
    if _type == 'openai':
        return ReasoningChatOpenAI(
            model=_model,
            api_key=_key,
            base_url=_url or 'https://api.openai.com/v1',
            temperature=_temperature,
            top_p=_top_p,
            max_tokens=_max_tokens,
        )
    if _type == 'tongyi':
        return ChatTongyi(model=_model, api_key=_key, top_p=_top_p)
    if _type == 'dify':
        return DifyChatModel(url=_url, api_key=_key, conversation_id=llm_config.get('conversation_id', ''))
    if _type == 'gradio':
        return GradioChatModel(url=_url)
    if _type == 'anthropic':
        from langchain_anthropic import ChatAnthropic
        kwargs = dict(model=_model, api_key=_key, temperature=_temperature, max_tokens=_max_tokens)
        if _url:
            kwargs['base_url'] = _url
        return ChatAnthropic(**kwargs)
    return None


def resolve_model_config(model_id):
    """
    根据模型ID查询数据库，返回可直接传入 get_llm 的 config dict。
    未找到返回空 dict（调用方 fallback 到环境变量默认配置）。
    """
    import json
    from web_apps import db
    from web_apps.llm.db_models import LLMModel
    from web_apps.llm.provider_config import get_provider_config

    model = db.session.query(LLMModel).filter(LLMModel.id == model_id).first()
    if not model:
        return {}

    provider = get_provider_config(model.provider)
    provider_type = provider['provider_type'] if provider else model.provider
    api_key = model.api_key or (provider.get('api_key', '') if provider else '')
    base_url = model.base_url or (provider.get('base_url', '') if provider else '')

    config = {}
    if model.config:
        try:
            config = json.loads(model.config) if isinstance(model.config, str) else model.config
        except Exception:
            pass

    config.update({
        'provider_type': provider_type,
        'model': model.model_code,
        'api_key': api_key,
        'base_url': base_url,
    })
    return config


def polish_code(code: str) -> str:
    """
    Polish the code by removing the leading "python" or "py",  \
    removing the imports and removing trailing spaces and new lines.
    Args:
        code (str): A string of Python code.
    Returns:
        str: Polished code.
    """
    if re.match(r"^(python|py)", code):
        code = re.sub(r"^(python|py)", "", code)
    if re.match(r"^`.*`$", code):
        code = re.sub(r"^`(.*)`$", r"\1", code)
    code = code.strip()
    return code


def is_python_code(string):
    """
    Return True if it is valid python code.
    Args:
        string (str):
    Returns (bool): True if Python Code otherwise False
    """
    try:
        ast.parse(string)
        return True
    except SyntaxError:
        return False


def extract_code(response: str, separator: str = "```") -> str:
    """
    Extract the code from the response.
    Args:
        response (str): Response
        separator (str, optional): Separator. Defaults to "```".
    Raises:
        NoCodeFoundError: No code found in the response
    Returns:
        str: Extracted code from the response
    """
    code = response

    if separator not in response:
        raise ValueError("No code found in the response")

    if len(code.split(separator)) > 1:
        code = code.split(separator)[1]
    code = polish_code(code)
    return code



if __name__ == '__main__':
    llm = get_llm()
    res = llm.invoke("hello")
    print(res)
