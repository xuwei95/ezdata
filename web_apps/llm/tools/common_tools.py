from langchain_core.tools import tool
from utils.common_utils import get_now_time, format_date, request_url
import html2text
from web_apps.llm.utils import get_llm


@tool
def get_time(format: str = '%Y-%m-%d %H:%M:%S') -> str:
    '''
    获取当前时间
    '''
    now = get_now_time()
    return format_date(now, format=format)


@tool
def get_url_content(url: str) -> str:
    '''
    请求网络url获取内容
    '''
    res = request_url(url)
    html = res.text
    text_maker = html2text.HTML2Text()
    text_maker.bypass_tables = False
    text_maker.ignore_links = False
    text_maker.ignore_images = False
    text = text_maker.handle(html)
    return text


@tool
def summary_content(content: str, max_length: int = 2000, length: int = 500) -> str:
    '''
    使用大模型输出所给内容的总结摘要
    content: 内容
    max_length: 给大模型的最长内容，超过将会被截断
    length：输出总结内容字数
    '''
    llm = get_llm()
    prompt = f"总结一下内容，生成一篇{length}字左右内容摘要:\n{content[:max_length]}"
    result = llm.invoke(prompt).content
    return result


if __name__ == '__main__':
    print(get_time())
