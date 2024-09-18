from langchain.tools import BaseTool
from typing import Optional, Type
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.pydantic_v1 import BaseModel, Field
from web_apps import app, db
from web_apps.datamodel.db_models import DataModel
from utils.etl_utils import get_reader_model
from web_apps.llm.llm_utils import get_llm
from web_apps.llm.agents.data_chat_agent import DataChatAgent
from web_apps.rag.services.rag_service import get_star_qa_answer


class DataChatInput(BaseModel):
    question: str = Field(
        description="用户问题"
    )
    knowledge: str = Field(
        description="问题相关知识库信息，若没有则为空字符串"
    )


class DataChatTool(BaseTool):
    """
    数据分析工具
    """

    name: str = "datachat"
    description: str = (
        "数据分析"
    )
    return_direct = True
    datamodel_id: str = ''
    reader: Optional[object] = None
    args_schema: Type[BaseModel] = DataChatInput

    def bind_model(self):
        with app.app_context():
            datamodel_obj = db.session.query(DataModel).filter(DataModel.id == self.datamodel_id).first()
            if datamodel_obj:
                flag, self.reader = get_reader_model({'model_id': self.datamodel_id})
                if not flag:
                    self.reader = None
                # 修改名称
                self.name = f"datachat_{self.datamodel_id}"
                # 修改描述
                self.description = f"""数据分析工具，用于查询数据模型 {datamodel_obj.name} 做数据分析和统计绘图等功能
                数据模型类型：{datamodel_obj.type}
                描述： {datamodel_obj.description}
                """

    def _run(
        self,
        question: str,
        knowledge: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict:
        with app.app_context():
            _llm = get_llm()
            # 查询知识库中是否有已标记的正确答案
            answer = get_star_qa_answer(question, metadata={'datamodel_id': self.datamodel_id})
            _agent = DataChatAgent(_llm, self.reader, knowledge=knowledge, answer=answer, retry=1)
            result = _agent.run(question)
            return result


def get_chat_data_tool(datamodel_id: str):
    _tool = DataChatTool(datamodel_id=datamodel_id)
    _tool.bind_model()
    if _tool.reader:
        return _tool
    return None


def get_chat_data_tools(datamodel_ids):
    tools = []
    for _id in datamodel_ids:
        if _id != '':
            tool = get_chat_data_tool(_id)
            if tool is not None:
                tools.append(tool)
    return tools


if __name__ == '__main__':
    from web_apps.llm.agents.tools_call_agent import ToolsCallAgent
    datamodel_ids = ['8a862fdf980245459ac9ef89734c166f', '22016439fbd0431887641544a0cf5cf4']
    tools = get_chat_data_tools(datamodel_ids)
    agent = ToolsCallAgent(tools=tools)
    res = agent.chat('查出sys_dict 表前10条数据')
    for chunk in res:
        print(chunk)
