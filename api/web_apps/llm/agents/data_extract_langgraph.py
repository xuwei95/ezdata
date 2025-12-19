# encoding: utf-8
"""
DataExtractLangGraph - 数据提取 Agent (LangGraph 版本)
使用 LangGraph StateGraph 实现数据提取工作流
强制返回 DataFrame 格式
"""
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from web_apps.llm.llm_utils import extract_code, get_llm
from utils.common_utils import get_now_time
import traceback
import pandas as pd


class DataExtractState(TypedDict):
    """数据提取 Agent 状态定义"""
    messages: List[BaseMessage]          # 对话消息
    question: str                        # 用户问题
    info_prompt: str                     # 数据模型信息提示
    generated_code: str                  # 生成的代码
    llm_result: str                      # LLM生成结果
    executed_code: str                   # 最后执行的代码
    code_exception: str                  # 代码执行异常
    execution_result: Any                # 代码执行结果
    retry_count: int                     # 重试次数
    max_retry: int                       # 最大重试次数
    max_token: int                       # 最大token数


class DataExtractLangGraph:
    """
    数据提取 Agent - LangGraph 实现

    特性：
    - 强制返回 DataFrame 格式
    - 自动代码生成和执行
    - 错误自动修复（重试机制）
    - 清晰的工作流编排
    """

    def __init__(self, llm=None, reader=None, retry=1, max_token=4000):
        """
        初始化数据提取 Agent

        Args:
            llm: 语言模型实例
            reader: 数据读取器对象
            retry: 最大重试次数
            max_token: 最大token数
        """
        if llm is None:
            self.llm = get_llm()
        else:
            self.llm = llm
        self.reader = reader
        self.max_retry = retry
        self.max_token = max_token
        self.llm_result = ''  # 保持与旧版本兼容

    def create_info_prompt_generator(self):
        """创建信息提示生成器节点"""

        def generate_info_prompt(state: DataExtractState) -> DataExtractState:
            """生成数据模型信息提示"""
            if state["info_prompt"] == '':
                info_prompt = self.reader.get_info_prompt('')
                if len(info_prompt) > state["max_token"]:
                    # 信息过长，抽出模型列表，使用llm筛选出部分模型生成信息提示
                    model_list = self.reader.gen_models()
                    model_list = [{'type': i['type'], 'name': i['model_conf']['name']} for i in model_list]
                    prompt = f"你正在进行数据分析任务，有以下数据模型：\n{model_list}\n 请根据问题：\n {state['question']}\n 从以上数据模型中筛选出你需要的模型名称列表,只需要返回名称列表，用逗号隔开，不要其他内容"
                    model_prompt = self.llm.invoke(prompt).content
                    info_prompt = self.reader.get_info_prompt(model_prompt)

                return {
                    **state,
                    "info_prompt": info_prompt
                }
            return state

        return generate_info_prompt

    def create_code_generator(self):
        """创建代码生成器节点"""

        def generate_code(state: DataExtractState) -> DataExtractState:
            """生成Python代码"""
            result_example_prompt = '{ "type": "dataframe", "value": pd.DataFrame({...}) }'

            prompt = f"""
I have a data reader object called reader, and the object information is：
{state['info_prompt']}

Update this initial code:
```python
# TODO: import the required dependencies

# Write code here

# Declare result var:
type (must be "dataframe"), value must be a pd.DataFrame. Example: result = {result_example_prompt}

```

### QUERY

{state['question']}

Variable `reader` is already declared.

At the end, declare "result" variable as a dictionary of type and value.


Generate python code and return full updated code:
请在代码中使用中文添加必要注释
"""

            llm_result = self.llm.invoke(prompt).content
            self.llm_result = llm_result  # 保持与旧版本兼容
            code = extract_code(llm_result)

            return {
                **state,
                "generated_code": code,
                "llm_result": llm_result
            }

        return generate_code

    def create_code_executor(self):
        """创建代码执行器节点"""

        def execute_code(state: DataExtractState) -> DataExtractState:
            """执行Python代码"""
            code = state["generated_code"]

            try:
                environment = {'reader': self.reader}
                exec(code, environment)

                if "result" not in environment:
                    raise ValueError("No result returned")
                else:
                    result = environment['result']
                    if not isinstance(result['value'], pd.DataFrame):
                        raise ValueError(
                            f'Value type {type(result["value"])} must match with type {result["type"]}'
                        )

                    return {
                        **state,
                        "executed_code": code,
                        "execution_result": result
                    }

            except Exception as e:
                traceback_errors = traceback.format_exc()

                return {
                    **state,
                    "executed_code": code,
                    "code_exception": traceback_errors,
                    "retry_count": state["retry_count"] + 1
                }

        return execute_code

    def create_code_fixer(self):
        """创建代码修复器节点"""

        def fix_code(state: DataExtractState) -> DataExtractState:
            """修复错误代码"""
            fix_code_prompt = f"""
I have a data reader object called reader, and the object information is：
{state['info_prompt']}
The user asked the following question:
{state['question']}
You generated this python code:
{state['executed_code']}
the code running throws an exception:
{state['code_exception']}
Fix the python code above and return the new python code
请在代码中使用中文添加必要注释
        """

            llm_result = self.llm.invoke(fix_code_prompt).content
            self.llm_result = llm_result  # 保持与旧版本兼容
            new_code = extract_code(llm_result)

            return {
                **state,
                "generated_code": new_code,
                "llm_result": llm_result
            }

        return fix_code

    def create_retry_router(self):
        """创建重试路由节点"""

        def route_retry(state: DataExtractState) -> str:
            """根据执行结果决定下一步"""
            if "execution_result" in state and state["execution_result"] is not None:
                # 执行成功，结束
                return "success"
            elif state["retry_count"] < state["max_retry"]:
                # 需要重试，修复代码
                return "retry"
            else:
                # 重试次数用完，失败
                return "fail"

        return route_retry

    def create_langgraph_workflow(self):
        """创建LangGraph工作流"""
        # 创建工作流图
        workflow = StateGraph(DataExtractState)

        # 添加节点
        workflow.add_node("generate_info_prompt", self.create_info_prompt_generator())
        workflow.add_node("generate_code", self.create_code_generator())
        workflow.add_node("execute_code", self.create_code_executor())
        workflow.add_node("fix_code", self.create_code_fixer())

        # 设置入口点
        workflow.set_entry_point("generate_info_prompt")

        # 添加边
        workflow.add_edge("generate_info_prompt", "generate_code")
        workflow.add_edge("generate_code", "execute_code")

        # 添加条件边
        workflow.add_conditional_edges(
            "execute_code",
            self.create_retry_router(),
            {
                "success": END,
                "retry": "fix_code",
                "fail": END
            }
        )

        # 添加重试边
        workflow.add_edge("fix_code", "execute_code")

        return workflow.compile()

    def run(self, prompt):
        """
        同步运行数据提取 Agent

        Args:
            prompt: 用户问题

        Returns:
            字典格式结果 {"type": "dataframe", "value": pd.DataFrame}
            如果失败返回 None
        """
        # 创建工作流
        app = self.create_langgraph_workflow()

        # 初始化状态
        initial_state = {
            "messages": [HumanMessage(content=prompt)],
            "question": prompt,
            "info_prompt": "",
            "generated_code": "",
            "llm_result": "",
            "executed_code": "",
            "code_exception": "",
            "execution_result": None,
            "retry_count": 0,
            "max_retry": self.max_retry,
            "max_token": self.max_token
        }

        # 执行工作流
        result = app.invoke(initial_state)

        # 打印最终执行的代码（保持与旧版本兼容）
        if result.get("executed_code"):
            print(result["executed_code"])

        return result.get("execution_result")


if __name__ == "__main__":
    # 测试示例
    print("DataExtractLangGraph Demo")
    print("=" * 50)
    from web_apps import app

    with app.app_context():
        from utils.etl_utils import get_reader_model

        flag, reader = get_reader_model({'model_id': 'bfa33e81-4b46-4375-8172-4326ee204cee'})
        if flag:
            agent = DataExtractLangGraph(reader=reader)
            result = agent.run("查询前10条数据")
            print(f"结果类型: {type(result)}")
            if result and 'value' in result:
                print(f"DataFrame shape: {result['value'].shape}")
                print(result['value'].head())
