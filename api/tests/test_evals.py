"""评测框架单测:SSE→Trace 解析、确定性打分器、通过率聚合。全部离线可跑。"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from evals.cases import EvalCase, load_cases
from evals.report import CaseResult, RunResult, build_report
from evals.runner import run_all_replay
from evals.scorers import score_trace
from evals.trace import Trace


def _lines(*events):
    return [json.dumps(e, ensure_ascii=False) for e in events]


# ---------------- Trace 解析 ----------------

def test_trace_parses_tools_artifacts_content():
    tr = Trace.from_sse_lines(_lines(
        {"session_id": "s", "type": "meta"},
        {"type": "tool", "phase": "start", "id": "t1", "name": "plot_chart", "args": {"datasource_code": "demo_es"}},
        {"type": "tool", "phase": "end", "id": "t1", "name": "plot_chart", "result": "已生成图表(line)"},
        {"type": "artifact", "artifact": {"kind": "echart", "cfg": {"type": "line", "x": "date", "ys": [{"field": "v"}]}, "total": 30}},
        {"type": "content", "content": "结论。"},
    ))
    assert tr.session_id == "s"
    assert len(tr.tools) == 1 and tr.tools[0].ok
    assert tr.charts() and tr.charts()[0]["total"] == 30
    assert tr.final_text == "结论。"


def test_trace_tool_error_status():
    tr = Trace.from_sse_lines(_lines(
        {"type": "tool", "phase": "start", "id": "t1", "name": "run_datasource_query", "args": {}},
        {"type": "tool", "phase": "error", "id": "t1", "name": "run_datasource_query", "error": "NameError: x"},
    ))
    assert tr.has_tool_error()


# ---------------- 打分器 ----------------

def _case(checks, **kw):
    return EvalCase(id="c", question="q", checks=checks, **kw)


def test_tool_ran_ok_detects_nameerror_in_result_text():
    tr = Trace.from_sse_lines(_lines(
        {"type": "tool", "phase": "start", "id": "t1", "name": "run_datasource_query", "args": {}},
        {"type": "tool", "phase": "end", "id": "t1", "name": "run_datasource_query", "result": "NameError: name 'df'"},
    ))
    [res] = score_trace(_case(["tool_ran_ok"]), tr)
    assert not res.passed


def test_used_datasource_and_result_nonempty():
    tr = Trace.from_sse_lines(_lines(
        {"type": "tool", "phase": "start", "id": "t1", "name": "run_datasource_query", "args": {"datasource_code": "demo_es"}},
        {"type": "tool", "phase": "end", "id": "t1", "name": "run_datasource_query", "result": "ok"},
        {"type": "artifact", "artifact": {"kind": "table", "total": 12}},
    ))
    results = score_trace(_case([
        {"type": "used_datasource", "code": "demo_es"},
        {"type": "result_nonempty", "min_rows": 10},
    ]), tr)
    assert all(r.passed for r in results)
    # 未用到的源应判失败
    [miss] = score_trace(_case([{"type": "used_datasource", "code": "prod_mysql"}]), tr)
    assert not miss.passed


def test_chart_type_and_min_rows():
    tr = Trace.from_sse_lines(_lines(
        {"type": "artifact", "artifact": {"kind": "echart", "cfg": {"type": "line", "x": "d", "ys": [{"field": "v"}]}, "total": 30}},
    ))
    [ok] = score_trace(_case([{"type": "chart", "chart_type": "line", "min_rows": 20}]), tr)
    assert ok.passed
    [wrong] = score_trace(_case([{"type": "chart", "chart_type": "bar"}]), tr)
    assert not wrong.passed


def test_no_hallucinated_table():
    tr = Trace.from_sse_lines(_lines(
        {"type": "tool", "phase": "start", "id": "t1", "name": "get_table_schema", "args": {"table": "ghost_table"}},
        {"type": "tool", "phase": "end", "id": "t1", "name": "get_table_schema", "result": "ok"},
    ))
    [res] = score_trace(_case(["no_hallucinated_table"], known_tables=["div_bond10y"]), tr)
    assert not res.passed


def test_task_proposal():
    tr = Trace.from_sse_lines(_lines(
        {"type": "ui_action", "action": {"kind": "task_proposal", "template_code": "data_integration"}},
    ))
    [res] = score_trace(_case([{"type": "task_proposal", "template_code": "data_integration"}]), tr)
    assert res.passed


# ---------------- 聚合 ----------------

def test_case_result_pass_rate():
    from evals.scorers import CheckResult
    cr = CaseResult(case_id="c", tags=["x"], model_id=0, runs=[
        RunResult([CheckResult("a", True), CheckResult("b", True)]),
        RunResult([CheckResult("a", True), CheckResult("b", False)]),
        RunResult([CheckResult("a", True), CheckResult("b", True)]),
    ])
    assert cr.pass_runs == 2 and abs(cr.pass_rate - 2 / 3) < 1e-6
    assert cr.check_pass_rate()["b"] == (2, 3)
    assert cr.worst_checks() == ["b"]


# ---------------- 用例 + 回放端到端 ----------------

def test_cases_load_and_replay_end_to_end():
    cases = load_cases()
    assert cases, "应能加载 finance.yaml 用例"
    results = run_all_replay(cases)
    by_id = {r.case_id: r for r in results}
    # 弱模型不稳的标志用例:3 次里 1 次 NameError → 2/3
    assert by_id["div_bond10y_trend"].pass_runs == 2
    assert by_id["div_bond10y_trend"].n == 3
    # 只出表不出图的那次,chart 断言应挂
    assert by_id["stock_topn_amount"].pass_runs == 1
    md = build_report(results)
    assert "整体通过率" in md and "div_bond10y_trend" in md
