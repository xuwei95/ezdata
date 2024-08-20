from web_apps.llm.tools.common_tools import get_time, get_url_content, summary_content
tools_map = {
    'now_time': {
        'name': '获取当前时间',
        'tool': get_time
    },
    'get_url_content': {
        'name': '请求网络内容',
        'tool': get_url_content
    },
    'summary_content': {
        'name': '内容总结摘要',
        'tool': summary_content
    }
}


def get_tool(key):
    if key in tools_map:
        tool_info = tools_map[key]
        tool = tool_info['tool']
        return tool
    else:
        return None


def get_tools(names):
    if isinstance(names, str):
        names = names.split(',')
    tools = []
    for name in names:
        if name in tools_map:
            tools.append(get_tool(name))
    return tools


if __name__ == '__main__':
    from web_apps.llm.agents.tools_call_agent import ToolsCallAgent
    tools = get_tools(['now_time', 'get_url_content'])
    agent = ToolsCallAgent(tools=tools)
    # res = agent.chat('现在几点了？')
    res = agent.chat('获取https://akshare.akfamily.xyz/data/fund/fund_private.html 内容并总结为200字左右文案')
    for i in res:
        print(i)
