> [简体中文](metric-layer-and-lineage-design.md) | **English**

# Design Doc: Metric Layer (P1) + Task-Level Lineage (P2) — Executable Plan

> Status: P1a metric layer + P1b pushdown + P2a lineage graph **shipped**; P1b "AI-drafted candidates" still TODO (see §3).
> Scope: `module_data` (metric definition / compile & execute, lineage), `module_ai` (agent tools + funnel), frontend (metric management page + lineage graph)
> Supersedes: `semantic-metric-layer-design.md` (planning draft)
> Research basis: semantic layer — dbt MetricFlow (YAML in the same repo, executes in the warehouse, open-sourced 2025-10) / Cube (standalone service + Agentic governed context, LLM accuracy ×3–5) / Snowflake Semantic Views (+~20%); lineage — sqlglot static column-level / DataHub schema-aware (97–99%) / OpenLineage runtime.

---

## 1. Context / Goals

- **Why**: ezdata currently has no semantic layer, so caliber-type questions ("active/revenue/average P/E") can only be papered over via remark → an accuracy ceiling (the market consensus is that the semantic layer is the biggest lever). At the same time, ezdata's ETL tasks **already declare extract→load in their parameters**, so task-level lineage is "almost free."
- **P1 metric layer**: define a metric once (measure + dimensions + caliber); the agent fetches authoritative, consistent numbers via `query_metric` by metric name; the definer makes the final call.
- **P2 task-level lineage**: from task parameters + the binding relationships of models/metrics/dashboards/skills, build a "source → model → metric/dashboard/skill" lineage graph; supports **impact analysis / staleness prevention**.
- **Fusion**: fills in the top two layers of the agent funnel — metric (most trusted) → lineage (locate the governed model when no metric is defined) → retrieval (done) → raw tables.

**Non-goals**: don't bring in dbt (in-warehouse) / Cube (heavy); don't adopt DataHub/OpenMetadata; column-level lineage (sqlglot) and OpenLineage runtime are left for P3.

## 2. Principles
- **The definer makes the final call**: the LLM only drafts docs/candidates; a metric definition must be human-confirmed (dbt/WrenAI/Snowflake all hit the pitfall of the LLM auto-generating and baking ambiguity in).
- **Build on top of `data_model`**: reuse source/table/field metadata + handler execution; don't rebuild.
- **Lineage from "declaration," not "parsing"**: task parameters already contain extract→load, so task-level lineage is obtained with zero parsing.

---

# Part 1 — Metric Layer (P1)

## 1.1 Data model: `data_metric` (new table, module_data)

| Column | Type | Description |
|---|---|---|
| metric_id | bigint PK auto | |
| name | varchar(100) not null | Metric name ("Industry average P/E") |
| code | varchar(100) uniq not null | Unique identifier, referenced by query_metric |
| synonyms | varchar(500) | Synonyms (comma-separated, improves matching) |
| caliber | text | **Caliber (authoritative, human-written)**: what to compute, what's included/excluded, window |
| model_id | varchar(64) | Binds data_model.id (carries out datasource_code/object_name/fields) |
| measure | text(JSON) | `{"agg":"sum|avg|count|max|min|count_distinct|ratio|expr","field":"","expr":""}` |
| dimensions | text(JSON) | Allowed grouping dimensions `[{"field":"","name":""}]` |
| time_field | varchar(100) | Time field (nullable) |
| default_grain | varchar(20) | day/week/month |
| default_filters | text(JSON) | Fixed-caliber filters (exclude test/anomalous data) |
| unit / fmt | varchar(50) | Unit (100M / %), decimal places |
| verified_examples | text(JSON) | Human-vetted `[{"question":"","expect":""}]` (≈ Cortex VQR, doubles as eval seed) |
| status | char(1) '0' | 0 enabled, 1 disabled |
| review_state | varchar(20) 'ok' | ok / stale (triggered by P2 lineage) |
| built_in / user_id / dept_id / create_* / update_* / remark / tenant_id | | Same as ai_skill |

