> [简体中文](DATA_MODULE_DESIGN.md) | **English**

# Data Module Design (Data Management + Data Integration + Data API)

> This document describes the design and implementation of `module_data` (Data Management / Data Integration / Data API), grounded in the code that has already landed: `module_data/handlers` (60+ source connectors + capability flags + unified filters + connection_schema).

## 0. In One Sentence

- **Data Management**: A Navicat-style tool — a left-side "Data Source → Data Model" tree, right-side Tabs (Basic Info / Data Query / Data API), with Tab visibility driven by **capability flags**.
- **Data Integration**: Rather than building another engine, this is made into a **task component** of `module_task_schedule` (ETL spec → `compile_to_dlt` → reuse scheduling/retry/monitoring/alerting).
- **Data API**: Externally exposes only declarative `filter`; **native queries** are for internal/trusted use only; **AI data fetching** provides an "AI generates native query → preview → execute" entry point.

---

## 1. Overall Architecture

```
                         ┌───────────────── Frontend (Vue3+Element Plus+TS) ─────────────────┐
                         │  Data Management view: left tree (source→model) + right Tabs (info/query/api) │
                         └───────┬───────────────────┬───────────────────┬──────────────┘
                                 │ schema form         │ filter/native/AI query  │ API config
                ┌────────────────▼─────────┐ ┌────────▼─────────┐ ┌────────▼───────────┐
   Backend      │ module_data              │ │ Read path (per-request) │ │ module_dataapi     │
                │  DataSource / DataModel  │ │  connector.query  │ │  Data API spec     │
                │  connectors(78,built)    │ │  /search(filters) │ │  Dynamic routing+security │
                │  introspect / schema     │ │  AI fetch (Agno)  │ │  Reuse cache/rate-limit/masking │
                └─────────┬────────────────┘ └───────────────────┘ └────────────────────┘
                          │ ETL spec (Data Integration)
                ┌─────────▼──────────────────────────────┐
                │ module_task_schedule (reused)           │
                │  task_template: data_integration         │
                │  runner: compile_to_dlt(spec) → dlt       │
                │  scheduling/queue/retry/task_instance/alerting all reused │
                └──────────────────────────────────────────┘
```

Three runtimes: **batch ETL (write) = task scheduling**; **Data API (read) = per-request native**; **streaming = long-running worker**.

---

## 2. Data Modeling (DO Tables)

### 2.1 `DataSource` (Data Source = a connection)
```
id, name, code(stable reference), source_type, family, config(JSON non-secret),
secrets(Text, AES encrypted), status(untested/ok/failed), last_test_at, remark
+ TenantMixin(tenant_id/dept_id/create_by)
```
- On submit, config / secrets are split according to `connection_schema` (SecretStr fields encrypted), and returned masked.
- `create_handler(source_type, config, secrets)` consumes it directly.

### 2.2 `DataModel` (Data Model = a specific table/collection/index/topic within a source)
```
id, name, code, datasource_code(references DataSource),
kind(table|collection|index|topic|custom_query),
object_name(table/index/collection name), db_schema, fields(JSON, introspect cache),
default_filters(JSON), auth(can_query/can_api/can_extract/can_write flags),
remark + TenantMixin
```
- The **leaf node** of the tree; corresponds to the legacy `model` + `model_conf`.
- Multiple models can be created under one source; a model's `auth` flags ∩ connector `capabilities` = actually available capabilities.

### 2.3 ETL = Reuse `task`, No New Top-Level Table
- Add a `task_template`: `data_integration`, whose `params` = the **ETL spec** (see §4 below).
- One integration task = one `task` (template_code=`data_integration`); scheduling/instances/logs all use the existing machinery.

### 2.4 `DataApi` (Data API)
```
id, name, path, method, datamodel_code, query_mode(filter|native),
filter_config(JSON) | native_query(Text), params(JSON declaration),
pagination(default/max), security(auth/rate_limit/cache_ttl/field_mask/tenant_scoped),
status + TenantMixin
```
- Externally = `query_mode=filter` (declarative only); `native` is internal only.

---

## 3. Backend Endpoints (module_data)

| Endpoint | Purpose | Underlying |
|---|---|---|
| `GET /data/source/types` | Available sources + capability flags (source-creation dropdown/cards, with icons) | `list_source_types()` |
| `GET /data/source/schema/{type}` | Connection parameter JSON Schema (renders form) | `connection_schema()` |
| `GET /data/operators` | Operator catalog (filter builder) | `query.OPERATORS` |
| `POST /data/source` `PUT/DELETE` `GET` | Data source CRUD (secrets encrypted/masked) | DAO |
| `POST /data/source/test` | Test connection | `handler.test_connection()` |
| `GET /data/source/{id}/tables` | Lists/indexes/collections (build tree + select model) | `list_tables()` |
| `GET /data/source/{id}/tables/{t}/columns` | Field structure | `get_columns()` |
| `POST /data/model` `...` | Data model CRUD | DAO |
| `POST /data/model/{id}/query` | **Data query (no pagination)**: filters or native, **render exactly as many rows as returned** | `query()` |
| `POST /data/model/{id}/ai-query` | **AI data fetching**: NL→native query→preview | module_ai(Agno) |
| `POST /data/model/{id}/integrate` | Generate integration task (jumps to task scheduling) | module_task_schedule |

