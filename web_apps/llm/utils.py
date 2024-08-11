import re
import ast
from langchain.llms.openai import OpenAIChat
from web_apps.llm.llms.ali_bailian_llm import AliBailianLLM
from web_apps.llm.llms.dify_llm import DifyLLM
from web_apps.llm.llms.gradio_llm import GradioLLM
from config import SYS_CONF

# llm相关配置
LLM_TYPE = SYS_CONF.get('LLM_TYPE', 'openai')
LLM_URL = SYS_CONF.get('LLM_URL', 'https://api.openai.com/v1')
LLM_API_KEY = SYS_CONF.get('LLM_API_KEY', '')
LLM_MODEL = SYS_CONF.get('LLM_MODEL', '')


def get_llm(conversation_id=''):
    if LLM_TYPE == 'openai':
        return OpenAIChat(
            model_name=LLM_MODEL,
            api_key=LLM_API_KEY,
            api_base=LLM_URL
        )
    if LLM_TYPE == 'ali_bailian':
        return AliBailianLLM(
            model_name=LLM_MODEL,
            api_key=LLM_API_KEY
        )
    if LLM_TYPE == 'dify':
        return DifyLLM(
            conversation_id=conversation_id,
            url=LLM_URL,
            api_key=LLM_API_KEY
        )
    if LLM_TYPE == 'gradio':
        return GradioLLM(
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
