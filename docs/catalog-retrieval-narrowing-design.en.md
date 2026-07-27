> [简体中文](catalog-retrieval-narrowing-design.md) | **English**

# Design Doc: Data Catalog Retrieval Narrowing (Catalog Retrieval) — Full Injection → Vector Top-K

> Status: Draft / Pending Review
> Scope: `module_ai` (context assembly `build_data_catalog`, chat_services), `module_data` (data_model sync hook), reusing `module_rag` (embedding + vector retrieval)
> References: WrenAI "intent → vector-retrieve relevant tables → generate"; Anthropic "don't make the Agent brute-force search across a million fields — first narrow to a few dozen curated files".

---

## 1. Context

Today `build_data_catalog()` stuffs a manifest of **up to 30 sources × 12 tables** into the system prompt every turn, leaving the LLM to scan and identify sources itself. Two problems:
- **Doesn't scale**: as sources/tables grow, resident tokens climb linearly and the information diverges (most tables are irrelevant to the current question).
- **Table names only, no columns**: after the agent identifies a table it still has to call `get_table_schema` to fetch columns — an extra round-trip.

Yet ezdata **already has vector retrieval infrastructure** (`module_rag`: embedding + ES8 vector store + `retrieve()`, used for KB / recipes); it just isn't applied to **table/field selection**. This design replaces "dump the full catalog" with "vector-retrieve the Top-K relevant tables for the question", aligning with WrenAI's `intent→retrieve→generate` and delivering the "save tokens + stay focused" goal from earlier discussions.

## 2. Goals / Non-goals

**Goals**
1. Change data catalog injection from "full" to "retrieve Top-K tables for the current question (with key columns)", so resident tokens stay **constant in K, independent of total table count**.
2. Reuse `module_rag`'s embedding/vector store; do not build a new retrieval engine.
3. **Never worse than today**: automatically fall back to the current full-injection behavior when retrieval is unavailable or the catalog is small.

**Non-goals (out of scope this iteration)**
- Do not change the agent's tools or funnel (list_datasources/get_table_schema stay as fallback).
- Do not do unified retrieval of metrics/skills (extension slot reserved, see §10).
- Do not introduce a new embedding dependency (reuse the embedding fallback already configured in RAG).

## 3. Principles
- **Layering**: source level (cheap, resident) + table level (retrieval, Top-K) + drill-down (tools, on demand).
- **Narrow without hiding**: for tables the retrieval misses, the agent can still drill down via tools (follow-up / miss fallback).
- **Sync in place**: data_model changes trigger incremental index updates; failures do not affect the conversation.

## 4. Architecture: Three-Tier Catalog

```
Tier A Source level (resident, tiny): list every accessible datasource's code+name+type (no tables)
        —— lets the agent know "which sources exist", capped at a few hundred tokens
Tier B Table level (retrieve Top-K by question): vector-retrieve the K tables most relevant to the current question,
        injecting table name = business name + key columns (with descriptions) + remarks —— incidentally saves a get_table_schema round-trip
Tier C Drill-down (on demand, tools): list_datasources / get_table_schema —— anything retrieval missed can still be queried as before
```

## 5. Index Design (reusing module_rag)

**Index unit = one data_model (table)**. Document text (for embedding):
```
数据源 {source_name}({source_type}) · 表 {object_name} · 业务名 {model_name}
字段: col1(desc), col2(desc), ...        # column metadata already stored in data_model; left blank if absent
备注: {remark}
```
Metadata: `{datasource_code, object_name, model_id, tenant_id}`.

**Storage**: a dedicated system index (e.g. ES `ez_catalog_index`), **reusing module_rag's embedding client and ES connection**, but **physically isolated** from user KB datasets (heterogeneous content, different lifecycle, don't pollute the user knowledge base).
> Alternative: register a per-tenant system dataset `__catalog__` inside module_rag and reuse `retrieve(dataset_ids=[__catalog__])`. Pick whichever requires the smaller change given rag's existing abstractions.

**Embedding**: reuse the `AiConfig`/RAG fallback embedding (DashScope, etc.); the Contextual prefix already carries source context, which aids recall.

## 6. Sync (Incremental + Full)

