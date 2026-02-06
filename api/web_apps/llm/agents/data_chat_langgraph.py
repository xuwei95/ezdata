from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from web_apps.llm.llm_utils import extract_code, get_llm
from utils.common_utils import get_now_time, df_to_list
import traceback
import time


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
    history_context: str                 # 历史对话上下文字符串

    # Human-in-the-Loop 字段
    human_feedback: Optional[str]        # 人工反馈
    waiting_feedback: Optional[Dict[str, Any]]  # 等待反馈的数据（用于前端展示）


class DataChatLangGraph:
    """
    数据分析对话 Agent - LangGraph 实现

    功能：
    1. 自动生成数据分析代码
    2. 执行代码并返回结果
    3. 错误自动修复和重试
    4. 可选的代码审查（Human-in-the-Loop）
    """

    def __init__(self, llm=None, reader=None, knowledge='', answer='', retry=1, max_token=4000,
                 enable_review=False, web_mode=False, redis_manager=None,
                 feedback_timeout=300, feedback_interval=3):
        """
        初始化 DataChat Agent

        Args:
            llm: 语言模型实例
            reader: 数据读取器
            knowledge: 知识库信息
            answer: 预设答案
            retry: 最大重试次数
            max_token: 最大 token 数
            enable_review: 是否启用代码审查
            web_mode: Web 模式（使用 Redis 轮询）或 CLI 模式（使用 input）
            redis_manager: Redis 反馈管理器
            feedback_timeout: 反馈超时时间（秒），默认 5 分钟
            feedback_interval: 轮询间隔（秒），默认 3 秒
        """
        self.llm = llm or get_llm()
        self.reader = reader
        self.knowledge = knowledge
        self.answer = answer
        self.max_retry = retry
        self.max_token = max_token
        self.enable_review = enable_review
        self.web_mode = web_mode
        self.redis_manager = redis_manager
        self.feedback_timeout = feedback_timeout
        self.feedback_interval = feedback_interval
        self.checkpointer = MemorySaver() if web_mode else None
        self.current_thread_id = None  # 当前执行的线程 ID

    # ==================== 辅助方法 ====================

    def _add_flow_data(self, flow_data: List, title: str, content: Any, flow_type: str = 'flow'):
        """添加流程追踪数据"""
        flow_data.append({
            'content': {
                'title': title,
                'content': content,  # 可以是字符串或字典
                'time': get_now_time(res_type='datetime')
            },
            'type': flow_type
        })

    def _build_code_prompt(self, state: DataChatState) -> str:
        """构建代码生成提示词"""
        result_example = '{ "type": "string", "value": "100" } or { "type": "dataframe", "value": pd.DataFrame({...}) } or { "type": "html", "value": line.render_embed() }'

        human_feedback = state.get('human_feedback', '')
        has_error = state.get('code_exception', '') != ''
        is_regeneration = human_feedback and human_feedback.lower() != 'ok'

        # 构建代码历史部分
        if is_regeneration:
            if has_error:
                code_history = f"""You previously generated this code:
```python
{state.get('executed_code', state.get('generated_code', ''))}
```

The code execution failed with error:
{state.get('code_exception', '')}

The user reviewed the error and provided feedback:
{human_feedback}

Please regenerate the Python code based on the error and user's feedback."""
            else:
                code_history = f"""You previously generated this code:
```python
{state.get('generated_code', '')}
```

The user reviewed the code and provided feedback:
{human_feedback}

Please regenerate the Python code based on the user's feedback."""
        else:
            code_history = ""

        # 基础提示模板
        prompt = f"""
I have a data reader object called reader, and the object information is：
{state['info_prompt']}

{code_history}

Update this initial code:
```python
# TODO: import the required dependencies

# Write code here

# Declare result var:
type (possible values "string", "dataframe", "html"). Example: {result_example}

```

### QUERY

{state['question']}

{state.get('history_context', '')}

Variable `reader` is already declared.

At the end, declare "result" variable as a dictionary of type and value.

If you are asked to plot a chart, use "pyecharts" for charts, use the render_embed() function to return the corresponding html type and the html content value.

Generate python code and return full updated code:
请在代码中使用中文添加必要注释
"""

        # 添加知识库和历史上下文
        if state.get('knowledge'):
            prompt = f"结合知识库信息:\n{state['knowledge']}\n回答以下问题:\n{prompt}"

        return prompt

    def _build_fix_prompt(self, state: DataChatState) -> str:
        """构建代码修复提示词"""
        prompt = f"""
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

        if state.get('knowledge'):
            prompt = f"结合知识库信息:\n{state['knowledge']}\n回答以下问题:\n{prompt}"

        if state.get('history_context'):
            prompt = f"history_context:\n{state['history_context']}\n{prompt}"

        return prompt

    def _display_code_review(self, code: str, explanation: str):
        """展示代码审查界面（CLI 模式）"""
        print("\n" + "=" * 80)
        print("📝 生成的代码如下：")
        print("=" * 80)
        print(code)
        print("=" * 80)
        print("\n💡 LLM 说明：")
        print(explanation)
        print("=" * 80)

    def _display_error_feedback(self, state: DataChatState):
        """展示错误反馈界面（CLI 模式）"""
        print("\n" + "=" * 80)
        print(f"❌ 代码执行失败（已重试 {state.get('retry_count', 0)} 次）")
        print("=" * 80)
        print("错误代码：")
        print(state.get("executed_code", ""))
        print("\n错误信息：")
        print(state.get("code_exception", "未知错误"))
        print("=" * 80)

    def _get_user_input(self, prompt: str) -> str:
        """获取用户输入（CLI 模式）"""
        return input(f"\n{prompt}").strip()

    # ==================== 工作流节点 ====================

    def _generate_info_prompt(self, state: DataChatState) -> DataChatState:
        """生成数据模型信息提示"""
        if state["info_prompt"]:
            return state

        info_prompt = self.reader.get_info_prompt('')

        # 如果信息过长，使用 LLM 筛选相关模型
        if len(info_prompt) > state["max_token"]:
            model_list = self.reader.gen_models()
            model_list = [{'type': i['type'], 'name': i['model_conf']['name']} for i in model_list]

            filter_prompt = (
                f"你正在进行数据分析任务，有以下数据模型：\n{model_list}\n"
                f"请根据问题：\n{state['question']}\n"
                f"从以上数据模型中筛选出你需要的模型名称列表,只需要返回名称列表，用逗号隔开，不要其他内容"
            )
            model_prompt = self.llm.invoke(filter_prompt).content
            info_prompt = self.reader.get_info_prompt(model_prompt)

        return {**state, "info_prompt": info_prompt}

    def _generate_code(self, state: DataChatState) -> DataChatState:
        """生成 Python 代码"""
        flow_data = state.get("flow_data", [])
        human_feedback = state.get('human_feedback', '')
        is_regeneration = human_feedback and human_feedback.lower() != 'ok'
        has_error = state.get('code_exception', '') != ''

        # 如果有预设答案且不是重新生成，使用预设答案
        if state.get('answer') and not is_regeneration:
            llm_result = state['answer']
            code = extract_code(llm_result)
            self._add_flow_data(flow_data, '生成处理代码', '发现知识库中答案，直接使用')
        else:
            # 构建提示词并调用 LLM
            prompt = self._build_code_prompt(state)
            llm_result = self.llm.invoke(prompt).content
            code = extract_code(llm_result)

            # 添加流程数据
            if is_regeneration:
                title = '根据错误反馈重新生成代码' if has_error else '根据用户反馈重新生成代码'
                content = f'用户反馈: {human_feedback}'
                self._add_flow_data(flow_data, title, content)
            else:
                self._add_flow_data(flow_data, '生成处理代码', '开始生成处理代码')

        self._add_flow_data(flow_data, '处理代码生成成功', llm_result)

        return {
            **state,
            "generated_code": code,
            "llm_result": llm_result,
            "flow_data": flow_data,
            "human_feedback": None,
            "code_exception": "" if is_regeneration else state.get("code_exception", "")
        }

    def _request_code_review(self, state: DataChatState) -> DataChatState:
        """请求代码审查（添加等待事件，不阻塞）"""
        # 准备等待反馈的数据
        waiting_feedback_data = {
            'review_type': 'code_review',
            'generated_code': state.get('generated_code', ''),
            'llm_result': state.get('llm_result', ''),
            'prompt': '请审查以下生成的代码，输入 yes/y/ok 执行，或输入修改建议重新生成'
        }

        # 更新状态到 Redis
        if self.redis_manager and self.current_thread_id:
            self.redis_manager.set_status(self.current_thread_id, {
                'status': 'pending_review',
                'review_type': 'code_review',
                'generated_code': state.get('generated_code', ''),
                'llm_result': state.get('llm_result', '')
            })

        return {
            **state,
            "waiting_feedback": waiting_feedback_data  # 特殊字段，会被 yield 出去
        }

    def _human_review(self, state: DataChatState) -> DataChatState:
        """人工代码审查节点（阻塞等待反馈）"""
        flow_data = state.get("flow_data", [])

        if not self.web_mode:
            # CLI 模式：阻塞式获取用户输入
            self._display_code_review(state["generated_code"], state.get("llm_result", ""))
            user_input = self._get_user_input("👉 是否执行此代码？(输入 'ok' 执行，或输入反馈重新生成): ")
            self._add_flow_data(flow_data, '代码审查完成', f'用户反馈: {user_input}', 'code_review')

            return {
                **state,
                "flow_data": flow_data,
                "human_feedback": user_input
            }
        else:
            # Web 模式：轮询等待反馈（阻塞）
            user_input = None
            if self.redis_manager and self.current_thread_id:
                print(f"[Web模式] 等待用户反馈，thread_id={self.current_thread_id}，超时={self.feedback_timeout}秒")
                user_input = self.redis_manager.wait_for_feedback(
                    self.current_thread_id,
                    timeout=self.feedback_timeout,
                    interval=self.feedback_interval
                )

            if user_input is None:
                # 超时，默认拒绝执行
                user_input = "timeout"
                print(f"[Web模式] 等待反馈超时")
            else:
                print(f"[Web模式] 收到用户反馈: '{user_input}'")

            return {
                **state,
                "human_feedback": user_input,
                "waiting_feedback": None  # 清空 waiting_feedback
            }

    def _execute_code(self, state: DataChatState) -> DataChatState:
        """执行 Python 代码"""
        import os

        safe_mode = os.environ.get('SAFE_MODE', 'false').lower() == 'true'
        code = state["generated_code"]
        flow_data = state.get("flow_data", [])

        try:
            # 添加执行开始的 flow_data，包含具体代码和重试次数
            retry_count = state.get("retry_count", 0)
            if retry_count > 0:
                title = f'开始执行代码（第{retry_count + 1}次尝试）'
            else:
                title = '开始执行代码'

            execution_info = f"重试次数: {retry_count}\n\n执行代码:\n```python\n{code}\n```"
            self._add_flow_data(flow_data, title, execution_info, 'flow')

            if safe_mode:
                # 沙箱执行
                from utils.sandbox_utils import execute_data_in_sandbox
                result = execute_data_in_sandbox(
                    code=code,
                    model_info=self.reader.model_info,
                    timeout=600
                )
                if result.get('success'):
                    retry_count = state.get("retry_count", 0)
                    if retry_count > 0:
                        success_msg = f"代码执行成功（经过{retry_count}次修复后成功）\n\n执行的代码:\n```python\n{code}\n```\n\n正在解析结果..."
                    else:
                        success_msg = f"代码执行成功\n\n执行的代码:\n```python\n{code}\n```\n\n正在解析结果..."
                    self._add_flow_data(flow_data, '代码执行成功', success_msg, 'flow')
                    return {
                        **state,
                        "executed_code": code,
                        "execution_result": result.get('result'),
                        "flow_data": flow_data
                    }
                else:
                    error_msg = result.get("error", "Unknown error")
                    error_detail = f"执行失败 (尝试 {retry_count + 1}/{state['max_retry']})\n\n错误信息:\n{error_msg}\n\n错误代码:\n```python\n{code}\n```"
                    self._add_flow_data(flow_data, '代码执行失败', error_detail, 'flow')
                    return {
                        **state,
                        "executed_code": code,
                        "code_exception": result.get('error', 'Unknown error'),
                        "retry_count": state["retry_count"] + 1,
                        "flow_data": flow_data
                    }
            else:
                # 本地执行
                environment = {'reader': self.reader}
                exec(code, environment)

                if "result" not in environment:
                    raise ValueError("No result returned")

                result = environment['result']
                self.answer = state["llm_result"]

                retry_count = state.get("retry_count", 0)
                if retry_count > 0:
                    success_msg = f"代码执行成功（经过{retry_count}次修复后成功）\n\n执行的代码:\n```python\n{code}\n```\n\n正在解析结果..."
                else:
                    success_msg = f"代码执行成功\n\n执行的代码:\n```python\n{code}\n```\n\n正在解析结果..."
                self._add_flow_data(flow_data, '代码执行成功', success_msg, 'flow')
                return {
                    **state,
                    "executed_code": code,
                    "execution_result": result,
                    "flow_data": flow_data
                }

        except Exception as e:
            retry_count = state.get("retry_count", 0)
            error_traceback = traceback.format_exc()
            error_detail = f"执行失败 (尝试 {retry_count + 1}/{state['max_retry']})\n\n错误类型: {type(e).__name__}\n错误信息: {str(e)}\n\n错误代码:\n```python\n{code}\n```\n\n堆栈追踪:\n{error_traceback}"
            self._add_flow_data(flow_data, '代码执行失败', error_detail, 'flow')
            return {
                **state,
                "executed_code": code,
                "code_exception": error_traceback,
                "retry_count": state["retry_count"] + 1,
                "flow_data": flow_data
            }

    def _fix_code(self, state: DataChatState) -> DataChatState:
        """修复错误代码"""
        retry_count = state.get("retry_count", 0)

        # 添加开始修复的提示
        flow_data = state.get("flow_data", [])
        fix_start_info = f"LLM自动修复 (第{retry_count}次修复)\n\n错误代码:\n```python\n{state.get('executed_code', '')}\n```\n\n错误信息:\n{state.get('code_exception', '')}"
        self._add_flow_data(flow_data, f'开始自动修复代码（第{retry_count}次）', fix_start_info, 'flow')

        prompt = self._build_fix_prompt(state)
        llm_result = self.llm.invoke(prompt).content
        new_code = extract_code(llm_result)

        # 添加修复成功的详细信息
        review_hint = "\n\n⚠️ 开启了代码审查，修复后的代码将提交审查" if self.enable_review else ""
        fix_success_info = f"LLM修复完成 (第{retry_count}次修复)\n\n修复后的代码:\n```python\n{new_code}\n```\n\nLLM说明:\n{llm_result}{review_hint}"
        self._add_flow_data(flow_data, f'代码修复完成（第{retry_count}次）', fix_success_info, 'flow')

        return {
            **state,
            "generated_code": new_code,
            "llm_result": llm_result,
            "flow_data": flow_data
        }

    def _request_error_feedback(self, state: DataChatState) -> DataChatState:
        """请求错误反馈（添加等待事件，不阻塞）"""
        # 准备等待反馈的数据
        waiting_feedback_data = {
            'review_type': 'error_feedback',
            'executed_code': state.get('executed_code', ''),
            'code_exception': state.get('code_exception', ''),
            'retry_count': state.get('retry_count', 0),
            'prompt': f'代码执行失败（已重试 {state.get("retry_count", 0)} 次），输入 ok 结束流程，或输入修改建议重新生成代码'
        }

        # 更新状态到 Redis
        if self.redis_manager and self.current_thread_id:
            self.redis_manager.set_status(self.current_thread_id, {
                'status': 'error_feedback',
                'review_type': 'error_feedback',
                'executed_code': state.get('executed_code', ''),
                'code_exception': state.get('code_exception', ''),
                'retry_count': state.get('retry_count', 0)
            })

        return {
            **state,
            "waiting_feedback": waiting_feedback_data  # 特殊字段，会被 yield 出去
        }

    def _human_error_feedback(self, state: DataChatState) -> DataChatState:
        """人工错误反馈节点（阻塞等待反馈）"""
        flow_data = state.get("flow_data", [])

        if not self.web_mode:
            # CLI 模式：阻塞式获取用户输入
            self._display_error_feedback(state)
            user_input = self._get_user_input("👉 输入 'ok' 结束流程，或输入反馈重新生成代码: ")
            self._add_flow_data(flow_data, '错误反馈', f'用户反馈: {user_input}', 'error_feedback')

            return {
                **state,
                "flow_data": flow_data,
                "human_feedback": user_input,
                "retry_count": 0
            }
        else:
            # Web 模式：轮询等待反馈（阻塞）
            user_input = None
            if self.redis_manager and self.current_thread_id:
                print(f"[Web模式] 等待错误反馈，thread_id={self.current_thread_id}，超时={self.feedback_timeout}秒")
                user_input = self.redis_manager.wait_for_feedback(
                    self.current_thread_id,
                    timeout=self.feedback_timeout,
                    interval=self.feedback_interval
                )

            if user_input is None:
                # 超时，默认结束流程
                user_input = "ok"

            return {
                **state,
                "human_feedback": user_input,
                "retry_count": 0,
                "waiting_feedback": None  # 清空 waiting_feedback
            }

    def _parse_result(self, state: DataChatState) -> DataChatState:
        """解析执行结果"""
        result = state["execution_result"]
        flow_data = state.get("flow_data", [])
        retry_count = state.get("retry_count", 0)

        if result['type'] == 'html':
            parsed_result = {'content': result['value'], 'type': 'html'}
            parse_detail = f"结果类型: HTML 图表\n经过修复次数: {retry_count}\n\n"
            self._add_flow_data(flow_data, '结果解析完成', parse_detail, 'flow')
        elif result['type'] == 'dataframe':
            data_li = df_to_list(result['value'])
            parsed_result = {'content': data_li, 'type': 'data'}
            parse_detail = f"结果类型: 数据表格\n经过修复次数: {retry_count}\n\n表格信息:\n- 行数: {len(data_li)}\n- 列数: {len(data_li[0]) if data_li else 0}"
            self._add_flow_data(flow_data, '结果解析完成', parse_detail, 'flow')
        else:
            parsed_result = {'content': result['value'], 'type': 'text'}
            text_preview = str(result['value'])[:200] + '...' if len(str(result['value'])) > 200 else str(result['value'])
            parse_detail = f"结果类型: 文本\n经过修复次数: {retry_count}\n\n文本内容:\n{text_preview}"
            self._add_flow_data(flow_data, '结果解析完成', parse_detail, 'flow')

        return {**state, "parsed_result": parsed_result, "flow_data": flow_data}

    def _handle_error(self, state: DataChatState) -> DataChatState:
        """处理最终错误"""
        flow_data = state.get("flow_data", [])
        retry_count = state.get("retry_count", 0)
        executed_code = state.get("executed_code", "无")
        exception_msg = state.get("code_exception", "未知错误")

        error_detail = f"""任务最终失败

