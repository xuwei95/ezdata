"""对话 agent 输入侧护栏(pre_hooks):在用户/上游内容进入 LLM 之前拦截。

- PromptInjectionGuardrail(内置):拦常见提示注入套路。本项目 agent 会把数据源 remark、
  知识库分段、取回的数据行、收藏的"解法"等**他人写的内容**注入上下文,这些是注入的主要入口。
- DangerousIntentGuardrail(自研):拦高危写操作/删库意图,与沙箱只读护栏叠加,输入层再兜一道。

用法:挂在 Agent(pre_hooks=build_pre_hooks());命中抛 InputCheckError,由上层(_stream_agent)
兜住回友好提示。这是**输入层**防线,不替代沙箱隔离执行与 handler 只读。
"""

from __future__ import annotations

from typing import Any

from agno.exceptions import CheckTrigger, InputCheckError
from agno.guardrails import BaseGuardrail, PromptInjectionGuardrail


class DangerousIntentGuardrail(BaseGuardrail):
    """拦高危写操作/删库意图。规则式,兜常见套路;不替代权限与只读护栏。"""

    _BAD = (
        'drop table', 'drop database', 'truncate table', 'delete from',
        'format c:', 'rm -rf', '删库', '清空所有数据', '格式化硬盘',
    )

    def _hit(self, run_input: Any) -> str | None:
        text = run_input.input_content_string().lower()
        return next((b for b in self._BAD if b in text), None)

    def check(self, run_input: Any) -> None:
        hit = self._hit(run_input)
        if hit:
            raise InputCheckError(
                f'检测到高危操作意图({hit}),已拦截。如需执行请通过受控的任务/审批流程。',
                check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
            )

    async def async_check(self, run_input: Any) -> None:
        self.check(run_input)


# 内置 PromptInjectionGuardrail 仅含英文模式;本平台以中文为主,补中文注入套路。
_ZH_INJECTION_PATTERNS = [
    '忽略以上', '忽略之前', '忽略上述', '忽略前面', '无视以上', '无视之前', '无视上述',
    '忘记之前', '忘记以上', '你现在是', '现在你是', '从现在起你是', '假装你是', '假装成',
    '扮演', '进入开发者模式', '开发者模式', '越狱', '系统提示词', '绕过限制', '解除限制', '管理员权限',
]


def build_pre_hooks() -> list:
    """对话 agent 的输入侧护栏列表(供 Agent(pre_hooks=...))。

    PromptInjectionGuardrail 合并「内置英文模式 + 中文注入模式」(内置默认仅英文,中文平台会漏)。
    """
    default_patterns = list(PromptInjectionGuardrail().injection_patterns)
    injection = PromptInjectionGuardrail(injection_patterns=default_patterns + _ZH_INJECTION_PATTERNS)
    return [injection, DangerousIntentGuardrail()]
