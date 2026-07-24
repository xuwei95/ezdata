"""跑 agent 收 trace。两种模式共用 SSE→Trace 解析:

- replay:读回放录制的 SSE jsonl(用例 fixtures)。任何机器可跑,CI/测试用。
- live  :实跑 chat_services(需 DB/ES/模型/沙箱环境),并把 SSE 录到 fixtures/ 供以后回放。

用例每次重跑得到一个 Trace,按 case.checks 打分 → RunResult;N 次 → CaseResult。
"""

from __future__ import annotations

import os
from dataclasses import replace

from evals.cases import EvalCase
from evals.report import CaseResult, RunResult
from evals.scorers import score_trace
from evals.trace import Trace

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _read_jsonl(path: str) -> list[str]:
    with open(path, encoding='utf-8') as f:
        return f.readlines()


def _score(case: EvalCase, trace: Trace, error: str | None = None) -> RunResult:
    if error:
        return RunResult(checks=[], error=error, tool_calls=len(trace.tools))
    return RunResult(checks=score_trace(case, trace), tool_calls=len(trace.tools))


# ---------------- replay ----------------

def run_case_replay(case: EvalCase) -> CaseResult:
    cr = CaseResult(case_id=case.id, tags=case.tags, model_id=case.model_id)
    fixtures = case.fixtures or _autodiscover_fixtures(case.id)
    if not fixtures:
        cr.runs.append(RunResult(checks=[], error=f'无 fixture 可回放(cases/ 里给 fixtures 或放 fixtures/{case.id}.run*.jsonl)'))
        return cr
    for fx in fixtures:
        path = fx if os.path.isabs(fx) else os.path.join(FIXTURES_DIR, fx)
        try:
            trace = Trace.from_sse_lines(_read_jsonl(path))
            cr.runs.append(_score(case, trace))
        except FileNotFoundError:
            cr.runs.append(RunResult(checks=[], error=f'fixture 不存在: {fx}'))
    return cr


def _autodiscover_fixtures(case_id: str) -> list[str]:
    import glob
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(FIXTURES_DIR, f'{case_id}.run*.jsonl')))


# ---------------- live ----------------

async def _live_once(case: EvalCase, user_id: int, record_path: str | None) -> tuple[Trace, str | None]:
    """实跑一次:调 chat_services 排空 SSE。重依赖在函数内 import,避免 replay/测试引入整个 app。"""
    try:
        from config.database import AsyncSessionLocal
        from module_ai.entity.vo.ai_chat_vo import AiChatRequestModel
        from module_ai.service.ai_chat_service import AiChatService
    except Exception as e:
        return Trace(), f'导入 app 失败(live 需完整后端环境): {type(e).__name__}: {e}'

    # AiChatRequestModel 用 to_camel 别名,须按别名构造(modelId/sessionId/appId)
    req = AiChatRequestModel.model_validate({
        'sessionId': None, 'modelId': case.model_id, 'message': case.question, 'appId': case.app_id,
    })
    lines: list[str] = []
    try:
        async with AsyncSessionLocal() as db:
            async for chunk in AiChatService.chat_services(db, req, user_id):
                for ln in str(chunk).splitlines():
                    if ln.strip():
                        lines.append(ln)
    except Exception as e:
        return Trace(), f'chat_services 异常: {type(e).__name__}: {e}'
    if record_path:
        os.makedirs(os.path.dirname(record_path), exist_ok=True)
        with open(record_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
    return Trace.from_sse_lines(lines), None


def _apply_overrides(case: EvalCase, model_id: int | None, app_id: str | None) -> EvalCase:
    """CLI 覆盖 model_id/app_id(换模型跑同一套用例;app_id 用 sentinel '' 表示清空)。"""
    patch: dict = {}
    if model_id is not None:
        patch['model_id'] = model_id
    if app_id is not None:
        patch['app_id'] = app_id or None
    return replace(case, **patch) if patch else case


async def run_case_live(
    case: EvalCase,
    user_id: int = 1,
    record: bool = True,
    record_dir: str | None = None,
    model_id: int | None = None,
    app_id: str | None = None,
) -> CaseResult:
    case = _apply_overrides(case, model_id, app_id)
    cr = CaseResult(case_id=case.id, tags=case.tags, model_id=case.model_id)
    rdir = record_dir or FIXTURES_DIR
    for k in range(case.runs):
        rec = os.path.join(rdir, f'{case.id}.run{k + 1}.jsonl') if record else None
        trace, err = await _live_once(case, user_id, rec)
        cr.runs.append(_score(case, trace, err))
    return cr


# ---------------- 统一入口 ----------------

def run_all_replay(cases: list[EvalCase]) -> list[CaseResult]:
    return [run_case_replay(c) for c in cases]


async def run_all_live(
    cases: list[EvalCase],
    user_id: int = 1,
    record: bool = True,
    record_dir: str | None = None,
    model_id: int | None = None,
    app_id: str | None = None,
) -> list[CaseResult]:
    return [
        await run_case_live(c, user_id, record, record_dir, model_id, app_id)
        for c in cases
    ]
