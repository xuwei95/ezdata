> [简体中文](DAG_WORKFLOW.md) | **English**

# DAG Workflow Orchestration — Design Notes

> This document describes the design and implementation of DAG (Directed Acyclic Graph) workflow orchestration on top of `module_task_schedule`: executing multiple tasks serially/in parallel by dependency, visual canvas editing with AntV X6, and runtime monitoring; without introducing a heavy external engine, reusing the Celery + runner execution foundation.
>
> Note: This document contains current-state analysis and evolution records from the development period; all capabilities have landed. For the latest actual shape, refer to the code and [DEPLOY.md](DEPLOY.md).

---

## 1. Current State (verified against code)

| Dimension | Current State |
|---|---|
| Execution foundation | ✅ Solid: APScheduler (cron) → `dispatch.run_task` → Celery queue → `executor.execute_task` → `runner.run()` → `TaskInstance` records status. Multi-tenancy, retries, and alert hooks are all in place. |
| Runner registry | ✅ `register_runner('Template')` + `BaseRunner` + `get_runner`; PythonTask / ShellTask / DataIntegrationTask already exist. Stateless and decoupled from orchestration. |
| Single task | ✅ Complete: CRUD, one-off/scheduled triggering, instance records, detailed logs (DB/ES). |
| DAG placeholders | ⚠️ Only 3 placeholders: `Task.task_type=2` (dag workflow), `TaskInstance.parent_id`, `TaskInstance.node_id`. **Zero logic behind them.** |
| DAG definition tables | ❌ None. No node/edge/dependency tables. |
| Orchestration engine | ❌ None. No dependency resolution, no upstream→downstream triggering, no DAG run instance tracking. |
| Frontend canvas | ❌ None. Task management only has forms/lists. |

**Conclusion**: The execution core (Celery + runner + instance records) can be reused directly; the orchestration layer is a greenfield build. The `execute_task(task_id, instance_id)` contract naturally supports "one node, one execution"; what's missing is **node dependency resolution + event-driven downstream triggering + DAG runtime state**.

## 2. Evaluation of the DAG implementation on the master branch (original ezdata production code)

**A complete, usable DAG already exists on master**, and it is the most direct reference for this refactor (much of it is portable):

- **Frontend**: `web/src/views/task/dag_task/dag-editor/` (**AntV X6**, `graph/Node.vue` custom node + `dag-editor.vue` + `DagRunningModal`/`NodeInfoTab`). ✅ Confirms the technology choice; runtime state relies on frontend polling of `get_dag_task_node_status` (aggregating node instances by `parent_id`).
- **DAG utility**: The `DAG` class in `api/utils/dag.py` (`add_node/add_edge (validates against cycles when adding an edge)/predecessors/downstream/all_downstreams/topological_sort/ind_nodes/validate`) — mature, **directly reusable**.
- **Backend orchestration**: `api/tasks/dag_tasks.py`: `dag_task` parses X6 cells (`shape: container-node|edge`, `data.params={template_code, task_conf, retry, countdown, error_type, label}`) → `CeleryDag` builds a **static Celery Canvas** (layered by topology as `group | group`) or runs sequentially in a single process; a node = `dag_node_task` (looks up runner_dict to execute). `run_type`: 1 distributed / 2 single-process.

### Improvement Points (issues in the master implementation that this pass should fix)

