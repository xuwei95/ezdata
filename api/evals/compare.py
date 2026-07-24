"""A/B 对比:并排多份 `run_evals --json` 结果,看强/弱模型(或 prompt 版本)通过率差。

  python -m evals.run_evals --mode live --model-id 3 --label opus --json runs/opus.json
  python -m evals.run_evals --mode live --model-id 7 --label qwen --json runs/qwen.json
  python -m evals.compare runs/opus.json runs/qwen.json [--out ab.md]

第一个文件当基线,末列给出「相对基线的变化」(↑改善 / ↓回归)。
"""

from __future__ import annotations

import argparse
import json
import sys


def _load(path: str) -> dict:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _rate(c: dict) -> float:
    return c['pass_runs'] / c['n'] if c.get('n') else 0.0


def build(files: list[dict]) -> str:
    labels = [f['label'] for f in files]
    idx = [{c['case_id']: c for c in f['cases']} for f in files]
    case_ids: list[str] = []
    for f in files:
        for c in f['cases']:
            if c['case_id'] not in case_ids:
                case_ids.append(c['case_id'])

    lines = ['# A/B 对比\n', '| 用例 | ' + ' | '.join(labels) + ' | Δ vs 基线 |',
             '|---|' + '|'.join(['---'] * len(labels)) + '|---|']
    for cid in case_ids:
        cells, base, last = [], None, None
        for i, mp in enumerate(idx):
            c = mp.get(cid)
            if c is None:
                cells.append('—')
                continue
            r = _rate(c)
            if i == 0:
                base = r
            last = r
            tc = c.get('avg_tool_calls')
            tc_s = f', ~{tc:g}工具' if tc is not None else ''
            cells.append(f'{c["pass_runs"]}/{c["n"]} ({r:.0%}{tc_s})')
        delta = ''
        if base is not None and last is not None and len(labels) >= 2:
            d = last - base
            delta = '＝' if abs(d) < 1e-9 else (f'↑ +{d:.0%}' if d > 0 else f'↓ {d:.0%}')
        lines.append(f'| `{cid}` | ' + ' | '.join(cells) + f' | {delta} |')

    # 整体
    overalls = []
    for f in files:
        tp = sum(c['pass_runs'] for c in f['cases'])
        tn = sum(c['n'] for c in f['cases'])
        overalls.append(tp / tn if tn else 0.0)
    lines.append('| **整体** | ' + ' | '.join(f'**{o:.0%}**' for o in overalls) + ' | |')

    # check 级回归(仅两份时,列出基线通过、对比掉下去的 check)
    if len(files) == 2:
        regressions = []
        for cid in case_ids:
            a, b = idx[0].get(cid), idx[1].get(cid)
            if not a or not b:
                continue
            for name, (ok, tot) in a.get('checks', {}).items():
                bo, bt = b.get('checks', {}).get(name, (0, 0))
                if tot and bt and (ok / tot) > (bo / bt):
                    regressions.append(f'- `{cid}` · **{name}**: {ok}/{tot} → {bo}/{bt}')
        if regressions:
            lines.append('\n## 相对基线掉下去的 check\n')
            lines.extend(regressions)
    return '\n'.join(lines) + '\n'


def main() -> int:
    ap = argparse.ArgumentParser(description='评测结果 A/B 对比')
    ap.add_argument('files', nargs='+', help='run_evals --json 产出的结果文件(第一个为基线)')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()
    if len(args.files) < 2:
        print('至少给两份结果文件', file=sys.stderr)
        return 2
    md = build([_load(p) for p in args.files])
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f'对比已写入 {args.out}')
    else:
        print(md)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
