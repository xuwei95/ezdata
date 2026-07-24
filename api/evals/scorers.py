"""确定性打分器(P1 主力):纯函数 (case, trace, params) -> CheckResult。

不依赖 LLM,零判官方差,可进 CI。LLM-as-judge 留待 P2。
每个 check 在用例 YAML 里形如 {type: <名>, <参数...>};按 type 路由到此处函数。
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# 明确的失败信号(工具结果/错误文本里出现即判失败)
_FAIL_SIGNALS = ('NameError', 'Traceback', '沙箱', '调用沙箱失败', '数据源解析失败', '查询被拦截', '查询失败')


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ''


def _args_blob(trace: Any) -> str:
    """所有工具入参拼成一个可搜索字符串(args 已截断,但 code/短值仍在)。"""
    return json.dumps([t.args for t in trace.tools], ensure_ascii=False, default=str)


def _max_rows(trace: Any) -> int:
    n = 0
    for a in trace.artifacts:
        total = a.get('total')
        if isinstance(total, int):
            n = max(n, total)
        elif isinstance(a.get('rows'), list):
            n = max(n, len(a['rows']))
    return n


# ---------------- 各 check ----------------

def check_tool_ran_ok(case, trace, p) -> CheckResult:
    if trace.error:
        return CheckResult('tool_ran_ok', False, f'流级错误: {trace.error[:120]}')
    bad = [t for t in trace.tools if t.status == 'error']
    if bad:
        return CheckResult('tool_ran_ok', False, f'工具失败: {bad[0].name} — {(bad[0].error or "")[:120]}')
    # 结果文本里的失败信号(有些工具吞异常后以文本返回)
    for t in trace.tools:
        txt = str(t.result or '')
        hit = next((s for s in _FAIL_SIGNALS if s in txt), None)
        if hit:
            return CheckResult('tool_ran_ok', False, f'{t.name} 结果含失败信号「{hit}」')
    if not trace.tools:
        return CheckResult('tool_ran_ok', False, '未产生任何工具调用')
    return CheckResult('tool_ran_ok', True, f'{len(trace.tools)} 个工具全部跑通')


def check_used_datasource(case, trace, p) -> CheckResult:
    code = p.get('code') or p.get('value')
    if not code:
        return CheckResult('used_datasource', False, '缺少参数 code')
    ok = code in _args_blob(trace)
    return CheckResult('used_datasource', ok, f'{"用到" if ok else "未用到"}数据源 {code}')


def check_result_nonempty(case, trace, p) -> CheckResult:
    need = int(p.get('min_rows', 1))
    got = _max_rows(trace)
    return CheckResult('result_nonempty', got >= need, f'最大产出行数 {got}(需 ≥{need})')


def check_chart(case, trace, p) -> CheckResult:
    charts = trace.charts()
    if not charts:
        return CheckResult('chart', False, '未产出图表 artifact')
    want_type = p.get('chart_type')  # 注:'type' 是 check 的分发键,图表目标类型用 chart_type
    need_rows = int(p.get('min_rows', 1))
    for a in charts:
        cfg = a.get('cfg') or {}
        rows = a.get('total') if isinstance(a.get('total'), int) else len(a.get('rows') or [])
        if want_type and cfg.get('type') and cfg['type'] != want_type:
            continue
        if rows < need_rows:
            continue
        if p.get('x_present') and not (cfg.get('x') or not cfg):  # 有 cfg 才校验 x
            continue
        if p.get('y_present') and cfg and not cfg.get('ys'):
            continue
        t = cfg.get('type') or 'chart(html)'
        return CheckResult('chart', True, f'图表 {t},{rows} 行')
    return CheckResult('chart', False, f'有图表但不满足(需 type={want_type} rows≥{need_rows})')


def check_no_hallucinated_table(case, trace, p) -> CheckResult:
    known = set(case.known_tables) | set(p.get('extra') or [])
    if not known:
        return CheckResult('no_hallucinated_table', True, '未提供 known_tables,跳过')
    referenced: list[str] = []
    for t in trace.tools:
        if t.name in ('get_table_schema',) and isinstance(t.args, dict):
            tbl = t.args.get('table') or t.args.get('table_name')
            if tbl:
                referenced.append(str(tbl))
    bad = [r for r in referenced if r not in known]
    if bad:
        return CheckResult('no_hallucinated_table', False, f'引用了未知表: {bad}')
    return CheckResult('no_hallucinated_table', True, f'引用表均在白名单({len(referenced)} 次)')


def check_task_proposal(case, trace, p) -> CheckResult:
    want = p.get('template_code')
    if not trace.ui_actions:
        return CheckResult('task_proposal', False, '未产出任务提议(ui_action)')
    if not want:
        return CheckResult('task_proposal', True, f'{len(trace.ui_actions)} 个任务提议')
    hit = any(a.get('template_code') == want or a.get('templateCode') == want for a in trace.ui_actions)
    return CheckResult('task_proposal', hit, f'{"命中" if hit else "未命中"}模板 {want}')


def check_produced(case, trace, p) -> CheckResult:
    """宽松判据:最终产出了 artifact 即算成功,忽略中途可恢复的工具报错。

    agentic 跑法常有"错几次再改对"的过程,tool_ran_ok(零错误)对这类偏严;
    要问"最终有没有出东西"用这个。kind: chart|table|(空=任意)。"""
    kind = p.get('kind')
    if kind == 'chart':
        arts = trace.charts()
    elif kind == 'table':
        arts = trace.tables()
    else:
        arts = trace.artifacts
    ok = len(arts) > 0
    return CheckResult('produced', ok, f'{"最终产出" if ok else "未产出"} {kind or ""}产物 {len(arts)} 个(忽略中途报错)')


def check_answer_contains(case, trace, p) -> CheckResult:
    subs = p.get('any') or ([p['value']] if p.get('value') else [])
    hit = any(s in trace.final_text for s in subs)
    return CheckResult('answer_contains', hit, f'答案{"含" if hit else "不含"}关键词 {subs}')


SCORERS: dict[str, Callable] = {
    'tool_ran_ok': check_tool_ran_ok,
    'used_datasource': check_used_datasource,
    'result_nonempty': check_result_nonempty,
    'chart': check_chart,
    'no_hallucinated_table': check_no_hallucinated_table,
    'task_proposal': check_task_proposal,
    'produced': check_produced,
    'answer_contains': check_answer_contains,
}


def score_trace(case, trace) -> list[CheckResult]:
    """按用例声明的 checks 逐条打分。支持简写 'tool_ran_ok'(等价 {type: tool_ran_ok})。"""
    out: list[CheckResult] = []
    for chk in case.checks:
        if isinstance(chk, str):
            chk = {'type': chk}
        typ = chk.get('type')
        fn = SCORERS.get(typ)
        if fn is None:
            out.append(CheckResult(typ or '?', False, f'未知 check 类型: {typ}'))
            continue
        try:
            out.append(fn(case, trace, chk))
        except Exception as e:  # 打分器自身异常不该炸掉整轮
            out.append(CheckResult(typ, False, f'打分器异常: {type(e).__name__}: {e}'))
    return out