DDL goes into `api/sql/ezdata.sql` + `ezdata-pg.sql`; `DataMetric(Base, TenantMixin)`, menu/permissions `data:metric:*`.

## 1.2 Compile & execute: `MetricService` (module_data/service) — pushdown-first + pandas fallback

**Execution strategy (`_execute`, implemented in P1b)**: a metric query **pushes down** to in-database aggregation by default (small result set, scales to big tables); when the source doesn't support pushdown / raises `AggNotSupported` / a pushdown exception occurs, it **falls back** to "fetch rows (≤ `_FETCH_CAP` rows) + pandas aggregation" (`_aggregate`). Both paths share `_shape`/`_round_rows` for normalization, so **calibers are consistent** (guaranteed by cross-check tests, see §4) — therefore pushdown is **never worse than the status quo** and can be rolled out gradually per source / per metric.

**Aggregation IR `AggSpec`** (`ezdata/handlers/agg_spec.py`, source-agnostic): normalizes a metric definition into
`{table, measure{agg,field}, group_by, filters, time_field, time_range, grain, top_n}`, so the handler doesn't need to understand the metric definition; `validate()` catches illegal / non-pushdownable shapes → raises `AggNotSupported` to hand off to the fallback. Parsing of `default_filters`/default dimensions happens on the `MetricService` side; `AggSpec` only carries "what ultimately needs to be computed."

**Capability-bit driven**: adds `Capability.AGGREGATE`; `_execute` checks `handler.has(AGGREGATE)` before pushing down. Each source family implements `handler.aggregate(spec) -> [{dim..., value}]`:

