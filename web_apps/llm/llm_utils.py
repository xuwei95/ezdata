import re
import ast
from langchain_openai import ChatOpenAI
from langchain_community.chat_models.tongyi import ChatTongyi
from web_apps.llm.llms.dify_llm import DifyChatModel
from web_apps.llm.llms.gradio_llm import GradioChatModel
from config import SYS_CONF

# llm相关配置
LLM_TYPE = SYS_CONF.get('LLM_TYPE', 'openai')
LLM_URL = SYS_CONF.get('LLM_URL', 'https://api.openai.com/v1')
LLM_API_KEY = SYS_CONF.get('LLM_API_KEY', '')
LLM_MODEL = SYS_CONF.get('LLM_MODEL', '')


def get_llm(llm_config=None):
    if llm_config is None:
        llm_config = {
            'temperature': 0.5,
            'top_p': 0.8,
            'max_tokens': 4000
        }
    if LLM_TYPE == 'openai':
        return ChatOpenAI(
            model_name=LLM_MODEL,
            openai_api_key=LLM_API_KEY,
            openai_api_base=LLM_URL,
            temperature=llm_config.get('temperature', 0.5),
            top_p=llm_config.get('top_p', 0.8),
            max_tokens=llm_config.get('max_tokens', 4000)
        )
    if LLM_TYPE == 'tongyi':
        return ChatTongyi(
            model_name=LLM_MODEL,
            api_key=LLM_API_KEY,
            top_p=llm_config.get('top_p', 0.8)
        )
    if LLM_TYPE == 'dify':
        return DifyChatModel(
            url=LLM_URL,
            api_key=LLM_API_KEY,
            conversation_id=llm_config.get('conversation_id', '')
        )
    if LLM_TYPE == 'gradio':
        return GradioChatModel(
            url=LLM_URL
        )
    return None


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
    res = llm("hello")
    print(res)
