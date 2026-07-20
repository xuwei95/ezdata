# 设计文档:指标层(P1)+ 任务级血缘(P2)—— 可执行方案

> 状态:P1a 指标层 + P1b 下推 + P2a 血缘图 **已落地**;P1b「AI 起草候选」待做(见 §3)。
> 范围:`module_data`(指标定义/编译执行、血缘)、`module_ai`(agent 工具 + 漏斗)、前端(指标管理页 + 血缘图)
> 取代:`semantic-metric-layer-design.md`(规划稿)
> 调研依据:语义层——dbt MetricFlow(YAML 同 repo、仓库执行,2025-10 开源)/ Cube(独立服务 + Agentic 受治理上下文,LLM 准确率 ×3–5)/ Snowflake Semantic Views(+~20%);血缘——sqlglot 静态列级 / DataHub schema-aware(97–99%)/ OpenLineage 运行时。

---

## 1. Context / 目标

- **为什么**:ezdata 当前无语义层,口径类问题("活跃/营收/市盈率均值")只能靠 remark 兜 → 准确率天花板(市场公认语义层是最大杠杆)。同时 ezdata 的 ETL 任务**参数里已声明 extract→load**,任务级血缘"几乎白送"。
- **P1 指标层**:指标定义一次(度量+维度+口径),agent 按指标名 `query_metric` 取权威一致的数;定义人拍板。
- **P2 任务级血缘**:从任务参数 + 模型/指标/看板/技能的绑定关系,构建"源→模型→指标/看板/技能"血缘图;支撑**影响分析 / 防过期**。
- **融合**:补齐 agent 漏斗最顶两层 —— 指标(最信)→ 血缘(未定义指标时定位受治理模型)→ 检索(已做)→ 原始表。

**非目标**:不引 dbt(仓内)/Cube(重);不上 DataHub/OpenMetadata;列级血缘(sqlglot)与 OpenLineage 运行时留 P3。

## 2. 原则
- **定义人拍板**:LLM 只起草文档/候选,指标定义必须人确认(dbt/WrenAI/Snowflake 都踩过 LLM 自动生成把模糊编码进去的坑)。
- **建在 `data_model` 之上**:复用源/表/字段元数据 + handler 执行,不重造。
- **血缘靠"声明"而非"解析"**:任务参数已含 extract→load,零解析即得任务级血缘。

---

# Part 1 — 指标层(P1)

## 1.1 数据模型:`data_metric`(新表,module_data)

| 列 | 类型 | 说明 |
|---|---|---|
| metric_id | bigint PK auto | |
| name | varchar(100) not null | 指标名(「行业平均市盈率」) |
| code | varchar(100) uniq not null | 唯一标识,供 query_metric 引用 |
| synonyms | varchar(500) | 同义词(逗号分隔,提升命中) |
| caliber | text | **口径(权威、人写)**:算什么、含不含、窗口 |
| model_id | varchar(64) | 绑定 data_model.id(带出 datasource_code/object_name/字段) |
| measure | text(JSON) | `{"agg":"sum|avg|count|max|min|count_distinct|ratio|expr","field":"","expr":""}` |
| dimensions | text(JSON) | 允许分组维度 `[{"field":"","name":""}]` |
| time_field | varchar(100) | 时间字段(可空) |
| default_grain | varchar(20) | day/week/month |
| default_filters | text(JSON) | 固定口径过滤(排除测试/异常) |
| unit / fmt | varchar(50) | 单位(亿/%)、小数位 |
| verified_examples | text(JSON) | 人工审定 `[{"question":"","expect":""}]`(≈ Cortex VQR,兼做评测种子) |
| status | char(1) '0' | 0启用 1停用 |
| review_state | varchar(20) 'ok' | ok / stale(P2 血缘触发) |
| built_in / user_id / dept_id / create_* / update_* / remark / tenant_id | | 与 ai_skill 一致 |

DDL 入 `api/sql/ezdata.sql` + `ezdata-pg.sql`;`DataMetric(Base, TenantMixin)`,菜单/权限 `data:metric:*`。

## 1.2 编译执行:`MetricService`(module_data/service)—— 下推优先 + pandas 兜底

**执行策略(`_execute`,P1b 已实现)**:指标查询默认**下推**到库内聚合(结果集小、可扛大表);源不支持下推 / 抛 `AggNotSupported` / 下推异常时,**回退**到"拉数(≤ `_FETCH_CAP` 行)+ pandas 聚合"(`_aggregate`)。两路共用 `_shape`/`_round_rows` 规整,**口径一致**(对拍测试保证,见 §4)——所以下推**永不比现状差**,可逐源/逐指标灰度。

**聚合 IR `AggSpec`**(`ezdata/handlers/agg_spec.py`,源无关):把指标定义规整成
`{table, measure{agg,field}, group_by, filters, time_field, time_range, grain, top_n}`,handler 不需懂指标定义;`validate()` 拦非法/不可下推形态 → 抛 `AggNotSupported` 交兜底。`default_filters`/默认维度的解析在 `MetricService` 侧完成,AggSpec 只承载"最终要算什么"。