| # | Issue | Impact | Fix |
|---|---|---|---|
| 1 | **DAG main status set to success too early**: after `dag_task` submits the canvas (asynchronously), it **immediately** sets `status=SUCCESS, progress=100` while nodes haven't run yet; the real progress logic is commented out and relies solely on frontend polling | The main instance's status/progress is distorted, failures aren't aggregated | **Event-driven**: the terminal node's completion backfills the final state; failures aggregate to failure |
| 2 | **Failure semantics inverted**: `if error_type != 'break': raise e` — `'break'` actually swallows the exception and lets downstream run; only non-break interrupts | Interrupt/continue control is confused, naming and behavior are opposite | Make it explicit `fail_fast`/`continue`, correctly setting downstream to `SKIPPED` |
| 3 | **Static Canvas's layer barrier wastes parallelism**: `group \| group` serializes by topological layer, so downstream must wait for the **entire previous layer** to complete even if it depends on only one member; diamond dependencies especially | Fast branches get held back by slow, unrelated branches | **Event-driven `advance_dag`**: a node triggers as soon as its **direct upstreams** complete, parallelizing by true dependency |
| 4 | `schedule_node` recursion + `al_schedule_nodes` mutating while traversing edges — fragile logic; leftover `print` debugging | Poor maintainability | DB state machine + topological readiness check, straightforward logic |
| 5 | Progress can only be polled by the frontend (backend doesn't maintain it) | No backend observability/alerting basis | Backend maintains DAG run progress in real time as `completed/total` |
| 6 | No "rerun from failed node" | The whole graph reruns, wasteful | Reset the failed node and its downstream and rerun |
| 7 | `once={'graceful': True}` uses all params as the idempotency key | May deduplicate incorrectly | Idempotency key uses `dag_run_id + node_key` |
| 8 | No conditional branching / no inter-node parameter passing (XCom) | Weak data-pipeline chaining | Edge conditions + context passing (P2) |

**Conclusion**: master's **X6 canvas + `utils/dag.py` + node=template+runner** ports directly to v2.0; the **orchestration engine is replaced with an event-driven DB state machine** (replacing the static Canvas), fixing #1/#2/#3/#5 in one stroke. This is exactly the design in §5.2 of this proposal.

## 2.2 Evaluation of master's frontend DAG (not directly portable, needs a rewrite)

master's entire frontend is based on the **old project's tech stack**, incompatible with v2.0 (Vue3 + Element Plus + JS), and of poor quality in itself:

**Tech-stack incompatibility (must rewrite, cannot copy over)**
- **Mixed UI libraries**: the editor uses **Arco Design** (`a-button`/`icon-play-arrow`), modals use **Ant Design Vue + vben** (`BasicModal`/`useModal`/`Modal`/`Icon ant-design:*`/`Authority`/`a-card`/`a-descriptions`) — two UI kits + two icon sets mixed together, a fractured style. v2.0 should be pure **Element Plus**.
- **TypeScript** (`lang="ts"`) + old-project component aliases (`/@/components/Modal`, `useMessage`, `v-auth`) — v2.0 is JS + the RuoYi system.
- `graph/Node.vue` is written in the **Vue2 Options API**, with a comment even saying "writing it in vue2 feels like it renders faster" (unsubstantiated), which is awkward in a Vue3 project.

**Debugging leftovers / logic issues (the "debugging" you mentioned)**
- `console.log` all over the place, even with `666`/`777` debug markers: `'init data666'`, `'current666'`, `'click777'`, `'init'`, `'updateStatus'`, bare `console.log(res)`… clearly debugging leftovers.
- **Error handling = `console.log('error', res)`**, silent failure, no user feedback whatsoever (no message prompt).
- **Typo bug**: the monitoring modal has `selectedNode.stauts` (should be `status`) → "task status" is always empty.
- `selectedNode` uses `ref('')` (a string) but is used as an object — type confusion.
- `node.setData({...data}); node.setData({...item})` — **two consecutive setData calls** (laying down the old one first, then overwriting), redundant.
- The polling `setInterval` relies on the `res.is_ok` flag to `clearInterval`, with no backoff/timeout fallback.

**Ugly points / UX**
- **Node/status icons use remote Alibaba Cloud CDN images** (`https://gw.alipayobjects.com/...`) — an external dependency that breaks offline/on intranets, loads slowly, and isn't consistent with Element Plus icons.
- The toolbar's **"fit to screen" and "save" use the same `icon-save` icon** (a copy-paste leftover), easily confused.
- "Fit to screen" zoom uses a `1 - graph.zoom()` hack (duplicated in two places, no less); it should just be `graph.zoomToFit()` / `zoomTo(1)`.
- The component menu (stencil) is a `v-show` floating layer at 300px + `z-index:999`, a hacked-together layout rather than a clean sidebar.
- Colors are hardcoded to the Antd palette (`#52c41a`/`#ff4d4f`…), not Element Plus theme variables.
- Dropping in a node immediately triggers `node:added` → auto `nodeClick`+`nodeDbClick` popping the config dialog, a slightly jarring experience.

**Reusable / worth borrowing (only the X6 layer)**
- The `@antv/x6` engine itself + the `flow-graph` canvas configuration (stencil/history/minimap/snapline/connection rules) approach can be referenced.
- The design of "canvas on the left + node info/logs on the right" split-screen run monitoring, adding flowing dashed-line animations to edges in the running state, and pulling node status by `parent_id` — these interaction ideas can be kept.

**Key points for the v2.0 frontend rewrite (pure Element Plus + JS)**
1. Keep only `@antv/x6` + `@antv/x6-vue-shape`; rewrite everything else with Element Plus (toolbar `el-button`, modals `el-dialog`, drawers `el-drawer`, descriptions `el-descriptions`).
2. Use **Vue3 SFC + Element Plus icons** for nodes (drop the Alibaba Cloud CDN images); status colors use theme variables.
3. **The node config drawer reuses the existing task template components directly** (`getTaskComponent(template_code)`, e.g. `DataIntegrationTask.vue`) — the same set as single-task forms.
4. Remove all `console.log`; unify errors via `ElMessage`; fix `stauts`, the double `setData`, the zoom hack, the duplicate icons, etc.
5. Run monitoring: X6 on the left (read-only + status coloring) + node details/logs on the right (reusing the existing detailed-log component); polling with timeout and backoff, DAG final state driven by backend events (in concert with §5.2) rather than purely frontend judgment.
6. The saved graph JSON is slimmed down (storing only node_key/template_code/params/coordinates + edges), not the full contents of X6's raw `toJSON()`.

## 3. Survey of Off-the-Shelf Workflow Components

### 3.1 Backend Orchestration Engines

| Component | Model | Fit | Notes |
|---|---|---|---|
| **Apache Airflow** | Python-defined DAG + Operator, scheduler polling + Executor (Celery/K8s) | Reference its **model and semantics** (DAG run / task instance / XCom / trigger rules / backfill) | Heavy, Python-as-config, brings its own scheduler; introducing it directly would clash with the existing Celery/APScheduler |
| **DolphinScheduler** | DB-stored DAG (process_definition + task_definition + relation) + Master/Worker, visual drag-and-drop | ⭐ **Closest fit for this project**: DB-driven + canvas + distributed workers, Java | Borrow its **data model and canvas interaction**; don't introduce the Java stack |
| **Dagster / Prefect** | Assets/flows (asset/flow), Python decorators | Reference observability, reruns | Skews toward the Python data stack, a self-contained ecosystem |
| **Temporal** | Workflow-as-code (durable execution) | Reference reliability semantics | Heavy, changes the programming model |
| **Argo Workflows** | K8s CRD, YAML DAG | Not applicable (no K8s dependency) | — |
| **n8n / Node-RED** | Node-based low-code, native canvas | Borrow the **node + connection interaction** and trigger nodes | Skews toward integration automation, not batch scheduling |
| **Celery Canvas** (chain/group/chord) | In-code static orchestration | Partially usable | Static, hard to do conditional branching and UI observability; **not the main engine**, only an option for purely linear sub-chains |

**Selection conclusion (backend)**: **Build a lightweight, DB-driven orchestrator in-house** (the model of DolphinScheduler / Airflow), running on top of the existing Celery execution layer. The reasoning matches the connector layer — reuse our own foundation, avoid heavy coupling; DB-stored graph + state makes UI observation, reruns, and backfills easy.

### 3.2 Frontend DAG Canvas — X6 vs Vue Flow detailed comparison (decided: **AntV X6**)

Both are MIT-licensed and both can do a DAG in Vue3, but their design philosophies are opposite: **X6 = a batteries-included graph editing engine** (editing capabilities built in); **Vue Flow = a genuinely Vue3-native flowchart library** (light, but a lot has to be assembled yourself). Comparing item by item against this project's DAG editor's hard requirements:

| Dimension | **AntV X6** | **Vue Flow** |
|---|---|---|
| Rendering | SVG + HTML, its own rendering engine, MVC (data/view separation) | Nodes are Vue components (DOM), CSS transform for zoom; the most "Vue-ish" |
| Vue3 integration | Framework-agnostic, Vue nodes rely on `@antv/x6-vue-shape`; **imperative API** (`graph.addNode`/`graph.on`), data flows through `setData`/`change:data` | **Native Vue3**, nodes = SFC, reactive, `useVueFlow()`; the smoothest DX |
| Build | Written in TS, usable from JS; **Vite needs alias config** (`@antv/x6`, `x6-vue-shape`, a known pitfall) | No special build pitfalls |
| Draggable component panel (Stencil) | ✅ **Built in** | ❌ Implement it yourself (drag+drop) |
| Undo/redo | ✅ **Built in** `graph.history` | ❌ Do it yourself |
| Alignment snapline | ✅ **Built in** | ❌ None (grid snapping only) |
| Minimap/zoom controls | ✅ Built in | ✅ Separate packages `@vue-flow/minimap`/`controls` |
| Box select/clipboard/shortcuts | ✅ Built in | ❌ Mostly do it yourself |
| Ports + connection validation | ✅ Strong (ports/`validateConnection`/magnet rules) | ✅ handles + `isValidConnection` (adequate, needs more wiring) |
| Edge routing/export PNG/SVG/JSON | ✅ Rich + built-in export | Middling; PNG needs external html-to-image |
| Auto layout / cycle prevention | `@antv/layout`; cycle prevention written yourself | External dagre/elkjs; cycle prevention written yourself |
| Size/performance | Larger; more stable on large graphs (thousands of nodes) | Core is light; gets heavier with many DOM nodes (no difference for a task DAG of a few dozen nodes) |
| Ecosystem/cases | AntV (Alibaba), full Chinese and English docs, **many enterprise-grade DAG cases** (peers like DolphinScheduler); **master already uses it** | Growing, good docs, but few enterprise scheduling-class cases |

| **LogicFlow** (DiDi) | Medium | Flowchart framework, BPMN-friendly, Vue3 integration historically a bit rough — not chosen |

**Selection conclusion (frontend): decided on AntV X6.** Reasons:
1. This project's DAG editor's hard requirements — **draggable component panel / undo-redo / alignment lines / minimap / connection validation / runtime coloring** — happen to be all built into X6, whereas Vue Flow would require building basically all of these from scratch; the total effort is **actually less with X6**.
2. **master already runs on X6**, so its structure and interaction can be referenced (though the code stack is incompatible and needs rewriting, see §2.6), and there are many enterprise-grade DAG cases.
3. The node config drawer still uses Element Plus + reuses the existing task template components; X6 is only responsible for the canvas layer, so the awkwardness of "imperative / non-reactive" has limited impact.

**Cost (accepted)**: imperative API, Vite alias config, slight isolation between inside-node and Vue reactivity.
**When to pick Vue Flow instead**: only if you want a minimal editor + ultimate Vue3 maintainability and are willing to write the panel/undo yourself — this project doesn't fall into that case.

Sources at the end of the document.

## 4. Selection Summary

- **Backend**: build a DB-driven orchestrator in-house, reusing Celery + the existing runner; the model borrows from DolphinScheduler/Airflow.
- **Frontend**: **decided on AntV X6** (see the §3.2 comparison) + `@antv/x6-vue-shape`; the canvas uses X6, the rest of the UI is pure Element Plus, and node config reuses the existing "task template component" system (`templates/*.vue`).
- **Not introducing**: heavy engines such as Airflow/Dagster/Temporal/Argo.

## 5. Refactor Plan

### 5.1 Data Model (graph stored by version, the Dify/n8n paradigm)

**Core idea**: the DAG reuses `task` (task_type=2) as a container (scheduling/triggering/alerting/instances all come for free); **the graph is stored as a whole document, by version**, in `dag_graph`, rather than split into node/edge rows. The draft is mutable, the published version is immutable, and formal runs only run the latest published version. Runtime state reuses `task_instance`, with zero new run tables.

Why not split into node/edge rows: the canvas is document-level atomic editing (one drag = one JSON row change); splitting into rows means every save has to diff/upsert a bunch of rows; moreover, an immutable published version **is naturally a run snapshot**, so editing the graph never affects running/historical runs; version rollback/comparison also comes for free. The only cost is low-frequency queries like "which DAGs reference a given template", mitigated with JSON queries or a derived index written at publish time.

```
task                       -- reused, task_type=2 is the DAG container
  ...(scheduling/cron/triggering/alerting/run_queue/retry all reuse ordinary task fields)
  published_version_id  -> dag_graph.id   the currently effective published version (nullable = unpublished, draft only)

dag_graph                  -- graph document, stored by version (the core new table)
  id            PK
  dag_task_id   -> task.id
  version       'draft' | version number (publish timestamp / auto-increment sequence)
  status        draft | published | archived
  graph         JSON  the whole graph:
                {
                  nodes: [{ node_key, name, template_code, params, pos:{x,y},
                            retry, timeout, error_policy:'fail_fast'|'continue' }],
                  edges: [{ source, target, condition? }],
                  viewport: {...}            -- canvas view state (zoom/pan/X6 rendering details)
                }
  remark        release notes
  create_by, create_time
  unique(dag_task_id, version)

dag_node_ref               -- optional derived index (written alongside at publish time), only to speed up "which DAGs reference a given template"
  dag_task_id, version, template_code
```

> A node = `template_code + inline params` (self-contained), **not referencing a standalone task row** (to avoid lifecycle coupling). Templates reuse the existing task template registry (PythonTask/ShellTask/DataIntegrationTask/...).

**Key flows**
- **Editing**: always read/write this DAG's `version='draft'` row (create it if absent); the canvas is `draft.graph`, and dragging = changing this row.
- **Publishing**: validate acyclicity → copy the draft into an immutable `published` version (version=timestamp) → update `task.published_version_id` (and write `dag_node_ref`).
- **Formal run**: run the version pointed to by `published_version_id`; the DAG run instance records `dag_version_id`, so which version ran is traceable.
- **Test run/debug**: run the `draft` directly (without publishing); the run instance is marked source=draft.
- **Rollback**: point `published_version_id` back to some historical published version (or "restore a historical version to draft, then publish"); all versions are kept, roll back anytime.
- **History/comparison**: list versions by `dag_task_id`, view/diff any version.
- **Listing**: the ordinary task list filters `task_type=1`; the DAG list is `task_type=2`, with a dedicated entry.

**Runtime state: reuse `TaskInstance`, zero new tables**
- **DAG run**: one `TaskInstance`, `parent_id=NULL`, `node_id=NULL`, `task_id=dag_task_id`, extended to record `dag_version_id` (which graph version ran) + source (published/draft).
- **Node run**: one `TaskInstance` per node, `parent_id=<DAG run id>`, `node_id=<node_key>`.
- worker/progress/start-end/result/log fields are reused directly; the frontend aggregates all node statuses of one run by `parent_id`.

> Immutable published version = a free run snapshot: a run only needs to record `dag_version_id`, no need to copy the graph again.

**Comparison of three storage approaches (the third was ultimately chosen)**

| | master (graph stuffed into task.params) | split into dag_node/dag_edge rows | **dag_graph version document (adopted)** |
|---|---|---|---|
| Editing | one row, but no versioning | row-split upsert, annoying | draft in one row, atomic ✅ |
| Versioning/rollback | none | must build separately | natural ✅ |
| Run consistency | reading in real time can get messy | must snapshot manually | published version immutable, free snapshot ✅ |
| Template-usage query | hard | easy | somewhat hard (mitigated by derived index `dag_node_ref`) |

### 5.2 Execution Engine (the Orchestrator)

**Event-driven + DB state machine** (not static Celery Canvas orchestration):

```
run_dag(dag_task_id, source='published'|'draft'):
  1. Get the graph: published → the dag_graph pointed to by task.published_version_id; draft → the version='draft' row
  2. Create the DAG run instance (TaskInstance, status=STARTED), record dag_version_id + source
  3. Parse graph.nodes/edges → find root nodes with in-degree 0 → dispatch each one (reusing dispatch.run_task, carrying dag_run_id + node_key)
Node execution (reusing execute_task, the node run instance lands parent_id/node_id):
  4. After a node reaches SUCCESS/FAILURE, call back advance_dag(dag_run_id)
advance_dag(dag_run_id):  # idempotent + row lock to prevent concurrent duplicate dispatch
  5. Lock the DAG run row; read the graph by the version the run recorded + each node's latest status
  6. Find nodes whose "upstreams are all SUCCESS and that haven't been dispatched" → dispatch
  7. If any node is FAILURE: by policy (default fail-fast) mark the DAG run FAILURE, mark downstream SKIPPED
  8. If all are in a terminal state with no failures → DAG run SUCCESS
```

Key points:
- **Fixed graph source**: the run locks `dag_version_id` at startup and parses by that version (the immutable published version) throughout, so editing the graph doesn't affect a running run.
- **Downstream triggering**: add a hook at the end of `executor.execute_task`: if the instance belongs to some DAG run (parent_id is non-null), call `advance_dag`.
- **Parallelism**: `advance_dag` dispatches all ready nodes at once, and Celery executes them concurrently by nature.
- **Idempotency/dedup**: `advance_dag` does `SELECT ... FOR UPDATE` on the DAG run row; before dispatching, it checks whether a node already has an in-progress/completed instance, to avoid re-dispatching the same downstream when multiple upstreams complete simultaneously (diamond dependency).
- **Execution reuse**: a node still runs `execute_task` + `runner.run()` — the **same execution path** as a single task, just passing extra `dag_run_id/node_key` context.

### 5.3 Scheduling / Triggering

- **Manual**: `run_dag_once(dag_task_id)` → create the run → dispatch the root nodes.
- **Scheduled**: reuse the existing APScheduler (`sys_job` + `invoke_target='...dispatch.run_dag'`), the same mechanism as single-task cron.
- **Trigger types** follow `Task.trigger_type` (1 one-off / 2 scheduled), and the DAG container task is `task_type=2`.

### 5.4 Failure Semantics / Retries / Idempotency

- **Node retry**: reuse Celery retries (`retry`/`countdown`), overridable at the node level.
- **DAG failure policy** (`dag`-level config): `fail_fast` (default, one failure terminates, downstream SKIPPED) / `continue` (a failure only blocks its own downstream, other branches continue).
- **Edge trigger rules** (P2, borrowing Airflow trigger_rules): `all_success` (default) / `all_done` / `one_success`.
- **Rerun** (P2): rerun from the failed node/a specified node (resetting only that node and its downstream).

### 5.5 Inter-Node Data Passing (P2, borrowing Airflow XCom)

- The DAG run maintains a `context` (KV, landing in the DAG run instance's extension field or a standalone kv table).
- Key fields of a node's `runner.run()` return value are written into the context; downstream node params support the `${{ node_key.output_field }}` template interpolation, rendered before dispatch.
- ETL scenario: an upstream "extract" produces a table name/path → a downstream "load/transform" references it, chaining into a data pipeline.

### 5.6 Frontend Canvas (AntV X6)

- **Canvas**: X6 + `@antv/x6-vue-shape`; a node = a Vue component (icon + template name + status badge), port connections, connection validation (forbid cycles → DAG validation before submit).
- **Node config**: double-click a node → render the **existing task template component** in a drawer (`getTaskComponent(template_code)`, e.g. DataIntegrationTask.vue) → fully reuse the already-built low-code/built-in form system.
- **Runtime state**: the monitoring view pulls node instances by `parent_id`, colors nodes by status (gray/blue running/green/red), and clicking a node shows that node's logs (reusing the existing detailed logs); a Gantt/topology view can be overlaid.
- **Save**: canvas → `{nodes[], edges[], viewport}` → write the **draft version** (`dag_graph` version='draft'); clicking "Publish" generates the immutable published version.
- **Versions**: the toolbar offers "Publish / Version History / Rollback / Test Run (run the draft)"; run monitoring can optionally view some historical version.
- Vite needs alias config for `@antv/x6`, `@antv/x6-vue-shape` (a known pitfall).

### 5.7 API (added within `module_task_schedule`)

```
# DAG list/container (task_type=2)
GET    /task/dag/list            paginated DAG task list (task_type=2)
POST   /task/dag                 create a DAG (create the task container + an empty draft)
DELETE /task/dag/{id}            delete

# Graph editing (draft)
GET    /task/dag/{id}/draft      read the draft graph (returns an empty graph if none)
PUT    /task/dag/{id}/draft      save the draft (canvas dragging saves here; validates acyclicity)

# Versions (publish/history/rollback)
POST   /task/dag/{id}/publish    validate acyclicity → publish the draft as an immutable version → set as published_version
GET    /task/dag/{id}/versions   version list (draft + each published version)
GET    /task/dag/{id}/version/{ver}   read a version's graph (view/compare)
POST   /task/dag/{id}/rollback/{ver}  rollback: set a historical version as the current published version

# Runs
POST   /task/dag/{id}/run        formal run (run the published_version)
POST   /task/dag/{id}/debug      test run (run the draft, without publishing)
GET    /task/dag/{id}/runs       run history (list of DAG run instances, including the version that ran)
GET    /task/dag/run/{run_id}    all node statuses of one run (aggregated by parent_id)
POST   /task/dag/run/{run_id}/rerun   rerun from the failed/a specified node (P2)
POST   /task/dag/run/{run_id}/stop    terminate (reuse instance stop)
```
Permission bits: `task:dag:list/edit/publish/run` (merged into the existing task scheduling menu).

## 6. Reuse and Minimal Modification Points

| Reuse | Description |
|---|---|
| `execute_task` / runner registry | Node execution is fully reused, **runner unchanged** |
| `TaskInstance` | Both DAG run + node run use it (parent_id/node_id finally come in handy) |
| Celery / dispatch / APScheduler | Dispatching and scheduling are reused |
| Task template components (`templates/*.vue`) | Node config forms are reused |
| Detailed logs / alert hooks / multi-tenancy | Reused |

**Need to add**: `dag_graph` (the graph version document, draft/published) + the optional `dag_node_ref` (derived index), the `task.published_version_id` field, the orchestrator `dag_orchestrator.py` (`run_dag`/`advance_dag`), the advance hook at the end of `execute_task`, DAG/version services·DAOs·controllers, and the frontend X6 canvas + monitoring view.

## 7. Phased Rollout

- **P1 (MVP, ~1.5–2 weeks)**: data model + orchestrator (serial + parallel, fail_fast, no conditional edges) + DAG CRUD/run/monitoring API + X6 canvas (add/remove nodes and connections, node config reusing template components, save, manual run, runtime coloring). Able to run through data pipelines like "MySQL extract → transform → multi-target load".
- **P2 (~1–1.5 weeks)**: conditional edges/trigger rules, rerun from a node, inter-node context passing (XCom-style), scheduled DAGs.
- **P3 (as needed)**: backfill, node-level SLA/alerts, sub-DAGs, versioning and auditing.

## 8. Risks and Trade-offs

- **Duplicate concurrent dispatch**: under a diamond dependency, multiple upstreams complete simultaneously → row lock + idempotency check are a must (already incorporated into `advance_dag`).
- **Worker crash/lost instances**: a node instance stuck in STARTED → needs a timeout sweep (reuse the existing instance sweep or add a heartbeat).
- **Graph validation**: detect cycles at submit time (reject if topological sort fails); validate once more at run time.
- **Graph storage**: adopt the `dag_graph` version document (draft/published), the published version immutable → editing is atomic, runs are consistent, versions are traceable; "which DAGs reference a given template" falls back to the `dag_node_ref` derived index or a JSON query.
- **X6 learning cost**: slightly higher than Vue Flow, but the DAG's built-in capabilities save a lot of later self-development; if rushing a prototype, one could start with Vue Flow and migrate later.
- **What we won't do**: not introduce Airflow/Temporal; not use Celery Canvas as the main orchestration (static, hard to observe).

---

### References
- [AntV X6 — JavaScript Diagramming Library](https://x6.antv.vision/) · [GitHub antvis/X6](https://github.com/antvis/X6)
- [Vue Flow — Vue3 Flowchart Library](https://vueflow.dev/) · [Quickstart & Best Practices](https://dev.to/monsterpi13/vue-flow-quickstart-and-best-practices-482k)
- [LogicFlow Team](https://github.com/Logic-Flow)
- Apache Airflow (DAG / task instance / XCom / trigger rules model), Apache DolphinScheduler (DB-driven + canvas + Master/Worker model) — as backend orchestration model references