尝试次数: {retry_count}/{state.get('max_retry', 0)}

最后执行的代码:
```python
{executed_code}
```

错误信息:
{exception_msg}

建议: 请检查代码逻辑或数据源配置"""

        self._add_flow_data(
            flow_data,
            '处理失败',
            error_detail
        )
        return {**state, "flow_data": flow_data}

    # ==================== 路由方法 ====================

    def _route_after_review(self, state: DataChatState) -> str:
        """代码审查后的路由"""
        feedback = state.get("human_feedback", "")
        feedback_lower = feedback.lower().strip() if feedback else ""

        # 打印调试信息
        print(f"[路由] 收到的反馈: '{feedback}', 处理后: '{feedback_lower}'")

        # 接受 ok, yes, y 作为确认
        is_approved = feedback_lower in ['ok', 'yes', 'y']

        if is_approved:
            print(f"[路由] 代码已批准，执行代码")
            return "execute_code"
        else:
            print(f"[路由] 代码被拒绝或有修改建议，重新生成")
            return "regenerate_code"

    def _route_after_execution(self, state: DataChatState) -> str:
        """代码执行后的路由"""
        if state.get("execution_result") is not None:
            return "parse_result"
        elif state["retry_count"] < state["max_retry"]:
            return "fix_code"
        else:
            # retry 次数用完后，总是启用人工介入（无论 enable_review 的初始值）
            return "human_error_feedback"

    def _route_after_error_feedback(self, state: DataChatState) -> str:
        """错误反馈后的路由"""
        feedback = state.get("human_feedback", "")
        return "end_with_error" if feedback.lower().strip() == 'ok' else "regenerate_from_error"

    def _route_after_fix(self, state: DataChatState) -> str:
        """代码修复后的路由"""
        if self.enable_review:
            # 如果开启审查，修复后的代码也需要审查
            print(f"[路由] 代码已修复，需要人工审查")
            if self.web_mode:
                return "request_review"
            else:
                return "human_review"
        else:
            # 不开启审查，直接执行
            print(f"[路由] 代码已修复，直接执行")
            return "execute_code"

    # ==================== 工作流构建 ====================

    def create_langgraph_workflow(self):
        """创建 LangGraph 工作流"""
        workflow = StateGraph(DataChatState)

        # 添加节点
        workflow.add_node("generate_info_prompt", self._generate_info_prompt)
        workflow.add_node("generate_code", self._generate_code)
        workflow.add_node("execute_code", self._execute_code)
        workflow.add_node("fix_code", self._fix_code)
        workflow.add_node("parse_result", self._parse_result)
        workflow.add_node("handle_error", self._handle_error)

        # 添加人工审查节点（仅当启用代码审查时）
        if self.enable_review:
            if self.web_mode:
                # Web 模式：分成请求和等待两个节点
                workflow.add_node("request_code_review", self._request_code_review)
                workflow.add_node("human_review", self._human_review)
            else:
                # CLI 模式：只需要一个节点
                workflow.add_node("human_review", self._human_review)

        # 添加错误反馈节点（总是添加，因为错误3次后需要人工介入）
        if self.web_mode:
            workflow.add_node("request_error_feedback", self._request_error_feedback)
            workflow.add_node("human_error_feedback", self._human_error_feedback)
        else:
            workflow.add_node("human_error_feedback", self._human_error_feedback)

        # 设置入口
        workflow.set_entry_point("generate_info_prompt")

        # 基础流程
        workflow.add_edge("generate_info_prompt", "generate_code")

        # 代码生成后的流程
        if self.enable_review:
            if self.web_mode:
                # Web 模式：先请求审查（会被 yield 出去），再等待反馈（阻塞）
                workflow.add_edge("generate_code", "request_code_review")
                workflow.add_edge("request_code_review", "human_review")
            else:
                # CLI 模式：直接进入审查节点
                workflow.add_edge("generate_code", "human_review")

            workflow.add_conditional_edges(
                "human_review",
                self._route_after_review,
                {
                    "execute_code": "execute_code",
                    "regenerate_code": "generate_code"
                }
            )
        else:
            workflow.add_edge("generate_code", "execute_code")

        # 执行和重试流程
        # 无论 enable_review 如何，错误3次后都要人工介入
        if self.web_mode:
            # Web 模式：先请求反馈（会被 yield 出去），再等待反馈（阻塞）
            workflow.add_conditional_edges(
                "execute_code",
                self._route_after_execution,
                {
                    "parse_result": "parse_result",
                    "fix_code": "fix_code",
                    "human_error_feedback": "request_error_feedback"
                }
            )
            workflow.add_edge("request_error_feedback", "human_error_feedback")
        else:
            # CLI 模式：直接进入错误反馈节点
            workflow.add_conditional_edges(
                "execute_code",
                self._route_after_execution,
                {
                    "parse_result": "parse_result",
                    "fix_code": "fix_code",
                    "human_error_feedback": "human_error_feedback"
                }
            )

        # 错误反馈后的路由
        workflow.add_conditional_edges(
            "human_error_feedback",
            self._route_after_error_feedback,
            {
                "end_with_error": "handle_error",
                "regenerate_from_error": "generate_code"
            }
        )

        # 代码修复后的路由
        if self.enable_review:
            # 如果开启审查，修复后需要审查
            if self.web_mode:
                workflow.add_conditional_edges(
                    "fix_code",
                    self._route_after_fix,
                    {
                        "request_review": "request_code_review",
                        "execute_code": "execute_code"
                    }
                )
            else:
                workflow.add_conditional_edges(
                    "fix_code",
                    self._route_after_fix,
                    {
                        "human_review": "human_review",
                        "execute_code": "execute_code"
                    }
                )
        else:
            # 不开启审查，直接执行
            workflow.add_edge("fix_code", "execute_code")

        # 结束节点
        workflow.add_edge("parse_result", END)
        workflow.add_edge("handle_error", END)

        # 编译工作流（不再使用 interrupt_before，直接在节点内轮询等待）
        return workflow.compile()

    # ==================== 公共接口 ====================

    def run(self, prompt, history_context=""):
        """同步运行"""
        app = self.create_langgraph_workflow()

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
            "flow_data": [],
            "history_context": history_context,
            "human_feedback": None,
            "waiting_feedback": None
        }

        result = app.invoke(initial_state)
        return result["parsed_result"]

    def chat(self, prompt, history_context=""):
        """流式运行"""
        app = self.create_langgraph_workflow()

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
            "flow_data": [],
            "history_context": history_context,
            "human_feedback": None,
            "waiting_feedback": None
        }

        yielded_flow_count = 0  # 使用计数器追踪已 yield 的 flow_data 数量

        for chunk in app.stream(initial_state):
            for node_name, node_state in chunk.items():
                print(f"[Stream] 节点: {node_name}")

                # 检查是否有 waiting_feedback 事件
                if 'waiting_feedback' in node_state and node_state['waiting_feedback']:
                    print(f"[Stream] yield waiting_feedback")
                    yield {
                        'content': node_state['waiting_feedback'],
                        'type': 'waiting_feedback'
                    }

                # 处理 flow_data - 只 yield 新增的部分（对所有节点都处理）
                if 'flow_data' in node_state:
                    flow_data = node_state['flow_data']
                    new_flow_count = len(flow_data)
                    print(f"[Stream] flow_data 总数: {new_flow_count}, 已yield: {yielded_flow_count}")

                    # 只 yield 新增的 flow_data
                    for flow_item in flow_data[yielded_flow_count:]:
                        print(f"[Stream] yield flow[{yielded_flow_count}]: {flow_item['content']['title']}")
                        yield flow_item
                        yielded_flow_count += 1

                # 处理 parse_result 节点的最终结果
                if node_name == 'parse_result':
                    if 'parsed_result' in node_state and node_state['parsed_result']:
                        print(f"[Stream] yield parsed_result")
                        yield node_state['parsed_result']


if __name__ == "__main__":
    # 测试示例
    print("DataChat LangGraph Demo")
    print("=" * 50)
    from web_apps import app

    with app.app_context():
        from utils.etl_utils import get_reader_model

        flag, reader = get_reader_model({'model_id': 'c20ae41fcaa74597ab83293add482ff0'})
        agent = DataChatLangGraph(reader=reader, enable_review=True, retry=2)

        for chunk in agent.chat("查询字典项数据，按创建时间按月分组统计数据，画出统计表"):
            print(chunk)