- **Incremental**: `data_model` save/deactivate/delete → upsert/delete the corresponding index document (hooked into the model service's write path; async, failures only warn).
- **Full rebuild**: a command/task `rebuild_catalog_index(tenant?)`, run on first rollout or when drift occurs.
- **Tenant isolation**: documents carry tenant_id; retrieval filters by tenant (super-admin bypass as today).

## 7. Retrieval and Injection

**New** `CatalogRetrievalService.retrieve_tables(question, scope_codes, k=8)`:
- Vector-retrieve `ez_catalog_index` (filtered by tenant + scope_codes) → Top-K table documents.
- Return structured `[{datasource_code, object_name, model_name, columns, remark}]`.

**Refactor** `build_data_catalog(allowed_codes, *, question=None, k=8)`:
- `question` present and index available → produce **Tier A (source level, full list) + Tier B (Top-K tables with columns)**.
- `question` empty / index unavailable / **total table count ≤ threshold (e.g. 20)** → **fall back to current full behavior** (giving a small catalog in full is simpler; only retrieve for large catalogs).

**Refactor** `chat_services` / `_build_agent`: pass `chat_req.message` (optionally concatenated with the last 1–2 user turns to ease follow-ups) as `question`.

## 8. Token / Scaling Analysis

| | Today (full) | This design (retrieval) |
|---|---|---|
| Resident size | grows linearly with sources × tables | **Tier A (source count) + Tier B (constant K)**, independent of total table count |
| Relevance | all table names mixed together | Top-K matched tables + **key columns** (usually saves a get_table_schema round-trip) |
| Small catalog (≤20 tables) | given in full | same as today (threshold fallback) |

Net effect: small catalogs unchanged, **large catalogs markedly narrowed and more accurate**, with potentially fewer tool round-trips.

## 9. Fallback and Guardrails (never worse than today)
- Index service error / empty → try/except falls back to full `build_data_catalog` (the existing implementation is kept verbatim as fallback).
- After retrieving Top-K, **Tier C tools are always present**: on follow-ups or misses the agent can still drill down via `list_datasources/get_table_schema`.
- Threshold guard: don't enable retrieval when there are few tables, to avoid "narrowing for narrowing's sake".

## 10. Extension Slot (aligned with other designs, not this iteration)
The same `ez_catalog_index` can later hold **metrics** (see semantic-metric-layer-design) and **skill descriptions** for **unified retrieval**: a single vector query recalls "relevant tables / relevant metrics / relevant skills" at once, fully replacing both "dump the full catalog" and "list all skills in full" with on-demand recall. This design's index and retrieval interfaces are reserved for this (documents carry `unit_type: table|metric|skill`).

## 11. Phasing
- **Phase 1**: `ez_catalog_index` + `CatalogRetrievalService` (reusing rag embedding/ES) + full-rebuild command + `build_data_catalog(question=)` refactor + chat_services argument passing + threshold/exception fallback. Build the index for the seed/demo catalog to validate.
- **Phase 2**: incremental sync hook on the data_model write path; follow-up retrieval queries carry history.
- **Phase 3**: unified retrieval (tables + metrics + skills).

## 12. Validation
1. **Fallback safety**: disable the index (or empty index) → conversation is identical to today (full catalog).
2. **Correct narrowing**: with a large catalog (create 50+ tables), ask "Kweichow Moutai daily line" → the injected Tier B hits relevant tables like `fin_stock_daily` and contains no irrelevant tables; resident character count is clearly smaller than full.
3. **Fewer round-trips**: when Tier B already carries key columns, the agent writes the query directly, calling get_table_schema one fewer time.
4. **Miss fallback**: ask about an obscure table the retrieval didn't recall → the agent can still fetch it via get_table_schema.
5. **scope/tenant**: with an app bound to 3 sources, retrieval stays within those 3 sources; no cross-tenant leakage.
6. **e2e**: on the fallback model, compare "retrieval catalog vs full catalog" for query correctness, tool round count, and resident tokens.

## 13. Risks
| Risk | Mitigation |
|---|---|
| short follow-up questions retrieve no relevant table | concatenate the last 1–2 user turns into the query; Tier A resident + Tier C tool fallback |
| index drifts from data_model | write-path incremental sync + full-rebuild command; retrieval is only "preferred recall", drill-down as fallback |
| embedding dependency/cost | reuse the embedding already configured in RAG; batch/cache; fall back to full on error |
| over-engineering for small catalogs | table-count threshold guard, ≤20 goes full directly |
| missing column metadata (some sources have no modeled columns) | document columns may be empty, degrading to "table name + business name" recall, without affecting usability |