- **SQL family** (`sql_base`): uses **SQLAlchemy Core** to build `SELECT {dims}, {agg}({field}) AS value FROM {table} WHERE {default∧user∧time} GROUP BY {dims} ORDER BY value DESC [LIMIT top_n]`, **auto-adapting to each dialect** (MySQL/PG/CH/Doris/Snowflake…); the generated SQL passes the read-only guardrail (`assert_readonly_sql`). Supports sum/avg/max/min/count/count_distinct, multi-dimensional grouping, equality/IN filters, time ranges, top_n.
- **ES family** (`elasticsearch_handler`): compiles into aggs — dimensions `terms` (**text fields auto-suffixed with `.keyword`**), measure metric agg (`count_distinct`→`cardinality` approximation, `count`→count API), `bool.filter` (equality/IN) + `range` (time), `size:0`; when there's a measure, sort by measure descending; otherwise sort by `_count` descending. `_build_agg_request` is factored out as a pure function for easier testing.
  - **Key**: the platform compiles the DSL from a **fixed metric definition** (not free-form LLM generation), so it isn't affected by the "declarative aggregation is unreliable" conclusion in `chart-tool-routing`.
  - **v1 limitations**: single-dimension grouping only, `grain` not yet pushed down (consistent with the pandas fallback caliber, which also doesn't bucket); multi-dimensional / grain / illegal aggregation → `AggNotSupported` falls back to the fallback path.
- **Other sources** (akshare / mongo / files…): AGGREGATE not declared → go through the fallback (fetch rows + pandas), behavior identical to P1a.

`run_sync(metric_code, group_by, filters, time_range, top_n)`: look up metric/model/source → build handler in-process → `_execute` → unified `[{dim..., value}]` (agno synchronous path); `preview` reuses the same path via threadpool.

## 1.3 Agent integration (module_ai)

**Two tools** (thin wrappers over MetricService, added to the data capabilities in `_assemble_tools`):
- `list_metrics(keyword='')` → matched metric catalog (code/name/caliber/available dimensions)
- `query_metric(metric_code, group_by=[], filters={}, time_range=None, top_n=None)` → authoritative numbers

**Injection + funnel** (modify `build_data_catalog` at the same layer, or a standalone `build_metric_catalog`): session assembly injects a **compact metric catalog** (code + name + one-line caliber; can reuse catalog_index vector retrieval to recall relevant metrics per question); `_DATA_AGENT_INSTRUCTIONS` adds step 0 of the funnel:
```
0. Metric layer hit → must use query_metric (don't write your own SQL/agg)   ← new, most trusted
1. Identify source (search catalog)  2. Validate solution against KB  3. Free-form fetch from raw tables
```

## 1.4 Authoring (frontend + human final call)
- **Metric management page** (under Data Management, mirrors the ai/skill page): CRUD; auto-carries out field candidates when binding data_model; edit measure/dimensions/filters/caliber/verified_examples.
- **AI-drafted candidates** (P1b): the LLM reads the model schema + samples → produces a **metric draft** → **published only after human confirmation** (never auto-published).

## 1.5 Seed demo metrics (for validation)
- `industry_pe_avg`: dm_fin_industry_pe, avg(pe_weighted) by industry_name
- `market_main_net`: dm_fin_market_fund_flow, main_net by date (unit: 100M)
- `index_close`: dm_fin_index_daily, close by name/date

---

# Part 2 — Task-Level Lineage (P2)

## 2.1 Data source: declarative, no parsing
The **truth of lineage comes from existing declarations**, no SQL parsing needed:
- **Task**: `extract.datasource_code` (+ object/native / `datasource_codes` multi-source) → `load.datasource_code + table`
- **Model**: data_model.datasource_code + object_name (= a table in a source)
- **Metric**: data_metric.model_id → model
- **Dashboard**: the modelId of a data_dashboard_canvas component → model
- **Skill**: ai_skill.datasource_codes → source

## 2.2 Lineage graph: computed on demand (P2a, not persisted)

`LineageService.build_graph(node=None, direction='both', depth=3)` (module_data/service):
- **Nodes**: `datasource` / `model` (table/index) / `task` / `metric` / `dashboard` / `skill`
- **Edges**:
  - task: `extract.datasource → task → load.datasource.table(model)`
  - model ↔ datasource (model belongs to source)
  - metric → model, dashboard → model, skill → datasource
- Reads the tables above and assembles the graph in memory (self-hosted scale is sufficient, always fresh); if `node` is given, returns its upstream/downstream subgraph.
- If it needs to be faster, **materialize the `data_lineage` edge table** (after P2).

## 2.3 API + frontend
- `GET /data/lineage?nodeType=&nodeId=&direction=&depth=` → graph JSON (nodes/edges), permission `data:model:list`, filtered by tenant.
- Frontend: add a "Lineage" tab to the datasource/model detail page (render upstream/downstream with AntV X6/G6), or a standalone lineage graph page.

## 2.4 Impact analysis / staleness prevention (P2b)
- Hooked into `DataModelService.edit/delete` (same place as catalog index sync): model schema change → follow **downstream edges** to find dependent **metrics / dashboards / skills** → set `review_state='stale'`, mark them **"pending review"** in the list.
- Before deleting a model: if there are downstream dependencies → warn about the impact surface (which metrics/dashboards would be affected), to avoid accidental deletion.

## 2.5 Fusion with the metric layer / retrieval
- **Metric not matched**: the agent uses lineage to locate "which governed model this metric should be aggregated from" (model node), then goes to the raw tables — implementing Anthropic's "I don't recognize this → I know which model to aggregate from."
- **Unified retrieval** (P4, beyond this scope): catalog_index holds tables/metrics/skills together, so a single vector query recalls all three.

---

## 3. Phasing

| Phase | Content | Status |
|---|---|---|
| **P1a** | `data_metric` table (DO/VO/DAO/SQL×2) + MetricService (fetch rows + pandas aggregation) + `list_metrics`/`query_metric` + inject metric catalog + funnel step 0 + CRUD frontend + demo metrics | ✅ Shipped |
| **P1b-pushdown** | Aggregation IR `AggSpec` + `Capability.AGGREGATE` + `_execute` pushdown-first/pandas-fallback routing; SQL family (SQLAlchemy Core) + ES family (aggs) in-database aggregation; end-to-end cross-check tests (SQL real DB 19 items + ES FakeES 9 items) | ✅ Shipped |
| **P1b-draft** | AI reads model schema + samples to draft **metric drafts** (published only after human confirmation) + verified_examples fallback/eval seed | ⬜ TODO |
| **P2a** | LineageService.build_graph (task-level, on-demand) + /data/lineage API + frontend lineage graph | ✅ Shipped |
| **P2b** | Impact analysis + edit model → mark dependencies `stale` (hooked into DataModelService.edit/delete) | ⬜ TODO |
| **P1b-pushdown completion** | grain time bucketing pushdown (SQL date_trunc / ES date_histogram), Mongo family, `verified_examples` dual-run cross-check as a pushdown-switch regression gate | ⬜ TODO |

## 4. Validation
0. **Pushdown cross-check** (P1b, passed): `tests/test_metric_pushdown_{sql,es}.py` — SQL uses a real sqlite DB, verifying **pushdown result == pandas fallback result** across sum/avg/max/min/count/count_distinct × grouping/total/filter/time-range/top_n/multi-dimension combinations and checking absolute values; `_execute` routing verifies the two fallback paths ("no capability / pushdown exception"); ES uses FakeES to verify DSL construction (`.keyword`/order/range/count) and response→row mapping, plus fallback on non-pushdownable shapes.
1. **Compile**: create 1 metric each for SQL/ES; `query_metric` result matches the hand-written query.
2. **Funnel**: asking "average P/E per industry" → agent calls `query_metric('industry_pe_avg', group_by=['industry'])` rather than writing its own; only falls back when not matched.
3. **Consistency**: the same metric gives consistent results across different phrasings / different turns.
4. **Lineage**: the demo model's upstream/downstream graph is correct (source → model → metric/dashboard); changing a model field → dependent metric marked stale; frontend renders it.
5. **e2e** (fallback model): end-to-end comparison of fetch accuracy, number of turns, and tokens "with vs. without the metric layer"; deleting a model gives an impact-surface warning.

## 5. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Incomplete compiler coverage (multi-table join / complex aggregation) | P1 only does single-model single-measure + simple filter/dimension/time; complex cases fall back to KB solutions/raw tables, no hard compilation |
| Caliber drift between pushdown and fallback | Both paths share `_shape`/`_round_rows`; `AggSpec.validate` + capability bit push non-pushdownable shapes back to fallback; cross-check tests act as a regression gate, pushdown is **never worse than fallback** |
| Pushdown approximation / big-table memory | ES `count_distinct` uses `cardinality` (approximate, error at high cardinality, noted); fallback is bounded by `_FETCH_CAP`, big tables rely on pushdown; measure columns are assumed numeric |
| Wrong metric definition (more dangerous than having none) | Human final call + verified_examples fallback + review audit; AI only drafts |
| Confusion of responsibilities with Skill/KB | Clear: metric = **what (authoritative numbers)**, Skill = **how (operations manual)**, lineage = **relationships/governance**; the three are orthogonal |
| Incomplete lineage edges for code-based fetches | Task-level uses the `extract.datasource_codes` multi-source list to build edges (build all that are declared); column-level/runtime left for P3 |
| Cross-source compilation differences | Structured sources (SQL/ES) compile to pushdown, other sources fall back to fetch + pandas; both paths uniformly produce `[{dim..., value}]` |

## 6. Suggested implementation order
Shipped: **P1a** (minimal metric-layer loop) → **P2a** (task-level lineage graph) → **P1b-pushdown** (in-database aggregation, lifting the `_FETCH_CAP` 10k-row limit; the biggest beneficiaries are financial RDBMS daily bars + ES time-series big tables).
TODO: **P2b** (staleness prevention, stringing metrics/skills/dashboards into a governable whole) → **P1b-draft** (AI drafts metric candidates, human final call) → **P1b-pushdown completion** (grain bucketing / Mongo / verified_examples regression gate).
