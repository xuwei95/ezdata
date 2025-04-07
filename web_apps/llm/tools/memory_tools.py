from langchain.tools import BaseTool
from typing import Optional, Type
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.pydantic_v1 import BaseModel, Field
from web_apps import app
from web_apps.llm.services.conversation_service import add_core_memory, replace_core_memory, get_core_memory, search_archival_memory


class MemoryInput(BaseModel):
    memory: str = Field(
        description="记忆内容"
    )


class MemoryReplaceInput(BaseModel):
    old_content: str = Field(
        description="旧记忆内容"
    )
    new_content: str = Field(
        description="新的记忆内容"
    )


class CoreMemoryAppendTool(BaseTool):
    """
    添加核心记忆
    """

    name: str = "core_memory_append"
    description: str = (
        "追加加核心记忆，若用户提到新的关键信息，请使用此工具添加记忆"
    )
    return_direct = False
    conversation_id: str = ''
    args_schema: Type[BaseModel] = MemoryInput

    def _run(
        self,
        memory: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> object:
        add_core_memory(self.conversation_id, memory)
        return '核心记忆添加成功'


class CoreMemoryReplaceTool(BaseTool):
    """
    替换核心记忆
    """

    name: str = "core_memory_replace"
    description: str = (
        "若用户提到的信息与当前核心记忆有冲突，请使用此工具替换现有核心记忆的一部分为新的核心记忆，只替换需变更部分的记忆"
    )
    return_direct = False
    conversation_id: str = ''
    args_schema: Type[BaseModel] = MemoryReplaceInput

    def _run(
        self,
        old_content: str,
        new_content: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> object:
        replace_core_memory(self.conversation_id, old_content, new_content)
        return '核心记忆替换成功'


class MemorySearchInput(BaseModel):
    query: str = Field(
        description="查询关键词"
    )


class ArchivalMemorySearchTool(BaseTool):
    """
    查询归档记忆
    """

    name: str = "archival_memory_search"
    description: str = (
        "若用户提出未知的问题，可使用该工具查询相关历史归档记忆"
    )
    return_direct = False
    conversation_id: str = ''
    args_schema: Type[BaseModel] = MemorySearchInput

    def _run(
            self,
            query: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> object:
        memory = search_archival_memory(self.conversation_id, query)
        return memory


def get_memory_tools(conversation_id):
    core_memory_append_tool = CoreMemoryAppendTool(conversation_id=conversation_id)
    core_memory_replace_tool = CoreMemoryReplaceTool(conversation_id=conversation_id)
    archival_memory_search_tool = ArchivalMemorySearchTool(conversation_id=conversation_id)
    tools = [core_memory_append_tool, core_memory_replace_tool, archival_memory_search_tool]
    return tools


if __name__ == '__main__':
    from web_apps.llm.agents.tools_call_agent import ToolsCallAgent
    conversation_id = '8a862fdf980245459ac9ef89734c1668'
    tools = get_memory_tools(conversation_id)
    agent = ToolsCallAgent(tools=tools)
    with app.app_context():
        prompt = '我的爱好是弹钢琴'
        prompt += f"\n当前核心记忆：{get_core_memory(conversation_id)}"
        print(prompt)
        res = agent.chat(prompt)
        for chunk in res:
            print(chunk)
        prompt = '我在阿里巴巴上班'
        prompt += f"\n当前核心记忆：{get_core_memory(conversation_id)}"
        print(prompt)
        res = agent.chat(prompt)
        for chunk in res:
            print(chunk)
        prompt = '我最近跳槽去了美团'
        prompt += f"\n当前核心记忆：{get_core_memory(conversation_id)}"
        print(prompt)
        res = agent.chat(prompt)
        for chunk in res:
            print(chunk)
        prompt = '我不喜欢弹钢琴了'
        prompt += f"\n当前核心记忆：{get_core_memory(conversation_id)}"
        print(prompt)
        res = agent.chat(prompt)
        for chunk in res:
            print(chunk)