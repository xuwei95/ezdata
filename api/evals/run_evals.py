"""评测 CLI。

  python -m evals.run_evals --mode replay                          # 回放录制(任何机器,CI 用)
  python -m evals.run_evals --mode live --user-id 1                # 实跑(需后端环境),录制到 fixtures/live/
  # 换弱模型跑同一套用例(不改 YAML),打标签区分并存结果供 A/B:
  python -m evals.run_evals --mode live --model-id 7 --label qwen-turbo --json runs/qwen.json
  python -m evals.run_evals --mode live --model-id 3 --label opus      --json runs/opus.json
  python -m evals.compare runs/opus.json runs/qwen.json               # 强弱对比

退出码:整体通过率低于 --min-pass(默认 0,不 gate)时返回 1,便于 CI 卡回归。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evals.cases import load_cases
from evals.report import build_report
from evals.runner import FIXTURES_DIR, run_all_live, run_all_replay


def main() -> int:
    ap = argparse.ArgumentParser(description='ezdata Agent 评测/回归')
    ap.add_argument('--mode', choices=['replay', 'live'], default='replay')
    ap.add_argument('--cases', default=None, help='用例文件(默认扫 evals/cases/*.yaml)')
    ap.add_argument('--out', default=None, help='markdown 报告输出路径(默认打印到 stdout)')
    ap.add_argument('--label', default=None, help='配置标签(A/B 时区分,如 opus / qwen / prompt-v2)')
    ap.add_argument('--model-id', type=int, default=None,
                    help='覆盖所有用例的模型(0=环境兜底模型;>0=ai_model 表里的模型 id)。换弱模型跑就用它')
    ap.add_argument('--app-id', default=None, help='覆盖所有用例的应用 id(空串=清空)')
    ap.add_argument('--user-id', type=int, default=1, help='live 模式的用户 id')
    ap.add_argument('--no-record', action='store_true', help='live 模式不录制 fixtures')
    ap.add_argument('--json', dest='json_out', default=None, help='把结果摘要存 json(供 evals.compare 做 A/B)')
    ap.add_argument('--min-pass', type=float, default=0.0, help='整体通过率低于此值退出码 1(CI gate)')
    args = ap.parse_args()

    cases = load_cases(args.cases)
    if not cases:
        print('没有加载到用例', file=sys.stderr)
        return 2

    if args.mode == 'live':
        label = args.label or (f'model-{args.model_id}' if args.model_id is not None else 'live')
        # 录制按标签分目录,避免强/弱模型 A/B 时互相覆盖
        record_dir = os.path.join(FIXTURES_DIR, label)
        results = asyncio.run(run_all_live(
            cases, user_id=args.user_id, record=not args.no_record,
            record_dir=record_dir, model_id=args.model_id, app_id=args.app_id,
        ))
    else:
        results = run_all_replay(cases)
        label = args.label or 'replay'

    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        payload = {'label': label, 'cases': [
            {'case_id': r.case_id, 'tags': r.tags, 'model_id': r.model_id,
             'pass_runs': r.pass_runs, 'n': r.n, 'avg_tool_calls': round(r.avg_tool_calls, 2),
             'checks': {k: list(v) for k, v in r.check_pass_rate().items()}}
            for r in results
        ]}
        with open(args.json_out, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f'结果摘要已写入 {args.json_out}')

    md = build_report(results, config_label=label)
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f'报告已写入 {args.out}')
    else:
        print(md)

    total_runs = sum(r.n for r in results)
    total_pass = sum(r.pass_runs for r in results)
    overall = total_pass / total_runs if total_runs else 0.0
    if overall < args.min_pass:
        print(f'::gate:: 整体通过率 {overall:.0%} < 阈值 {args.min_pass:.0%}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
