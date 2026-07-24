"""ezdata Agent 离线评测/回归框架(P0+P1:确定性打分 + N 次重跑通过率)。

设计见 evals/README.md。核心:
- trace.py  : SSE 事件流 → 归一 Trace(打分器的唯一输入)
- cases.py  : YAML 用例集加载
- scorers.py: 确定性断言(工具跑通/用对源/非空/图表合法/未幻觉表/任务提议形状)
- runner.py : 跑 agent 收 trace(replay 回放 / live 实跑),N 次重跑
- report.py : 聚合通过率 → markdown 报告
"""
