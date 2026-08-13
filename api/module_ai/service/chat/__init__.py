"""AI 对话服务的内部协作模块。

ai_chat_service.AiChatService 是对外门面(controller/evals 调用面),真正的实现按职责
拆到本包内:prompts(提示词/意图常量)、session_store(会话与配置读写)等。
拆分原则:纯搬移、零行为变更;门面委派保持公开 API 不变。
"""
