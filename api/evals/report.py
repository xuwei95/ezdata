"""聚合打分结果 → markdown 报告。

关注两个维度:
- 用例级稳定性 = N 次重跑里「全部 check 通过」的比例(弱模型不稳的核心指标);
- check 级通过率 = 每个断言在 N 次里的通过比例(定位到底哪步不稳)。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from evals.scorers import CheckResult


@dataclass
class RunResult:
    checks: list[CheckResult]
    error: str | None = None  # 该次运行本身失败(runner 层)
    tool_calls: int = 0       # 该次运行的工具调用数(看弱模型循环有没有被压住)

    @property
    def all_passed(self) -> bool:
        return not self.error and bool(self.checks) and all(c.passed for c in self.checks)


@dataclass
class CaseResult:
    case_id: str
    tags: list[str]
    model_id: int
    runs: list[RunResult] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.runs)

    @property
    def pass_runs(self) -> int:
        return sum(1 for r in self.runs if r.all_passed)

    @property
    def pass_rate(self) -> float:
        return self.pass_runs / self.n if self.n else 0.0

    @property
    def avg_tool_calls(self) -> float:
        return sum(r.tool_calls for r in self.runs) / self.n if self.n else 0.0

    def check_pass_rate(self) -> dict[str, tuple[int, int]]:
        """check 名 -> (通过次数, 总次数)。"""
        agg: dict[str, list[int]] = {}
        for r in self.runs:
            for c in r.checks:
                a = agg.setdefault(c.name, [0, 0])
                a[0] += int(c.passed)
                a[1] += 1
        return {k: (v[0], v[1]) for k, v in agg.items()}

    def worst_checks(self) -> list[str]:
        return [k for k, (ok, tot) in self.check_pass_rate().items() if ok < tot]


def _bar(rate: float) -> str:
    filled = round(rate * 10)
    return '█' * filled + '░' * (10 - filled)


def build_report(results: list[CaseResult], config_label: str = 'default') -> str:
    n_cases = len(results)
    total_runs = sum(r.n for r in results)
    total_pass = sum(r.pass_runs for r in results)
    overall = total_pass / total_runs if total_runs else 0.0

    lines: list[str] = []
    lines.append(f'# Agent 评测报告 — `{config_label}`\n')
    lines.append(f'- 用例数: **{n_cases}**　总跑数: **{total_runs}**　'
                 f'整体通过率: **{overall:.0%}** {_bar(overall)}\n')

    # 用例明细
    lines.append('## 用例明细(稳定性 = 全 check 通过率)\n')
    lines.append('| 用例 | 标签 | 模型 | 通过率 | | 平均工具调用 | 不稳的 check |')
    lines.append('|---|---|---|---|---|---|---|')
    for r in sorted(results, key=lambda x: x.pass_rate):
        worst = ', '.join(r.worst_checks()) or '—'
        lines.append(f'| `{r.case_id}` | {",".join(r.tags) or "—"} | {r.model_id} | '
                     f'{r.pass_runs}/{r.n} ({r.pass_rate:.0%}) | {_bar(r.pass_rate)} | '
                     f'{r.avg_tool_calls:.1f} | {worst} |')
    lines.append('')

    # check 级明细
    lines.append('## check 级通过率\n')
    lines.append('| 用例 | check | 通过 |')
    lines.append('|---|---|---|')
    for r in results:
        for name, (ok, tot) in r.check_pass_rate().items():
            flag = '' if ok == tot else ' ⚠️'
            lines.append(f'| `{r.case_id}` | {name} | {ok}/{tot}{flag} |')
    lines.append('')

    # 按标签
    by_tag: dict[str, list[float]] = {}
    for r in results:
        for tag in (r.tags or ['(untagged)']):
            by_tag.setdefault(tag, []).append(r.pass_rate)
    lines.append('## 按标签\n')
    lines.append('| 标签 | 用例数 | 平均通过率 |')
    lines.append('|---|---|---|')
    for tag, rates in sorted(by_tag.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
        avg = sum(rates) / len(rates)
        lines.append(f'| {tag} | {len(rates)} | {avg:.0%} {_bar(avg)} |')
    lines.append('')

    # 失败详情(便于定位)
    fails = [(r, i, run) for r in results for i, run in enumerate(r.runs) if not run.all_passed]
    if fails:
        lines.append('## 失败详情\n')
        for r, i, run in fails:
            head = f'- `{r.case_id}` 第 {i + 1} 次'
            if run.error:
                lines.append(f'{head}: 运行失败 — {run.error[:160]}')
                continue
            failed = [c for c in run.checks if not c.passed]
            for c in failed:
                lines.append(f'{head} · **{c.name}** ✗ — {c.detail}')
        lines.append('')

    return '\n'.join(lines)


def build_compare(results_by_config: dict[str, list[CaseResult]]) -> str:
    """A/B:多配置(模型/prompt 版本)并排比较用例通过率。"""
    configs = list(results_by_config)
    case_ids: list[str] = []
    for rs in results_by_config.values():
        for r in rs:
            if r.case_id not in case_ids:
                case_ids.append(r.case_id)
    idx = {cfg: {r.case_id: r for r in rs} for cfg, rs in results_by_config.items()}

    lines = ['# A/B 对比\n', '| 用例 | ' + ' | '.join(configs) + ' |',
             '|---|' + '|'.join(['---'] * len(configs)) + '|']
    for cid in case_ids:
        cells = []
        for cfg in configs:
            r = idx[cfg].get(cid)
            cells.append(f'{r.pass_rate:.0%}' if r else '—')
        lines.append(f'| `{cid}` | ' + ' | '.join(cells) + ' |')
    lines.append('')
    # 整体
    lines.append('| 整体通过率 | ' + ' | '.join(
        f'{sum(r.pass_runs for r in rs) / max(1, sum(r.n for r in rs)):.0%}'
        for rs in results_by_config.values()
    ) + ' |')
    return '\n'.join(lines)