> Queries go through `query()`, which directly returns the entire result set (the row count is controlled by the user's own filters / the LIMIT in the native SQL), and the frontend renders it with vxe virtual scrolling; **no server-side pagination**.
> **Pagination lives only in the Data API** (§6): connectors additionally provide `search(table, filters, page, pagesize) → {records,total}` (SQL=LIMIT/OFFSET+COUNT, ES=from/size, Mongo=skip/limit) for the Data API to use.

---

## 4. Data Integration (Task Component)

**ETL spec (task.params):**
```jsonc
{
  "mode": "batch|stream",
  "extract": { "datamodel_code": "...", "filters": [...], "incremental_key": "start_time" },
  "transform": { "kind": "python_code", "code": "<AI-generated, frozen after debugging passes; executed in sandbox>" },
  "load": { "sink": "sqlalchemy|filesystem|duckdb|csv|excel", "datasource_code": "...", "table": "...", "mode": "append|merge|replace" }
}
```
**runner = `compile_to_dlt(spec)` (verified feasible):**
```
Parse datamodel → create_handler → handler.extract(filters, incremental_key)  # extract
   → resource.add_map(sandbox(transform.code))                                # transform
   → dlt.pipeline(destination=build_dest(load)).run(...)                      # load
```
- **Batch**: hooks into the Celery queue + APScheduler cron, progress written to `task_instance`, with failure retry/alerting all reused.
- **Stream**: `mode=stream` → long-running worker, `handler.stream()` micro-batches → sink (binlog/kafka).

---

## 5. Data Query (Read Path, Three Tiers) — No Pagination, Render Exactly As Many Rows As Returned

> The Data Query Tab is for interactive exploration (Navicat-style): run query → directly render the entire result set (vxe virtual scrolling handles the row count), **no server-side pagination**; the data volume is controlled by the user themselves in the filters / native SQL (e.g. LIMIT).
> (Optional) The backend keeps a **safety cap** (e.g. 50,000 rows) as a fallback; on exceeding it, prompt the user to add conditions rather than paginating.

1. **filter (form)**: unified `filters` structure → per-source translator → `query()` returns all results. **Field whitelist** (only columns produced by introspect are allowed).
2. **native (internal/trusted)**: directly `query(native SQL/DSL/pipeline)`, parameterized, render exactly what is returned.
3. **AI data fetching**: `ai-query` (NL + schema → Agno generates native query) → preview → manual confirmation → can be saved as a native Data API. AI is only in the build phase, not in the external hot path.

---

## 6. Data API (module_dataapi) — **Pagination Mandatory**

- The opposite of Data Query: external APIs are **forced to paginate** (to prevent external callers from pulling everything at once in one shot), going through `connector.search(filters, page, pagesize)` returning `{records, total, page, pagesize}`.
- spec persisted → **dynamic FastAPI route**: validate declared params → build filters (whitelist) → paginated `search()` → masking/cache/rate-limit → return.
- `pagination`: `{default, max}` (a requested pagesize over max is truncated); by default carries `page`/`pagesize` params.
- Reuse existing building blocks: `ApiCache`/rate-limit decorators/RBAC+row-level multi-tenancy/`crypto`/auto OpenAPI.
- Externally force `query_mode=filter`; native is for internal APIs only.

---

## 7. Frontend (Navicat-style)

```
┌──────────────┬───────────────────────────────────────────────┐
│ [+New Source]│  ┌ Basic Info ┐ ┌ Data Query ┐ ┌ Data API ┐   │
│ ▼ MySQL(ok)  │  │ Connection params(masked)/test conn/capability badges/field table │  │
│   ├ task_inst │  │ ──Data Query──: filter builder + data grid │  │
│   └ task_log  │  │   + native query editor(advanced) + AI fetch box │  │
│ ▼ ES(ok)     │  │ ──Data API──: this model's API list/new/test │  │
│   └ logs      │  └───────────────────────────────────────────┘  │
│ ▶ Qdrant      │  (Tabs shown/hidden by model.auth ∩ connector.capabilities) │
└──────────────┴───────────────────────────────────────────────┘
```
- **Left tree**: source (icon by source_type, status dot) → model (lazy-loaded introspect) → fields.
- **Right Tabs**:
  - **Basic Info**: metadata + connection params (masked) + test connection + capability badges + field table.
  - **Data Query** (shown only with READ): filter builder (column dropdown + OPERATORS + value) + **vxe-table data grid (row/column virtual scrolling)**, **no pagination, render exactly as many rows as returned**; advanced: native query editor (Monaco); AI fetch input box.
  - **Data API** (shown only with GEN_API): this model's Data API list/new (filter spec)/generate URL/test.
- **Capability-flag-driven UI**: READ→Query Tab, GEN_API→API Tab, EXTRACT→"New Integration" button, STREAM→streaming integration, WRITE→write.

### 7.1 Component Selection (finalized)

| Purpose | Selection | Notes |
|---|---|---|
| Overall framework | **Vue3 + Element Plus + TS** | Surrounding UI (layout/buttons/dialogs/Tabs/forms) uniformly Element Plus; **do not bring in antd** |
| **Data grid (rendering large volumes of data)** | **vxe-table 4.x + vxe-pc-ui** | Row/column **virtual scrolling**, no lag with tens of thousands of rows; UI-framework-agnostic, coexists with Element Plus. Self-wrapped thin `DataGrid.vue` wrapper. **Data query scenario: full rendering, no pagination** (virtual scrolling handles it); pagination only in the Data API scenario |
| Left source/model tree | Element Plus `el-tree` (lazy) | Lazy loading: expand source → introspect tables; node icon = `icon.svg` of the 78 handlers, status dot |
| Connection form | JSON-Schema renderer (`@form-create/element-ui` or form-render) | Driven by `GET /data/source/schema/{type}`, zero frontend changes when adding a new source type |
| filter builder | Custom component | Column dropdown (from introspect) + operator dropdown (from `GET /data/operators`) + value; produces unified `filters` |
| Native query editor | Monaco Editor | SQL / JSON (ES DSL / Mongo pipeline) highlighting; used for internal/AI fetching |
| Source type selection | Card grid | Uses the 78 `icon.svg` + capability badges |
| Dialog/layout/split panes | Element Plus (`el-dialog`/`el-tabs`/`el-splitter` or split-pane) | — |

> ⚠️ **Do not adopt** jeecg's `JVxeTable` wrapper (tightly coupled to antd/jeecg, would drag antd back in); only adopt its underlying **vxe-table** core, and write our own Element Plus-style thin `DataGrid.vue` (virtual scrolling + server-side pagination + columns dynamically generated from introspect).
>
> Performance splits into two scenarios:
> - **Data query (interactive exploration)**: no pagination, `query()` returns everything → vxe **virtual scrolling** rendering; row count self-controlled by the user's query, backend may keep a safety cap as a fallback.
> - **Data API (external)**: **server-side pagination** `search(filters,page,pagesize)`, returning only one page at a time.
> Massive exports go through a separate streaming download.

---

## 8. Module Responsibilities

| Module | Responsibility | Status |
|---|---|---|
| `module_data` | Data source + data model + connectors + introspect/query endpoints | Connector layer **built**, models/endpoints to be built |
| `module_task_schedule` | + `data_integration` template + `compile_to_dlt` runner | Scheduling foundation exists, add component |
| `module_dataapi` | Data API spec + dynamic routing + security | New |
| `module_ai` (Agno) | AI data fetching (NL→native query) + transform codegen | Agno already integrated, add tools |
| Frontend | Data Management view | New |

---

## 9. Milestones

```
M1  module_data backend: DataSource/DataModel models + DAO + service + endpoints (types/schema/test/introspect/query/search) + field whitelist
M2  Frontend: three-column layout + schema connection form + left tree (source→model) + Basic Info Tab
M3  Data Query Tab: filter builder + data grid + pagination + native editor
M4  Data Integration: data_integration task template + compile_to_dlt runner, hooked into module_task_schedule (batch)
M5  module_dataapi: filter-only Data API spec + dynamic routing + cache/rate-limit/masking/multi-tenancy
M6  AI data fetching: Agno NL→native query (introspect→generate→preview→save as native API)
M7  Streaming integration: binlog/kafka long-running worker; e2e + data compatibility verification
```

---

## 10. Key Decisions (finalized)

1. External APIs expose only declarative `filter`; native queries are internal only; AI data fetching goes through the "generate native query → preview → execute" entry point.
2. Data Integration = a task scheduling component (no self-built ETL engine), the ETL spec is compiled into dlt for execution.
3. Connector layer is connection-centric; the data model (table/collection) = an independent entity referencing source + object + rules.
4. Capability flags (connector) ∩ auth (model) drive the frontend Tab/button visibility.
5. Vector stores are delegated to Agno; the ES half-engine is not used (native client instead).
6. Frontend: **the data grid uses vxe-table (virtual scrolling, handles large volumes of data)**, surroundings use Element Plus; do not adopt jeecg's JVxeTable wrapper (to avoid pulling antd back in).
```
