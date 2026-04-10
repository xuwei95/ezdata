from typing import Annotated, Any, Dict, List, Optional
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from deepagents import create_deep_agent
from web_apps.llm.llm_utils import get_llm
from utils.common_utils import get_now_time, df_to_list
import traceback
import os
import queue
import threading


class DataChatDeepAgent:
    """
    数据分析对话 Agent - DeepAgents 实现

    功能：
    1. 查询知识库获取相关信息
    2. 获取数据模型信息提示
    3. 自动生成并执行数据分析代码
    4. 错误自动修复和重试
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
            answer: 预设答案（知识库中已有的代码答案）
            retry: 最大重试次数
            max_token: 最大 token 数（用于判断是否需要筛选数据模型）
            enable_review: 是否启用代码审查（Human-in-the-Loop）
            web_mode: True=Web 模式（Redis 轮询），False=CLI 模式（input）
            redis_manager: Redis 反馈管理器（web_mode=True 时使用）
            feedback_timeout: 等待反馈超时秒数
            feedback_interval: Redis 轮询间隔秒数
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
        self.conversation_id: Optional[str] = None  # 由调用方设置，用于 Redis key

        # 运行时状态（每次 run/chat 前重置）
        self._flow_data: List[Dict] = []
        self._execution_result: Optional[Dict] = None  # 保存结构化执行结果
        self._parsed_result: Optional[Dict] = None     # 解析后的结果

        # Human-in-the-Loop 状态（线程间通信）
        self._pending_review: Optional[Dict] = None   # 工具写入，chat() 读取并 yield
        self._review_queue: Optional[queue.Queue] = None  # chat() 写入反馈，工具读取
        self._code_exec_count: int = 0                # 记录 execute_python_code 调用次数（含失败）

    # ==================== 辅助方法 ====================

    def _yield_message_stream(self, msg_chunk):
        """
        从 AIMessageChunk 中提取流式 thinking/text 内容并 yield。
        - thinking block: {"type": "thinking", "thinking": "..."}  → type='thinking'
        - text block:     {"type": "text",     "text": "..."}      → type='flow'
        - 非结构化字符串内容（部分模型）: additional_kwargs.reasoning_content → type='thinking'
        """
        from langchain_core.messages import AIMessageChunk
        if not isinstance(msg_chunk, AIMessageChunk):
            return

        content = msg_chunk.content

        # 结构化 content blocks（Claude extended thinking）
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get('type')
                if btype == 'thinking':
                    text = block.get('thinking', '') or block.get('thinking_delta', '')
                    if text:
                        yield {'content': text, 'type': 'thinking'}
                elif btype == 'text':
                    text = block.get('text', '')
                    if text:
                        yield {'content': text, 'type': 'text'}

        # 纯字符串 content（普通文本 token，部分推理模型 content 为空但 reasoning 在 additional_kwargs）
        elif isinstance(content, str):
            reasoning = (msg_chunk.additional_kwargs.get('reasoning_content')
                         or msg_chunk.additional_kwargs.get('thinking'))
            if reasoning:
                yield {'content': reasoning, 'type': 'thinking'}
            elif content:
                yield {'content': content, 'type': 'text'}

    def _make_flow(self, title: str, content: Any, flow_type: str = 'flow') -> Dict:
        """构造一条流程数据（不存入 _flow_data）"""
        return {
            'content': {
                'title': title,
                'content': content,
                'time': get_now_time(res_type='datetime')
            },
            'type': flow_type
        }

    def _add_flow_data(self, title: str, content: Any, flow_type: str = 'flow'):
        """添加流程追踪数据"""
        self._flow_data.append({
            'content': {
                'title': title,
                'content': content,
                'time': get_now_time(res_type='datetime')
            },
            'type': flow_type
        })

    def _reset_state(self):
        """重置运行时状态"""
        self._flow_data = []
        self._execution_result = None
        self._parsed_result = None
        self._pending_review = None
        self._review_queue = None
        self._code_exec_count = 0

    def _parse_execution_result(self, result: Dict) -> Dict:
        """将代码执行结果解析为统一的输出格式"""
        if result['type'] == 'html':
            return {'content': result['value'], 'type': 'html'}
        elif result['type'] == 'dataframe':
            data_li = df_to_list(result['value'])
            return {'content': data_li, 'type': 'data'}
        else:
            return {'content': result['value'], 'type': 'text'}

    # ==================== Human-in-the-Loop 辅助方法 ====================

    def _request_review(self, review_type: str, code: str) -> str:
        """
        在后台线程（工具函数）中调用：设置 _pending_review 并阻塞等待反馈。
        chat() 主线程检测到 _pending_review 后 yield waiting_feedback，
        收到用户反馈后通过 _review_queue 解锁本方法。

        Returns:
            用户反馈字符串，超时返回 'timeout'
        """
        self._review_queue = queue.Queue()
        self._pending_review = {
            'review_type': review_type,
            'generated_code': code,
            'llm_result': code,
            'prompt': (
                '请审查以下生成的代码，输入 yes/ok 执行，或输入修改建议重新生成'
                if review_type == 'code_review'
                else f'代码执行失败（已重试 {self._code_exec_count} 次），输入 ok 结束，或输入修改建议重新生成代码'
            )
        }
        try:
            feedback = self._review_queue.get(timeout=self.feedback_timeout)
        except queue.Empty:
            feedback = 'timeout'
        finally:
            self._pending_review = None
            self._review_queue = None
        return feedback

    def _handle_exec_error(self, code: str, error_msg: str) -> str:
        """
        执行失败后判断是否触发 error_feedback（重试次数耗尽），
        否则直接返回错误信息让 LLM 自动修复。
        """
        if self._code_exec_count >= self.max_retry:
            # 重试耗尽，请求人工介入
            feedback = self._request_review('error_feedback', code)
            if feedback == 'timeout' or feedback.lower() == 'ok':
                self._add_flow_data('错误反馈', f'流程终止，反馈: {feedback}')
                return "用户选择终止流程"
            # 有修改建议，重置计数并让 LLM 重新生成
            self._code_exec_count = 0
            self._add_flow_data('错误反馈：用户要求修改', f'反馈: {feedback}')
            return f"用户反馈：{feedback}，请根据反馈修改代码后重新生成"
        return error_msg

    def _collect_feedback(self) -> str:
        """
        在 chat() 主线程中调用：从 CLI 或 Redis 收取用户反馈并返回。
        """
        if not self.web_mode:
            # CLI 模式：阻塞式 input
            review_data = self._pending_review or {}
            code = review_data.get('generated_code', '')
            print(f"\n{'='*60}\n代码审查:\n{code}\n{'='*60}")
            return input("是否执行？(ok/yes 执行，或输入修改建议): ").strip()
        else:
            # Web 模式：通知 Redis 状态，然后轮询等待反馈
            if self.redis_manager and self.conversation_id:
                self.redis_manager.set_status(self.conversation_id, {
                    'status': 'pending_review',
                    **(self._pending_review or {})
                })
                feedback = self.redis_manager.wait_for_feedback(
                    self.conversation_id,
                    timeout=self.feedback_timeout,
                    interval=self.feedback_interval
                )
                return feedback if feedback is not None else 'timeout'
            return 'timeout'

    # ==================== Tools 定义 ====================

    def _create_tools(self) -> list:
        """创建 Agent 使用的工具列表"""

        # ---------- Tool 1: 查询知识库 ----------
        def query_knowledge_base(
            question: Annotated[str, "用户提出的问题"],
        ) -> str:
            """
            查询知识库，获取与问题相关的知识信息或预设答案代码。
            如果知识库中有匹配的答案，返回可以直接使用的 Python 代码；否则返回相关背景知识。
            """
            self._add_flow_data('查询知识库', f'查询问题: {question}')

            result_parts = []

            if self.knowledge:
                result_parts.append(f"知识库背景信息:\n{self.knowledge}")
                self._add_flow_data('知识库查询结果', f'找到知识库信息，长度: {len(self.knowledge)}')

            if self.answer:
                result_parts.append(f"知识库预设答案（可直接使用的代码）:\n{self.answer}")
                self._add_flow_data('知识库预设答案', '找到预设代码答案，可直接执行')

            if not result_parts:
                self._add_flow_data('知识库查询结果', '知识库中没有相关信息')
                return "知识库中没有相关信息，请根据数据模型信息自行生成代码。"

            return "\n\n".join(result_parts)

        # ---------- Tool 2: 获取数据模型信息 ----------
        def get_data_model_info(
            question: Annotated[str, "用户提出的问题，用于筛选相关数据模型"],
        ) -> str:
            """
            获取数据模型的详细信息提示，包含数据字段名称、类型、描述等元信息。
            这些信息是生成正确数据查询代码的基础，必须先调用此工具再生成代码。
            如果数据模型信息过长，会自动根据问题筛选出相关模型。
            """
            self._add_flow_data('获取数据模型信息', '开始获取数据模型元信息')

            info_prompt = self.reader.get_info_prompt('')

            if len(info_prompt) > self.max_token:
                # 信息过长，使用 LLM 筛选相关模型
                model_list = self.reader.gen_models()
                model_list = [{'type': i['type'], 'name': i['model_conf']['name']} for i in model_list]

                filter_prompt = (
                    f"你正在进行数据分析任务，有以下数据模型：\n{model_list}\n"
                    f"请根据问题：\n{question}\n"
                    f"从以上数据模型中筛选出你需要的模型名称列表，只需要返回名称列表，用逗号隔开，不要其他内容"
                )
                model_prompt = self.llm.invoke(filter_prompt, config={"callbacks": []}).content
                info_prompt = self.reader.get_info_prompt(model_prompt)
                self._add_flow_data('数据模型筛选完成', f'根据问题筛选出的相关模型: {model_prompt}')
            else:
                self._add_flow_data('数据模型信息获取完成', f'信息长度: {len(info_prompt)} 字符')

            return info_prompt

        # ---------- Tool 3: 执行 Python 代码 ----------
        def execute_python_code(
            code: Annotated[str, (
                "要执行的完整 Python 代码。"
                "代码中可直接使用 reader 对象（已自动注入）。"
                "代码末尾必须声明 result 变量，格式为字典: "
                "{'type': 'string'|'dataframe'|'html', 'value': <实际值>}。"
                "如需绘图使用 pyecharts，通过 render_embed() 返回 html 类型。"
            )],
        ) -> str:
            """
            执行 Python 数据分析代码。
            - 代码中可使用 reader 对象访问数据源
            - 必须在代码末尾声明 result 变量（dict，包含 type 和 value 字段）
            - 执行失败时返回详细错误信息，可据此修复代码后重试
            - 结果类型：string（文本）、dataframe（表格）、html（图表）
            """
            self._add_flow_data('开始执行代码', f'执行代码:\n```python\n{code}\n```')
            safe_mode = os.environ.get('SAFE_MODE', 'false').lower() == 'true'

            # ---------- 代码审查（执行前）----------
            if self.enable_review:
                feedback = self._request_review('code_review', code)
                if feedback == 'timeout':
                    self._add_flow_data('代码审查超时', '等待审查超时，取消执行')
                    return "代码审查超时，流程已终止"
                if feedback.lower() not in ('ok', 'yes', 'y'):
                    self._add_flow_data('代码审查：用户要求修改', f'反馈: {feedback}')
                    return f"用户审查反馈：{feedback}，请根据反馈修改代码后重新生成"
                self._add_flow_data('代码审查通过', '用户确认执行代码')

            try:
                if safe_mode:
                    from utils.sandbox_utils import execute_data_in_sandbox
                    result = execute_data_in_sandbox(
                        code=code,
                        model_info=self.reader.model_info,
                        timeout=600
                    )
                    if result.get('success'):
                        exec_result = result.get('result')
                        self._execution_result = exec_result
                        self._parsed_result = self._parse_execution_result(exec_result)
                        self._add_flow_data('代码执行成功', f'沙箱执行成功，结果类型: {exec_result.get("type")}')
                        return _describe_result(exec_result)
                    else:
                        error_msg = result.get("error", "Unknown error")
                        self._add_flow_data('代码执行失败', f'沙箱执行失败:\n{error_msg}')
                        self._code_exec_count += 1
                        return self._handle_exec_error(code, error_msg)
                else:
                    environment = {'reader': self.reader}
                    exec(code, environment)

                    if "result" not in environment:
                        raise ValueError("代码中没有声明 result 变量，请在代码末尾添加 result = {'type': ..., 'value': ...}")

                    exec_result = environment['result']
                    self._execution_result = exec_result
                    self._parsed_result = self._parse_execution_result(exec_result)
                    self._add_flow_data('代码执行成功', f'本地执行成功，结果类型: {exec_result.get("type")}')
                    return _describe_result(exec_result)

            except Exception as e:
                error_traceback = traceback.format_exc()
                error_msg = (
                    f"执行失败:\n"
                    f"错误类型: {type(e).__name__}\n"
                    f"错误信息: {str(e)}\n"
                    f"堆栈追踪:\n{error_traceback}"
                )
                self._add_flow_data('代码执行失败', error_msg)
                self._code_exec_count += 1
                return self._handle_exec_error(code, error_traceback)

        def _describe_result(result: Dict) -> str:
            """将执行结果转为 LLM 可读的描述（不含原始大数据）"""
            if result['type'] == 'html':
                return "[执行成功] 已生成 HTML 图表，结果已保存。"
            elif result['type'] == 'dataframe':
                data_li = df_to_list(result['value'])
                rows = len(data_li)
                cols = len(data_li[0]) if data_li else 0
                preview = str(data_li[:3]) if data_li else "[]"
                return f"[执行成功] 已生成数据表格，共 {rows} 行 {cols} 列。\n前3行预览:\n{preview}"
            else:
                value_str = str(result['value'])
                preview = value_str[:500] + '...' if len(value_str) > 500 else value_str
                return f"[执行成功] 文本结果:\n{preview}"

        return [
            StructuredTool.from_function(
                name="query_knowledge_base",
                description="查询知识库，获取与问题相关的背景知识或预设代码答案",
                func=query_knowledge_base,
            ),
            StructuredTool.from_function(
                name="get_data_model_info",
                description="获取数据模型的详细元信息（字段、类型等），生成代码前必须先调用此工具",
                func=get_data_model_info,
            ),
            StructuredTool.from_function(
                name="execute_python_code",
                description="执行 Python 数据分析代码，代码中可使用 reader 对象，末尾必须声明 result 变量",
                func=execute_python_code,
            ),
        ]

    # ==================== System Prompt ====================

    def _build_system_prompt(self) -> str:
        result_example = (
            '{"type": "string", "value": "100"} 或 '
            '{"type": "dataframe", "value": pd.DataFrame({...})} 或 '
            '{"type": "html", "value": line.render_embed()}'
        )
        return f"""你是一个专业的数据分析助手。根据用户问题，完成数据查询与分析任务。

