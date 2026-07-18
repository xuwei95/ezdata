# 设计文档:语义/指标层(Metric Layer)—— 权威口径,置于数据模型之上

> 状态:草案 / 待评审
> 范围:`module_data`(指标定义、编译执行)、`module_ai`(agent 工具 + 漏斗指令)、前端(指标管理页)
> 参考:Anthropic《self-service data analytics》(语义层信任度最高、定义须人拍板、漏斗式);WrenAI MDL、Snowflake Cortex Semantic View(实测语义模型 +20% 准确率)、Cube/dbt 指标层。

---

## 1. Context

调研结论:市场高准确率玩家(WrenAI 90%+、Snowflake Cortex 90%+)都以**语义/指标层**为核心——把「活跃用户」「营收」这类指标的**口径一次性定义好**,LLM 基于它取数,而不是每次从原始表猜。ezdata 目前从 `data_model`(dm_*)/原始表直接取,遇到口径类问题(什么算"活跃"?算不算欺诈用户?回溯窗口多长?)只能靠 remark 文字兜,是与第一梯队最实的差距。

本设计在 ezdata 既有体系上补这一层,且遵守两条硬约束:
- **定义由人拍板**(文章/WrenAI/Snowflake 都踩过坑:LLM 自动生成指标定义会把要消除的模糊又编码进去)。
- **兼容 ezdata 的跨源 + 代码优先**:不像 Cortex/Genie 只吃仓内 SQL,指标要能定义在 SQL / ES / akshare 等**任意已建模的数据源**上(这是 ezdata 的护城河,不能丢)。

## 2. Goals / Non-goals

**Goals**
1. 新增**指标(metric)** 概念:权威口径 + 可执行定义,绑定到已有 `data_model`。
2. agent 取数**漏斗新增最顶层**:先查指标层命中即用 → 再 KB 解法 → 再原始表(对齐 Anthropic 顺序、WrenAI/Cortex"优先语义层")。
3. 跨源可执行:SQL / ES 结构化编译;其余源代码模板兜底。
4. 人工定义 + 可选 AI 起草(草稿必须人确认)。

**Non-goals(本期不做)**
- 跨模型自动 join / 完整血缘图(需先有血缘,列入 Phase 3)。
- 复杂派生指标(同比/环比/比率的通用引擎)先只做单度量 + 简单比率。
- 取代 Skill:指标层是「**what**——权威数字」,Skill 是「**how**——操作手册」,二者正交(见 §7)。

## 3. 设计原则
- **一个概念一个权威答案**:code 唯一 + 同义词,防同名多义。
- **漏斗**:指标层(信任最高、最省)→ 知识型 Skill/KB 解法 → 原始表自由取数。
- **人定义、AI 起草**:LLM 只能产草稿,发布须人确认。
- **建在 data_model 之上**:复用已有的源/表/字段元数据,不重造。

## 4. 数据模型:新增 `data_metric`(module_data)

| 列 | 类型 | 说明 |
|---|---|---|
| metric_id | bigint PK | |
| name | varchar(100) | 指标名(如「主力净流入」) |
| code | varchar(100) uniq | 唯一标识(供 query_metric 引用) |
| synonyms | varchar(500) | 同义词(逗号分隔,提升命中,如「主力资金/大单净额」) |
| caliber | text | **口径定义(权威、人写)**:什么算、含不含、窗口多长 |
| model_id | bigint | 绑定的 data_model(带出 datasource_code/object_name/字段) |
| measure | text(JSON) | 度量:`{agg: sum/count/avg/max/min/count_distinct/ratio/expr, field, expr?}` |
| dimensions | text(JSON) | 允许的分组维度 `[{field,name}]` |
| time_field | varchar(100) | 时间字段(可空) |
| default_grain | varchar(20) | 默认时间粒度 day/week/month |
| default_filters | text(JSON) | 固定口径过滤(如排除测试/欺诈) |
| unit / format | varchar(50) | 单位/小数/百分比(亿、%、2位) |
| verified_examples | text(JSON) | 人工审定示例 `[{question, expect}]`(对应 Cortex VQR) |
| status | char(1) | 0启用 1停用 |
| review_state | varchar(20) | ok / stale(模型 schema 变更后标待复核) |
| built_in / user_id / dept_id / audit / tenant_id | | 与 ai_skill 一致 |

> 维度暂内联在 metric;若后续多指标共享维度再抽 `data_dimension` 表(Phase 2)。

## 5. 编译与执行(跨源关键)

`MetricService.compile(metric, group_by, filters, time_range, top_n)` → 按绑定模型的**源类型**产出执行计划,复用现有 handler(`run_datasource_query` 那条链路),**不新建执行引擎**:

- **SQL 源**:拼 `SELECT {dims}, {agg}({field}) AS value FROM {table} WHERE {default_filters ∧ user_filters ∧ time} GROUP BY {dims} ORDER BY value DESC [LIMIT top_n]`。
- **ES 源**:拼 aggregation body(维度 terms 用 `.keyword`、时间 date_histogram、度量 metric agg;`size:0`)——复用 `es_query` skill 里已固化的坑规则。
- **其余源(akshare/mongo…)**:metric 可存**参数化代码模板**(占位 `{dims}/{filters}/{time}`),编译即填充后交 handler 执行(Phase 2)。

