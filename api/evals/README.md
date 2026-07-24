# Agent 评测/回归框架(P0+P1)

给数据分析 Agent 用的**离线回归**:改 prompt / 换模型 / 调工具后,跑一遍看**通过率**红绿,替代人肉试。

核心判断:数据 Agent 的"对不对"大多**可程序化判定**(工具跑没跑通、返回几行、图表 cfg 合不合法、用没用对源、有没有幻觉表),所以主力是**确定性断言**;LLM-as-judge(P2)只兜最后那层答案质量。"弱模型不稳"是随机问题 → 同一用例**跑 N 次报通过率**,而非单次红绿。

## 目录

| 文件 | 作用 |
|---|---|
| `trace.py` | SSE 事件流 → 归一 `Trace`(打分器唯一输入) |
| `cases.py` | YAML 用例集加载(`cases/*.yaml`) |
| `scorers.py` | 确定性打分器(纯函数,零判官方差) |
| `runner.py` | 跑 agent 收 trace:`replay`(回放)/ `live`(实跑) |
| `report.py` | 聚合通过率 → markdown;`build_compare` 做 A/B |
| `run_evals.py` | CLI |
| `cases/` | 用例(YAML) |
| `fixtures/` | 录制的 SSE(`<id>.run<k>.jsonl`),replay 用 |

## 跑

```bash
# 回放(任何机器 / CI;不需要后端环境)
python -m evals.run_evals --mode replay --out report.md

# 实跑(需 DB/ES/模型/沙箱环境),并把每轮 SSE 录到 fixtures/ 供以后回放
python -m evals.run_evals --mode live --user-id 1

# CI gate:整体通过率 < 阈值则退出码 1
python -m evals.run_evals --mode replay --min-pass 0.9
```

单测(纯离线):`pytest tests/test_evals.py`

## 换个(弱)模型跑同一套用例 + A/B

模型由 `model_id` 决定:`0`=环境兜底模型(`LLM_*` env);`>0`=「AI 模型管理」里配好的 `ai_model` 表行 id。
**前提**:先把要测的弱模型在平台「AI 模型管理」配好(provider/api_key/base_url),拿到它的 id;或把 `LLM_*` env 指向它、用 `model_id=0`。

不用改 YAML,用 CLI 覆盖所有用例的模型:

```bash
# 强模型基线
python -m evals.run_evals --mode live --model-id 3 --label opus --json runs/opus.json
# 换弱模型跑同一套(录制单独进 fixtures/qwen-turbo/,不覆盖基线)
python -m evals.run_evals --mode live --model-id 7 --label qwen-turbo --json runs/qwen.json
# 并排对比(第一个当基线,标 ↑改善 / ↓回归,并列出掉下去的 check)
python -m evals.compare runs/opus.json runs/qwen.json --out ab.md
```

- `--model-id N` 覆盖所有用例;`--label` 用于区分并给 live 录制分目录(`fixtures/<label>/`),强弱模型 A/B 不互相覆盖。
- 弱模型不稳是随机的 → 用例里把 `runs` 调大(如 5~10)再看通过率更可信。
- 只想单看某弱模型:`--mode live --model-id 7 --label qwen`(不需要 `--json`/compare)。
- `--app-id` 可覆盖应用(带其工具/数据源范围);空串清空。

## 加用例

在 `cases/*.yaml` 加一条:

```yaml
- id: my_case
  question: 用户问题(原样喂给 agent)
  model_id: 0            # 0=环境兜底模型;>0=指定模型(A/B)
  app_id: null           # 指定应用则带其工具/数据源范围
  runs: 3                # 重跑次数 → 通过率
  tags: [取数, 出图]
  known_tables: [t1, t2] # no_hallucinated_table 用
  checks:
    - tool_ran_ok                              # 工具全跑通(无 NameError/沙箱失败)
    - {type: used_datasource, code: demo_es}   # 用到指定源
    - {type: result_nonempty, min_rows: 20}    # 产出行数 ≥
    - {type: chart, chart_type: line, min_rows: 20}  # 出图且类型/行数达标
    - no_hallucinated_table                    # 未引用 known_tables 外的表
    - {type: task_proposal, template_code: data_integration}  # 提议指定任务
    - {type: answer_contains, any: [下行, 上行]}  # 答案含关键词(轻量兜底)
```

`replay` 模式下每个 `<id>.run<k>.jsonl` 算一次运行;`live` 模式实跑 `runs` 次并自动录制。

## check 一览(确定性)

| check | 参数 | 判定 |
|---|---|---|
| `tool_ran_ok` | — | 无工具 error / 流级错误 / 结果含 NameError·沙箱失败等信号 |
| `used_datasource` | `code` | 某工具入参含该数据源 code |
| `result_nonempty` | `min_rows` | 最大产出行数 ≥ |
| `chart` | `chart_type` `min_rows` `x_present` `y_present` | 有图表 artifact 且达标 |
| `no_hallucinated_table` | `extra` | get_table_schema 引用的表 ⊆ known_tables |
| `task_proposal` | `template_code` | 产出 ui_action 任务提议(可指定模板) |
| `answer_contains` | `any` / `value` | 最终答案含关键词 |

## 路线

- **P0/P1(本目录)**:用例集 + 确定性打分 + N 次通过率 + markdown 报告 + CI gate。✅
- **P2**:LLM-as-judge(pairwise A/B,`build_compare` 已备聚合)+ rubric 用例(答案质量/幻觉)。
- **P3**:从 `ai_sessions` 挖真实会话扩充用例(⭐收藏=正例,失败会话=回归守卫);回读 session 补全 code 全文做 `value_match` 对真值。

## 与主服务的边界

只读地复用 `AiChatService.chat_services`(live)、`config.database.AsyncSessionLocal`。不改主服务代码;`live` 的重依赖都在 `runner._live_once` 内延迟 import,故 `replay`/单测在无后端环境下也能跑。