## 工作流程

1. **查询知识库**：首先调用 `query_knowledge_base` 获取相关背景知识或预设答案
2. **获取数据模型信息**：调用 `get_data_model_info` 了解可用的数据字段和结构
3. **生成并执行代码**：根据上述信息，编写 Python 代码并调用 `execute_python_code` 执行
4. **修复重试**：若执行失败，根据错误信息修复代码，最多重试 {self.max_retry} 次

## 代码编写规范

- 代码中可直接使用 `reader` 对象（已自动注入，无需声明）
- 代码末尾必须声明 `result` 变量，格式: `{result_example}`
- 如需绘制图表，使用 `pyecharts` 库，通过 `render_embed()` 返回 html 类型
- 可 import 所需的任何标准库或第三方库
- 请在代码中用**中文**添加必要注释

## 注意事项

- 如果知识库中有预设答案代码，优先尝试使用
- 执行失败时仔细分析错误信息，针对性地修复
- 不需要向用户解释代码细节，专注于获取正确结果
- 最终结果已通过工具返回，无需重复输出数据内容
"""

    # ==================== Agent 创建 ====================

    def _create_agent(self):
        """创建 DeepAgents 实例"""
        tools = self._create_tools()
        system_prompt = self._build_system_prompt()

        agent = create_deep_agent(
            model=self.llm,
            tools=tools,
            system_prompt=system_prompt,
        )
        return agent

    # ==================== 公共接口 ====================

    def run(self, prompt: str, history_context: str = "") -> Dict:
        """
        同步运行，返回解析后的结果

        Returns:
            dict: 包含 parsed_result 和 flow_data 的字典
        """
        self._reset_state()
        agent = self._create_agent()

        full_prompt = self._build_full_prompt(prompt, history_context)
        try:
            agent.invoke({"messages": [HumanMessage(content=full_prompt)]})
        except Exception as e:
            if not self._parsed_result:
                raise

        return {
            "parsed_result": self._parsed_result or {},
            "flow_data": self._flow_data,
        }

    def chat(self, prompt: str, history_context: str = ""):
        """
        流式运行，逐步 yield 流程数据和最终结果。
        支持 Human-in-the-Loop：代码审查和错误反馈。

        实现要点：
        - agent.stream() 在后台线程运行，事件通过 event_queue 传给主线程
        - 当工具需要人工审查时，工具函数阻塞等待 _review_queue
        - 主线程检测到 _pending_review 后：
            1. yield waiting_feedback（前端展示审查界面）
            2. 调用 _collect_feedback() 等待用户反馈
            3. 将反馈写入 _review_queue，解锁工具函数

        Yields:
            dict: flow_data 条目（type='flow'/'thinking'）或最终结果（type='data'/'html'/'text'）
                  或审查请求（type='waiting_feedback'）
        """
        self._reset_state()
        agent = self._create_agent()
        full_prompt = self._build_full_prompt(prompt, history_context)

        # ---- 后台线程：运行 agent.stream() ----
        event_queue = queue.Queue()
        stream_error: list = []

        def _run_stream():
            try:
                for event in agent.stream(
                    {"messages": [HumanMessage(content=full_prompt)]},
                    stream_mode=["updates", "messages"],
                ):
                    event_queue.put(event)
            except Exception as e:
                stream_error.append(e)
            finally:
                event_queue.put(None)  # 结束哨兵

        stream_thread = threading.Thread(target=_run_stream, daemon=True)
        stream_thread.start()

        # ---- 主线程：消费事件 + 处理 H-i-L ----
        yielded_flow_count = 0
        final_text_response = ""
        streamed_text = False  # 是否已通过 messages 事件逐 token 流式输出过文本

        while True:
            # 短超时轮询，以便主线程能检测 _pending_review
            try:
                event = event_queue.get(timeout=0.3)
            except queue.Empty:
                # 队列暂时没有事件：检查是否有待审查请求
                if self._pending_review is not None:
                    # 1. 先 yield 剩余 flow_data（让前端看到审查前的步骤）
                    for item in self._flow_data[yielded_flow_count:]:
                        yield item
                        yielded_flow_count += 1
                    # 2. yield waiting_feedback，前端弹出审查界面
                    yield {'content': self._pending_review, 'type': 'waiting_feedback'}
                    # 3. 阻塞收取反馈（Redis 轮询 / CLI input）
                    feedback = self._collect_feedback()
                    # 4. 将反馈写入队列，解锁后台线程中的工具函数
                    if self._review_queue is not None:
                        self._review_queue.put(feedback)
                continue

            # 哨兵：stream 结束
            if event is None:
                if stream_error:
                    if not self._parsed_result:
                        raise stream_error[0]
                break

            # 代码已执行成功，跳出循环（不等 LLM 二次分析）
            if self._parsed_result:
                continue  # 继续消耗队列直到哨兵，避免后台线程阻塞

            event_type, data = event

            # ---- 处理消息流（token 级别）----
            if event_type == "messages":
                msg_chunk, _meta = data
                for _chunk in self._yield_message_stream(msg_chunk):
                    if _chunk.get('type') == 'text':
                        streamed_text = True
                    yield _chunk

            # ---- 处理状态更新（工具调用/返回）----
            elif event_type == "updates":
                for node_output in data.values():
                    if not isinstance(node_output, dict):
                        continue
                    messages = node_output.get("messages", [])
                    if hasattr(messages, 'value'):
                        messages = messages.value
                    if not isinstance(messages, list):
                        continue

                    for msg in messages:
                        if isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                for tc in msg.tool_calls:
                                    if tc['name'] == 'write_todos':
                                        todos = tc.get('args', {}).get('todos', [])
                                        todo_str = '\n'.join(
                                            f"[{t.get('status', 'pending')}] {t.get('content', '')}"
                                            for t in todos
                                        )
                                        yield self._make_flow('规划任务', todo_str)
                                    else:
                                        args_str = str(tc.get('args', {}))
                                        preview = args_str[:300] + '...' if len(args_str) > 300 else args_str
                                        yield self._make_flow('调用工具', f"工具: {tc['name']}\n参数: {preview}")
                            else:
                                content = msg.content
                                if isinstance(content, str):
                                    final_text_response = content
                                elif isinstance(content, list):
                                    text_parts = [
                                        block.get('text', '')
                                        for block in content
                                        if isinstance(block, dict) and block.get('type') == 'text'
                                    ]
                                    final_text_response = ''.join(text_parts)

                        elif isinstance(msg, ToolMessage):
                            if msg.name == 'write_todos':
                                continue
                            content_str = str(msg.content)
                            preview = content_str[:300] + '...' if len(content_str) > 300 else content_str
                            yield self._make_flow('工具返回', preview)

                # yield 新增的 flow_data（工具内部主动添加的）
                for item in self._flow_data[yielded_flow_count:]:
                    yield item
                    yielded_flow_count += 1

        # 流结束后，yield 剩余未发出的 flow_data
        for item in self._flow_data[yielded_flow_count:]:
            yield item

        # 最后 yield 最终结果
        if self._parsed_result:
            yield self._parsed_result
        elif not streamed_text and final_text_response:
            # 未流式输出过（如非流式模型），整体 yield 一次
            yield {'content': final_text_response, 'type': 'text'}

    def _build_full_prompt(self, prompt: str, history_context: str) -> str:
        """构建包含历史上下文的完整提示"""
        if history_context:
            return f"历史对话上下文:\n{history_context}\n\n当前问题:\n{prompt}"
        return prompt


if __name__ == "__main__":
    print("DataChat DeepAgents")
    print("=" * 50)
    from web_apps import app

    with app.app_context():
        from utils.etl_utils import get_reader_model

        flag, reader = get_reader_model({'model_id': 'c20ae41fcaa74597ab83293add482ff0'})
        agent = DataChatDeepAgent(reader=reader, retry=2)

        for chunk in agent.chat("rag模块的数据库架构是啥"):
            print(chunk)