**能力位驱动**:新增 `Capability.AGGREGATE`;`_execute` 判 `handler.has(AGGREGATE)` 才下推。各源族实现 `handler.aggregate(spec) -> [{dim..., value}]`:

- **SQL 族**(`sql_base`):用 **SQLAlchemy Core** 构造 `SELECT {dims}, {agg}({field}) AS value FROM {table} WHERE {default∧user∧time} GROUP BY {dims} ORDER BY value DESC [LIMIT top_n]`,**自动适配各方言**(MySQL/PG/CH/Doris/Snowflake…),生成 SQL 过只读护栏(`assert_readonly_sql`)。支持 sum/avg/max/min/count/count_distinct、多维分组、等值/IN 过滤、时间范围、top_n。
- **ES 族**(`elasticsearch_handler`):编译成 aggs —— 维度 `terms`(**文本字段自动补 `.keyword`**)、度量 metric agg(`count_distinct`→`cardinality` 近似、`count`→count API)、`bool.filter`(等值/IN)+ `range`(时间),`size:0`;有度量按度量降序、无度量按 `_count` 降序。`_build_agg_request` 抽为纯函数便于测试。
  - **关键**:平台按**固定指标定义**编译 DSL(非 LLM 自由生成),不受 `chart-tool-routing` 里"声明式聚合不可靠"的结论影响。
  - **v1 限制**:仅单维度分组、暂不下推 `grain`(与 pandas 兜底口径一致,兜底也不分桶);多维 / grain / 非法聚合 → `AggNotSupported` 回退兜底。
- **其它源**(akshare / mongo / 文件…):未声明 AGGREGATE → 走兜底(拉数 + pandas),行为与 P1a 一致。

`run_sync(metric_code, group_by, filters, time_range, top_n)`:查指标/模型/源 → 进程内建 handler → `_execute` → 统一 `[{dim..., value}]`(agno 同步链路);`preview` 经 threadpool 复用同一路径。

## 1.3 Agent 集成(module_ai)

**两个工具**(薄封装 MetricService,加入 `_assemble_tools` 的 data 能力):
- `list_metrics(keyword='')` → 命中指标目录(code/name/caliber/可用维度)
- `query_metric(metric_code, group_by=[], filters={}, time_range=None, top_n=None)` → 权威数字

**注入 + 漏斗**(改 `build_data_catalog` 同层,或独立 `build_metric_catalog`):会话装配注入**精简指标目录**(code+name+一句口径,可复用 catalog_index 向量检索按问题召回相关指标);`_DATA_AGENT_INSTRUCTIONS` 加漏斗第 0 步:
```
0. 指标层命中 → 必须用 query_metric(别自写 SQL/agg)   ← 新增,最信
1. 认源(检索目录)  2. KB 验证解法  3. 原始表自由取数
```

## 1.4 编写(前端 + 人拍板)
- **指标管理页**(数据管理下,镜像 ai/skill 页):CRUD;绑定 data_model 时自动带出字段候选;编辑 度量/维度/过滤/口径/verified_examples。
- **AI 起草候选**(P1b):LLM 读模型 schema + 样本 → 产**指标草稿** → **人确认才发布**(绝不自动上线)。

## 1.5 种子 demo 指标(验证用)
- `industry_pe_avg`:dm_fin_industry_pe,avg(pe_weighted) by industry_name
- `market_main_net`:dm_fin_market_fund_flow,main_net by date(单位 亿)
- `index_close`:dm_fin_index_daily,close by name/date

---

# Part 2 — 任务级血缘(P2)

## 2.1 数据来源:声明式,不解析
血缘的**真相来自已有声明**,无需 SQL 解析:
- **任务**:`extract.datasource_code`(+ object/native / `datasource_codes` 多源)→ `load.datasource_code + table`
- **模型**:data_model.datasource_code + object_name(= 某源某表)
- **指标**:data_metric.model_id → 模型
- **看板**:data_dashboard_canvas 组件的 modelId → 模型
- **技能**:ai_skill.datasource_codes → 源

## 2.2 血缘图:按需计算(P2a,不落表)

`LineageService.build_graph(node=None, direction='both', depth=3)`(module_data/service):
- **节点**:`datasource` / `model`(表/索引)/ `task` / `metric` / `dashboard` / `skill`
- **边**:
  - task: `extract.datasource → task → load.datasource.table(model)`
  - model ↔ datasource(model 属于源)
  - metric → model,dashboard → model,skill → datasource
- 读上述几张表在内存拼图(自托管规模足够,始终新鲜);`node` 给定则返回其上下游子图。
- 需要提速再**物化 `data_lineage` 边表**(P2 之后)。

## 2.3 API + 前端
- `GET /data/lineage?nodeType=&nodeId=&direction=&depth=` → 图 JSON(nodes/edges),权限 `data:model:list`,按 tenant 过滤。
- 前端:数据源/模型详情页加「血缘」tab(AntV X6/G6 渲染上下游),或独立血缘图页。