产出统一为 `[{dim..., value}]`,再交 `plot_chart`/文本作答。

## 6. Agent 集成:漏斗新增最顶层

**两个新工具(module_ai/tools,薄封装 MetricService):**
- `list_metrics(keyword='')` → 命中的指标目录(code/name/caliber/可用维度)。
- `query_metric(metric_code, group_by=[], filters={}, time_range=None, top_n=None)` → 编译执行,返回权威数字。

**注入 & 指令(改 `_DATA_AGENT_INSTRUCTIONS`,放进漏斗第 0 步):**
- 会话装配时注入**精简指标目录**(类似 `build_data_catalog`,只列 code+name+一句口径)。
- 规则:「问题若能映射到已定义指标 → **必须先用 `query_metric`**,别自己写 SQL/agg;拿不准先 `list_metrics`。命中不了才进 KB 解法 / 原始表。」——对齐 WrenAI/Cortex「强制优先语义层」。

**漏斗最终形态:**
```
0. 指标层命中? → query_metric(权威、一致、最省)   ← 新增
1. 认源(数据目录/ list_datasources)
2. KB 验证解法(search_datasource_knowledge)
3. 原始表自由取数(get_table_schema → run_datasource_query)
```

## 7. 与 Skill 体系的关系(正交,互补)
- **指标层 = what**(权威数字定义);**Skill = how**(流程/知识操作手册)。
- 知识型 Skill 可**引用指标**:如某源的 `<source>_guide` 里写「查估值优先用 `industry_pe_avg` 指标」。
- 复用刚落地的机制:指标像知识型 Skill 一样**绑定数据源**,可在 `search_datasource_knowledge` 认源时一并浮现「本源有指标:X」。

## 8. 授权/编写(人定义、AI 起草)
- **前端「指标管理」页**(数据管理下,镜像 ai/skill 页):CRUD + 口径/度量/维度/过滤/示例编辑;绑定 data_model 时自动带出字段候选。
- **「AI 起草候选」**:按钮让 LLM 读模型 schema + 样本数据,产出**指标草稿**(measure/dims/caliber 建议)→ **人审核确认才发布**(绝不自动上线)。
- verified_examples:填「示例问题→期望结果」,既做文档也做评测种子。

## 9. 治理 / 防过期(承接 Anthropic 与 Skill 设计)
- 指标绑 `model_id`;模型 schema 变更(字段消失/改名)→ 触发相关指标 `review_state=stale`,列表标「待复核」。
- 全量改动审计;code 唯一 + 同义词避免"一个概念多个数"。
- 与 Skill 一致:后续把指标纳入 seed / 版本,改口径的 PR 同步。

## 10. 差异化(相对市场,别丢)
- **跨源**:指标可建在 ES / akshare 模型上,不像 Cortex/Genie 仅仓内 SQL(Snowflake 自己都为此搞 OSI 跨平台倡议)。
- **代码优先兜底**:结构化源走编译,非结构化源走代码模板,始终能落地。
- **到图/看板闭环**:query_metric 结果直接 `plot_chart`→存看板。

## 11. 分阶段

**Phase 1(闭环最小可用)**
- `data_metric` 表(DO/VO/DAO;SQL×2;运行库 ALTER)。
- `MetricService`:SQL + ES 编译执行。
- `list_metrics` / `query_metric` 工具 + 注入精简指标目录 + 漏斗第 0 步指令。
- 前端指标管理页(CRUD,不含 AI 起草)。
- 种 2~3 个 demo 指标(demo_es 上:如「行业平均市盈率 industry_pe_avg」「大盘主力净流入 market_main_net」「指数收盘 index_close」)。

**Phase 2**
- AI 起草候选 + verified_examples;非结构化源代码模板;`review_state` 待复核联动;知识型 Skill 引用指标浮现。

**Phase 3**
- 维度复用表 + 跨模型 join(需血缘);同比/环比/比率派生指标引擎。

## 12. 验证
1. 编译正确性:SQL/ES 各造 1 指标,`query_metric` 结果与手写查询一致。
2. 漏斗:问「本季度各行业平均市盈率」→ agent 调 `query_metric('industry_pe_avg', group_by=['industry'])` 而非自写 SQL;命中不到的问题才回退原始表。
3. 一致性:同一指标不同问法/不同轮次结果一致。
4. 治理:改绑定模型字段 → 指标标 stale。
5. 前端:建/改指标(绑模型带出字段)、停用、示例编辑;浏览器验证。
6. e2e(兜底模型):端到端一问到底,对比"有指标层 vs 关掉指标层"的取数正确率与轮数。

## 13. 风险
| 风险 | 缓解 |
|---|---|
| 编译器覆盖不全(复杂聚合/多表) | Phase 1 只做单模型单度量 + 简单过滤/维度/时间;复杂的回退 KB 解法/原始表,不硬编译 |
| 指标定义错(口径写错比没有更危险) | 人拍板 + verified_examples 兜底 + review 审计;AI 只起草 |
| 与 Skill/KB 职责混淆 | 明确 what/how 分工(§7);指标只管权威数字,流程仍归 Skill |
| 跨源编译差异 | 结构化(SQL/ES)编译 + 其余代码模板;统一产出 `[{dim,value}]` |
