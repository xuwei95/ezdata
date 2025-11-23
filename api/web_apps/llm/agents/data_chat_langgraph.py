from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from web_apps.llm.llm_utils import extract_code, process_dataframe, get_llm
from utils.common_utils import get_now_time
import traceback


# 定义状态类型
class DataChatState(TypedDict):
    messages: List[BaseMessage]          # 对话消息
    question: str                        # 用户问题
    knowledge: str                       # 知识库信息
    answer: str                          # 预设答案
    info_prompt: str                     # 数据模型信息提示
    generated_code: str                  # 生成的代码
    llm_result: str                      # LLM生成结果
    executed_code: str                   # 最后执行的代码
    code_exception: str                  # 代码执行异常
    execution_result: Any                # 代码执行结果
    parsed_result: Dict[str, Any]       # 解析后的结果
    retry_count: int                     # 重试次数
    max_retry: int                       # 最大重试次数
    max_token: int                       # 最大token数
    flow_data: List[Dict[str, Any]]     # 流程数据


class DataChatLangGraph:
    def __init__(self, llm=None, reader=None, knowledge='', answer='', retry=1, max_token=4000):
        if llm is None:
            self.llm = get_llm()
        else:
            self.llm = llm
        self.reader = reader
        self.knowledge = knowledge
        self.answer = answer
        self.max_retry = retry
        self.max_token = max_token

    def create_info_prompt_generator(self):
        """创建信息提示生成器节点"""
        def generate_info_prompt(state: DataChatState) -> DataChatState:
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
                else:
                    info_prompt = info_prompt
                
                return {
                    **state,
                    "info_prompt": info_prompt
                }
            return state
        
        return generate_info_prompt

    def create_code_generator(self):
        """创建代码生成器节点"""
        def generate_code(state: DataChatState) -> DataChatState:
            """生成Python代码"""
            result_example_prompt = '{ "type": "string", "value": "100" } or { "type": "dataframe", "value": pd.DataFrame({...}) } or { "type": "html", "value": line.render_embed() }'
            
            prompt = f"""
I have a data reader object called reader, and the object information is：
{state['info_prompt']}

Update this initial code:
```python
# TODO: import the required dependencies

# Write code here

# Declare result var: 
type (possible values "string", "dataframe", "html"). Example: {result_example_prompt}

```

### QUERY

{state['question']}

Variable `reader` is already declared.

At the end, declare "result" variable as a dictionary of type and value.

If you are asked to plot a chart, use "pyecharts" for charts, use the render_embed() function to return the corresponding html type and the html content value.

Generate python code and return full updated code:
请在代码中使用中文添加必要注释
"""
            
            if state['knowledge'] != '':
                prompt = f"结合知识库信息:\n{state['knowledge']}\n回答以下问题:\n{prompt}"
            
            llm_result = self.llm.invoke(prompt).content
            code = extract_code(llm_result)
            
            # 添加流程数据
            flow_data = state.get("flow_data", [])
            if state['answer'] != '':
                flow_data.append({
                    'content': {
                        'title': '生成处理代码', 
                        'content': '发现知识库中答案，直接使用',
                        'time': get_now_time(res_type='datetime')
                    }, 
                    'type': 'flow'
                })
            else:
                flow_data.append({
                    'content': {
                        'title': '生成处理代码', 
                        'content': '开始生成处理代码',
                        'time': get_now_time(res_type='datetime')
                    }, 
                    'type': 'flow'
                })
            
            flow_data.append({
                'content': {
                    'title': '处理代码生成成功', 
                    'content': llm_result,
                    'time': get_now_time(res_type='datetime')
                }, 
                'type': 'flow'
            })
            
            return {
                **state,
                "generated_code": code,
                "llm_result": llm_result,
                "flow_data": flow_data
            }
        
        return generate_code

    def create_code_executor(self):
        """创建代码执行器节点"""
        def execute_code(state: DataChatState) -> DataChatState:
            """执行Python代码"""
            code = state["generated_code"]
            
            # 添加流程数据
            flow_data = state.get("flow_data", [])
            flow_data.append({
                'content': {
                    'title': '执行处理代码', 
                    'content': f"```python\n{code}\n```", 
                    'time': get_now_time(res_type='datetime')
                }, 
                'type': 'flow'
            })
            
            try:
                environment = {'reader': self.reader}
                exec(code, environment)
                
                if "result" not in environment:
                    raise ValueError("No result returned")
                else:
                    result = environment['result']
                    
                    # 添加成功流程数据
                    flow_data.append({
                        'content': {
                            'title': '处理完成', 
                            'content': '处理完成', 
                            'time': get_now_time(res_type='datetime')
                        }, 
                        'type': 'flow'
                    })
                    
                    return {
                        **state,
                        "executed_code": code,
                        "execution_result": result,
                        "flow_data": flow_data
                    }
                    
            except Exception as e:
                traceback_errors = traceback.format_exc()
                
                # 添加错误流程数据
                flow_data.append({
                    'content': {
                        'title': '执行代码出错，修复代码', 
                        'content': f'执行代码报错：{traceback_errors}', 
                        'time': get_now_time(res_type='datetime')
                    }, 
                    'type': 'flow'
                })
                
                return {
                    **state,
                    "executed_code": code,
                    "code_exception": traceback_errors,
                    "flow_data": flow_data
                }
        
        return execute_code

    def create_code_fixer(self):
        """创建代码修复器节点"""
        def fix_code(state: DataChatState) -> DataChatState:
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
            
            if state['knowledge'] != '':
                fix_code_prompt = f"结合知识库信息:\n{state['knowledge']}\n回答以下问题:\n{fix_code_prompt}"
            
            llm_result = self.llm.invoke(fix_code_prompt).content
            new_code = extract_code(llm_result)
            
            # 添加修复成功流程数据
            flow_data = state.get("flow_data", [])
            flow_data.append({
                'content': {
                    'title': '修复处理代码成功', 
                    'content': llm_result, 
                    'time': get_now_time(res_type='datetime')
                }, 
                'type': 'flow'
            })
            
            return {
                **state,
                "generated_code": new_code,
                "llm_result": llm_result,
                "flow_data": flow_data
            }
        
        return fix_code

    def create_result_parser(self):
        """创建结果解析器节点"""
        def parse_result(state: DataChatState) -> DataChatState:
            """解析执行结果"""
            result = state["execution_result"]
            
            if result['type'] == 'html':
                parsed_result = {'content': result['value'], 'type': 'html'}
            elif result['type'] == 'dataframe':
                data_li = process_dataframe(result)
                parsed_result = {'content': data_li, 'type': 'data'}
            else:
                parsed_result = {'content': result['value'], 'type': 'text'}
            
            return {
                **state,
                "parsed_result": parsed_result
            }
        
        return parse_result

    def create_retry_router(self):
        """创建重试路由节点"""
        def route_retry(state: DataChatState) -> str:
            """根据执行结果决定下一步"""
            if "execution_result" in state and state["execution_result"] is not None:
                # 执行成功，继续解析结果
                return "parse_result"
            elif state["retry_count"] < state["max_retry"]:
                # 需要重试，修复代码
                return "fix_code"
            else:
                # 重试次数用完，结束
                return "end_with_error"
        
        return route_retry

    def create_error_handler(self):
        """创建错误处理节点"""
        def handle_error(state: DataChatState) -> DataChatState:
            """处理最终错误"""
            flow_data = state.get("flow_data", [])
            flow_data.append({
                'content': {
                    'title': '处理失败', 
                    'content': f'处理失败：{state.get("code_exception", "未知错误")}', 
                    'time': get_now_time(res_type='datetime')
                }, 
                'type': 'flow'
            })
            
            return {
                **state,
                "flow_data": flow_data
            }
        
        return handle_error

    def create_langgraph_workflow(self):
        """创建LangGraph工作流"""
        # 创建工作流图
        workflow = StateGraph(DataChatState)
        
        # 添加节点
        workflow.add_node("generate_info_prompt", self.create_info_prompt_generator())
        workflow.add_node("generate_code", self.create_code_generator())
        workflow.add_node("execute_code", self.create_code_executor())
        workflow.add_node("fix_code", self.create_code_fixer())
        workflow.add_node("parse_result", self.create_result_parser())
        workflow.add_node("handle_error", self.create_error_handler())
        
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
                "parse_result": "parse_result",
                "fix_code": "fix_code",
                "end_with_error": "handle_error"
            }
        )
        
        # 添加重试边
        workflow.add_edge("fix_code", "execute_code")
        
        # 设置结束点
        workflow.add_edge("parse_result", END)
        workflow.add_edge("handle_error", END)
        return workflow.compile()

    def run(self, prompt):
        """同步运行"""
        # 创建工作流
        app = self.create_langgraph_workflow()
        
        # 初始化状态
        initial_state = {
            "messages": [HumanMessage(content=prompt)],
            "question": prompt,
            "knowledge": self.knowledge,
            "answer": self.answer,
            "info_prompt": "",
            "generated_code": "",
            "llm_result": "",
            "executed_code": "",
            "code_exception": "",
            "execution_result": None,
            "parsed_result": {},
            "retry_count": 0,
            "max_retry": self.max_retry,
            "max_token": self.max_token,
            "flow_data": []
        }
        
        # 执行工作流
        result = app.invoke(initial_state)
        
        return result["parsed_result"]

    def chat(self, prompt):
        """流式运行"""
        # 创建工作流
        app = self.create_langgraph_workflow()
        # 初始化状态
        initial_state = {
            "messages": [HumanMessage(content=prompt)],
            "question": prompt,
            "knowledge": self.knowledge,
            "answer": self.answer,
            "info_prompt": "",
            "generated_code": "",
            "llm_result": "",
            "executed_code": "",
            "code_exception": "",
            "execution_result": None,
            "parsed_result": {},
            "retry_count": 0,
            "max_retry": self.max_retry,
            "max_token": self.max_token,
            "flow_data": []
        }
        
        # 执行工作流（流式）
        for chunk in app.stream(initial_state):
            yield chunk


if __name__ == "__main__":
    # 测试示例
    print("DataChat LangGraph Demo")
    print("=" * 50)
    from web_apps import app
    with app.app_context():
        from utils.etl_utils import get_reader_model
        flag, reader = get_reader_model({'model_id': 'e222b61c62be4d09908a5bc94aebf22d'})
        # 这里需要提供实际的reader对象进行测试
        agent = DataChatLangGraph(reader=reader)
        # result = agent.run("查询数据")
        # print(f"结果: {result}")
        for chunk in agent.chat("查询前10条数据"):
            print(chunk)