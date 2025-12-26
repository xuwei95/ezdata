"""
LLM工具服务
"""
import traceback
import json
from typing import List, Union
from utils.logger.logger import get_logger
from web_apps import db
from web_apps.llm.db_models import LLMTool
from web_apps.llm.tools import get_builtin_tools, tools_map
logger = get_logger(p_name='system_log', f_name='llm_tool', log_level='INFO')

def get_tools(names: Union[str, List[str]], include_mcp: bool = True):
    """
    获取工具列表，整合内置工具和 MCP 工具
    适用于 Flask 同步环境

    Args:
        names: 工具名称列表或逗号分隔的字符串
        include_mcp: 是否包含 MCP 工具（不在内置工具列表中时）

    Returns:
        工具列表（包含内置工具和 MCP 工具）
    """
    if isinstance(names, str):
        names = names.split(',')

    # 分离内置工具名称和可能的 MCP 工具名称
    builtin_tool_names = []
    mcp_tool_ids = []

    for name in names:
        name = name.strip()
        if name in tools_map:
            builtin_tool_names.append(name)
        else:
            mcp_tool_ids.append(name)

    # 获取内置工具
    builtin_tools = get_builtin_tools(builtin_tool_names)
    mcp_tool_config = {}
    # 如果启用 MCP 工具，直接从数据库查询
    if include_mcp and mcp_tool_ids:
        try:
            # 从数据库查询 MCP 工具
            mcp_tools_from_db = db.session.query(LLMTool).filter(
                LLMTool.type == 'mcp',
                LLMTool.id.in_(mcp_tool_ids),
                LLMTool.status == 1
            ).all()

            if not mcp_tools_from_db:
                logger.warning(f"未找到 MCP 工具: {mcp_tool_ids}")
                return builtin_tools
            # 构建 MCP 工具配置
            for tool_db in mcp_tools_from_db:
                tool_config = json.loads(tool_db.args) if isinstance(tool_db.args, str) else tool_db.args
                server_name = tool_db.code
                # 根据服务器类型配置参数
                server_type = tool_config.get('server_type', 'stdio')
                params = {}
                if server_type == 'stdio':
                    params = {
                        "command": tool_config.get('command', ''),
                        "args": tool_config.get('args', []),
                        "transport": "stdio"
                    }
                elif server_type in ['sse', 'streamable_http']:
                    params = {
                        "url": tool_config.get('url', ''),
                        "transport": "streamable_http",
                        "headers": tool_config.get('headers', {})
                    }
                mcp_tool_config[server_name] = params
        except Exception as e:
            logger.error(f"获取 MCP 工具失败: {str(e)}")
            logger.error(traceback.format_exc())

    return builtin_tools, mcp_tool_config
