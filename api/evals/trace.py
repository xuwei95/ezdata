"""SSE 事件流 → 归一 Trace。

Trace 是打分器的唯一输入,可来自:
- live 模式:排空 `chat_services()` 产出的 SSE json 行;
- replay 模式:读回放录制的同格式 jsonl。
两条路共用 `Trace.from_sse_lines`,故 replay 测到的解析/打分逻辑 == live 跑的逻辑。

事件形状对齐 ai_chat_service._stream_agent:
  {type:meta, session_id} / {type:run_info, run_id}
  {type:tool, phase:start|end|error, id, name, args?/result?/error?, agentName?}
  {type:content, content} / {type:reasoning, content} / {type:metrics, metrics}
  {type:artifact, artifact:{kind, cfg?, rows?, total?, saveable?}}
  {type:ui_action, action:{...}} / {type:error, error}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    args: Any = None          # start 事件的(已截断)入参
    result: Any = None        # end 事件的(已截断)结果文本
    error: str | None = None  # error 事件文本;非 None 即该工具调用失败
    status: str = 'pending'   # pending | ok | error

    @property
    def ok(self) -> bool:
        return self.status == 'ok'


@dataclass
class Trace:
    session_id: str | None = None
    run_id: str | None = None
    tools: list[ToolCall] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    ui_actions: list[dict] = field(default_factory=list)
    final_text: str = ''
    reasoning_text: str = ''
    metrics: dict = field(default_factory=dict)
    error: str | None = None  # 流级错误(整轮异常)

    # ---- 便捷视图(打分器用)----
    def tool_names(self) -> list[str]:
        return [t.name for t in self.tools]

    def tool_calls(self, name: str) -> list[ToolCall]:
        return [t for t in self.tools if t.name == name]

    def charts(self) -> list[dict]:
        return [a for a in self.artifacts if a.get('kind') in ('chart', 'echart')]

    def tables(self) -> list[dict]:
        return [a for a in self.artifacts if a.get('kind') == 'table']

    def has_tool_error(self) -> bool:
        return any(t.status == 'error' for t in self.tools)

    @classmethod
    def from_sse_lines(cls, lines: list[str]) -> Trace:
        """把一组 SSE json 行归一成 Trace。空行/非 json 行跳过。"""
        tr = cls()
        by_id: dict[str, ToolCall] = {}
        for raw in lines:
            raw = (raw or '').strip()
            if not raw:
                continue
            try:
                ev = json.loads(raw)
            except (ValueError, TypeError):
                continue
            typ = ev.get('type')
            if typ == 'meta':
                tr.session_id = ev.get('session_id')
            elif typ == 'run_info':
                tr.run_id = ev.get('run_id')
            elif typ == 'tool':
                tc = by_id.get(ev.get('id'))
                if tc is None:
                    tc = ToolCall(id=ev.get('id') or f'_{len(tr.tools)}', name=ev.get('name') or '')
                    by_id[tc.id] = tc
                    tr.tools.append(tc)
                phase = ev.get('phase')
                if phase == 'start':
                    tc.args = ev.get('args')
                    if tc.name == '':
                        tc.name = ev.get('name') or ''
                elif phase == 'end':
                    tc.result = ev.get('result')
                    if tc.status != 'error':
                        tc.status = 'ok'
                elif phase == 'error':
                    tc.error = ev.get('error')
                    tc.status = 'error'
            elif typ == 'content':
                tr.final_text += ev.get('content') or ''
            elif typ == 'reasoning':
                tr.reasoning_text += ev.get('content') or ''
            elif typ == 'metrics':
                tr.metrics = ev.get('metrics') or {}
            elif typ == 'artifact':
                art = ev.get('artifact')
                if isinstance(art, dict):
                    tr.artifacts.append(art)
            elif typ == 'ui_action':
                act = ev.get('action')
                if isinstance(act, dict):
                    tr.ui_actions.append(act)
            elif typ == 'error':
                tr.error = ev.get('error')
        return tr
