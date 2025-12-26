"""
内置工具管理模块
"""
from web_apps.llm.tools.common_tools import get_time, get_url_content, summary_content, network_search

# 内置工具映射表
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
    },
    'network_search': {
        'name': '网络搜索',
        'tool': network_search
    }
}


def get_tool(key):
    """
    获取单个内置工具

    Args:
        key: 工具名称（键）

    Returns:
        工具函数或 None（如果不存在）
    """
    if key in tools_map:
        tool_info = tools_map[key]
        return tool_info['tool']
    return None


def get_builtin_tools(names):
    """
    获取内置工具列表

    Args:
        names: 工具名称列表或逗号分隔的字符串

    Returns:
        内置工具列表
    """
    if isinstance(names, str):
        names = names.split(',')

    tools = []
    for name in names:
        name = name.strip()
        tool = get_tool(name)
        if tool:
            tools.append(tool)

    return tools


def get_all_builtin_tools():
    """
    获取所有内置工具

    Returns:
        所有内置工具列表
    """
    return [tool_info['tool'] for tool_info in tools_map.values()]


def list_builtin_tools():
    """
    列出所有内置工具信息

    Returns:
        内置工具信息列表
    """
    return [
        {
            'key': key,
            'name': info['name'],
            'tool': info['tool']
        }
        for key, info in tools_map.items()
    ]


if __name__ == '__main__':
    # 测试内置工具
    print("=" * 60)
    print("内置工具列表")
    print("=" * 60)

    # 列出所有内置工具
    builtin_tools = list_builtin_tools()
    for tool in builtin_tools:
        print(f"  - {tool['key']}: {tool['name']}")

    # 获取单个工具
    print("\n获取单个工具示例:")
    time_tool = get_tool('now_time')
    if time_tool:
        print(f"  now_time 工具: {time_tool}")

    # 获取多个工具
    print("\n获取多个工具示例:")
    tools = get_builtin_tools(['now_time', 'get_url_content'])
    print(f"  获取到 {len(tools)} 个工具")
    for tool in tools:
        print(f"    - {tool}")
