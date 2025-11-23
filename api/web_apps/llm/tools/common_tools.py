from langchain_core.tools import tool
from utils.common_utils import get_now_time, format_date
from web_apps.rag.extractor.http_url_extractor import HttpUrlExtractor
from web_apps.llm.llm_utils import get_llm


@tool
def get_time(format: str = '%Y-%m-%d %H:%M:%S') -> str:
    '''
    获取当前时间
    '''
    now = get_now_time()
    return format_date(now, format=format)


@tool
def summary_content(content: str, max_length: int = 4000, length: int = 500) -> str:
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


@tool(return_direct=True)
def get_url_content(url: str) -> str:
    '''
    请求网络url获取内容
    '''
    extractor = HttpUrlExtractor(
        url=url,
        ignore_links=True,
        ignore_images=True
    )
    documents = extractor.extract()
    text = '\n'.join([d.page_content for d in documents])
    return summary_content(text)


@tool(return_direct=True)
def network_search(keyword: str) -> str:
    '''
    搜索互联网获取相关信息
    keyword: 搜索关键词
    '''
    url = f'https://www.baidu.com/s?wd={keyword}'
    extractor = HttpUrlExtractor(
        url=url,
        ignore_links=True,
        ignore_images=True
    )
    documents = extractor.extract()
    text = '\n'.join([d.page_content for d in documents])
    if '百度为您找到以下结果' in text:
        text = text.split('百度为您找到以下结果')[1]
    if '相关搜索' in text:
        text = text.split('相关搜索')[0]
    llm = get_llm()
    prompt = f"根据用户问题：{keyword} \n 总结一下内容，生成一篇500字左右内容摘要:\n{text[:4000]}"
    result = llm.invoke(prompt).content
    return result


if __name__ == '__main__':
    print(get_time())