## 2.4 影响分析 / 防过期(P2b)
- 挂在 `DataModelService.edit/delete`(与 catalog 索引同步同一处):模型 schema 变更 → 沿**下游边**找依赖的 **指标 / 看板 / 技能** → 置 `review_state='stale'`,列表标**「待复核」**。
- 删除模型前:若有下游依赖 → 提示影响面(哪些指标/看板会受影响),避免误删。

## 2.5 与指标层/检索的融合
- **指标未命中**:agent 经血缘定位"该指标该从哪个受治理模型聚合"(model 节点),再走原始表——把 Anthropic 的"我不认识→我知道从哪个模型聚合"落地。
- **统一检索**(P4,超本范围):catalog_index 同时容纳 表/指标/技能,一次向量查召回三者。

---

## 3. 分阶段

| 阶段 | 内容 | 状态 |
|---|---|---|
| **P1a** | `data_metric` 表(DO/VO/DAO/SQL×2)+ MetricService(拉数 + pandas 聚合)+ `list_metrics`/`query_metric` + 注入指标目录 + 漏斗第0步 + CRUD 前端 + demo 指标 | ✅ 已落地 |
| **P1b-下推** | 聚合 IR `AggSpec` + `Capability.AGGREGATE` + `_execute` 下推优先/pandas 兜底路由;SQL 族(SQLAlchemy Core)+ ES 族(aggs)库内聚合;端到端对拍测试(SQL 真库 19 项 + ES FakeES 9 项) | ✅ 已落地 |
| **P1b-起草** | AI 读模型 schema + 样本起草**指标草稿**(人确认才发布)+ verified_examples 兜底/评测种子 | ⬜ 待做 |
| **P2a** | LineageService.build_graph(任务级、按需)+ /data/lineage API + 前端血缘图 | ✅ 已落地 |
| **P2b** | 影响分析 + 改模型→依赖标 `stale`(挂 DataModelService.edit/delete) | ⬜ 待做 |
| **P1b-下推补全** | grain 时间分桶下推(SQL date_trunc / ES date_histogram)、Mongo 族、`verified_examples` 双跑对拍作下推切换回归闸 | ⬜ 待做 |

## 4. 验证
0. **下推对拍**(P1b,已通过):`tests/test_metric_pushdown_{sql,es}.py`——SQL 用 sqlite 真库,对 sum/avg/max/min/count/count_distinct × 分组/总值/过滤/时间范围/top_n/多维 逐组合验证**下推结果 == pandas 兜底结果**并核验绝对值;`_execute` 路由验证"无能力/下推异常"两路回退;ES 用 FakeES 验证 DSL 构造(`.keyword`/order/range/count)与响应→行映射、不可下推形态回退。
1. **编译**:SQL/ES 各造 1 指标,`query_metric` 结果与手写查询一致。
2. **漏斗**:问「各行业平均市盈率」→ agent 调 `query_metric('industry_pe_avg', group_by=['industry'])` 而非自写;未命中的才回退。
3. **一致性**:同指标不同问法/不同轮结果一致。
4. **血缘**:demo 模型的上下游图正确(源→模型→指标/看板);改模型字段 → 依赖指标标 stale;前端渲染。
5. **e2e**(兜底模型):端到端对比"有无指标层"的取数正确率、轮数、token;删模型给出影响面提示。

## 5. 风险与缓解
| 风险 | 缓解 |
|---|---|
| 编译器覆盖不全(多表 join/复杂聚合) | P1 只做单模型单度量 + 简单过滤/维度/时间;复杂回退 KB 解法/原始表,不硬编译 |
| 下推与兜底口径漂移 | 两路共用 `_shape`/`_round_rows`;`AggSpec.validate` + 能力位把不可下推形态挡回兜底;对拍测试作回归闸,下推**永不比兜底差** |
| 下推近似/大表内存 | ES `count_distinct` 用 `cardinality`(近似,高基数有误差,已注明);兜底受 `_FETCH_CAP` 限、大表以下推为主;度量列假设为数值 |
| 指标定义错(比没有更危险) | 人拍板 + verified_examples 兜底 + review 审计;AI 只起草 |
| 与 Skill/KB 职责混淆 | 明确:指标=**what(权威数字)**,Skill=**how(操作手册)**,血缘=**关系/治理**,三者正交 |
| 代码取数血缘边不全 | 任务级用 `extract.datasource_codes` 多源列表建边(声明的都建);列级/运行时留 P3 |
| 跨源编译差异 | 结构化源(SQL/ES)下推编译,其它源回退拉数+pandas;两路统一产出 `[{dim..., value}]` |

## 6. 落地顺序建议
已落地:**P1a**(指标层最小闭环)→ **P2a**(任务级血缘图)→ **P1b-下推**(库内聚合,解开 `_FETCH_CAP` 1 万行上限,金融 RDBMS 日线 + ES 时序大表受益最大)。
待做:**P2b**(防过期,把指标/技能/看板串成可治理整体)→ **P1b-起草**(AI 起草指标候选,人拍板)→ **P1b-下推补全**(grain 分桶 / Mongo / verified_examples 回归闸)。
