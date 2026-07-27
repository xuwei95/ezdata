> [简体中文](skill-agent-optimization.md) | **English**

# Design Doc: Built-in Skills + Skill×Data Binding — Slimming Down the Agent's Resident Context

> Status: Draft / Pending review
> Scope: `module_ai` (conversational agent assembly, Skills), `module_data` (datasource/model metadata, read-only)
> Reference: Anthropic's "How Anthropic enables self-service data analytics with Claude" — knowledge-type/process-type Skills, funnel-style progressive disclosure, "no Skill 21% → with Skill 95%+".

---

## 1. Background & Problem

Every turn of an ordinary conversation currently **injects three blocks into the context unconditionally**, and more than half of that is "conditional knowledge paid for in full every single turn":

| Source | Content | Injection timing | Estimate |
|---|---|---|---|
| `ai_chat_service._DATA_AGENT_INSTRUCTIONS` | Data-retrieval flow + chart routing + ES pitfalls + task/cron rules | **Resident every turn** | ~900–1100 tok |
| `data_agent_tools.build_data_catalog()` | Datasources + list of already-modeled tables | **Resident every turn** | hundreds ~1K+ (scales with source count) |
| `skill_tools.build_skill_catalog()` | code + name + description of every enabled skill | **Resident every turn** | grows linearly with skill count |
| Tool schemas (`plot_chart`/`run_datasource_query` docstrings) | Chart/retrieval usage | Every turn, with tool definitions | the plot_chart section alone is quite long |

**Core problem**: `_DATA_AGENT_INSTRUCTIONS` mixes the "indispensable core flow" together with "conditional topics (charting, ES, task/cron creation)" in a single constant. When a user merely asks "how did Kweichow Moutai move today", not one of the cron rules, chart routing, or the ES `.keyword` pitfall is of any use — yet all of it is paid for in full every turn.

**At the same time**: the freshly landed Skill system and the data are **loosely coupled** — a skill has no idea "which datasource/model it serves", while the data-side hard-won knowledge instead piles up in a resident mega-instruction, never going through the Skill on-demand channel.

## 2. Goals / Non-goals

**Goals**
1. Split the conditional topics out of `_DATA_AGENT_INSTRUCTIONS` into **built-in Skills**, loaded on demand via `load_skill`, keeping only the core resident.
2. Let Skills **bind to datasources**, so a knowledge-type skill is only surfaced when the relevant source enters scope (rather than dumping all of them in mindlessly).
3. Priority of benefits: **focus/accuracy > maintainability > saving tokens** (see §7 Trade-offs).

**Non-goals (out of scope this round)**
- Semantic/metrics layer (compiled metrics) — separate project.
- Eval harness (offline eval + correction harvesting) — separate project.
- Binary resources / sandbox filesystem — constrained by the sandbox; stick with "scripts as text".

## 3. Design Principles (following the article)

- **Funnel-style progressive disclosure**: keep only the "scope-narrowing" core resident; pull details on demand.
- **Two kinds of Skill**:
  - **Process-type (process)**: the standard steps of a single query/task-creation + reusable analysis patterns. Globally applicable → resident in the L1 directory.
  - **Knowledge-type (knowledge)**: the definitions, pitfalls, and dedicated retrieval methods of a given datasource/domain. **Bound to a datasource** → surfaces only when that source is touched.
- **Built-in Skills (`built_in=1`)**: shipped out of the box, non-deletable, code-locked; content can be tweaked.

## 4. Architecture

### 4.1 Three-layer structure (after refactor)

```
Resident (every turn):
  ├─ build_data_catalog()                # datasource/table directory (for narrowing, kept)
  ├─ _DATA_AGENT_INSTRUCTIONS (slimmed)  # only the core funnel flow remains ~150 tok
  └─ build_skill_catalog()               # lists only process-type + scope-matched knowledge-type
On demand (triggered by load_skill):
  ├─ chart_building / task_scheduling / es_query …  (body of built-in process/knowledge skills)
  └─ body of per-source knowledge skills + attached files (read_skill_file)
```

### 4.2 Skill × Data binding rules

| Skill type | Enters L1 directory? | How it becomes discoverable |
|---|---|---|
| Process-type (process) | **Always** | resident directory |
| Knowledge-type (knowledge) + bound source | **Only when a bound source ∈ current scope** | ① the app has bound that source; ② the return of `search_datasource_knowledge(that source)` appends "skill X available for this source, you may load_skill('X')" |

- **Ordinary conversation** (scope = all): knowledge-type skills **do not mindlessly enter the directory**; instead, after the agent calls `search_datasource_knowledge(source)` to identify the source, the return incidentally informs it that "this source has a dedicated skill". This way, as the skill count grows the resident directory does not bloat, and the moment of discovery fits the funnel (identify the source first → then grab that source's dedicated operating manual).
- **App conversation** (scope = the few bound sources): the knowledge-type skills of those sources enter the directory directly.

### 4.3 Built-in Skill list

| code | type | moved from | when it gets loaded |
|---|---|---|---|
| `data_query_flow` | process | retrieval funnel core + reusable analysis patterns (retention/funnel/period-over-period) | during complex analysis; core steps still stay resident |
| `chart_building` | process | current section 3.5: plot_chart vs code routing + native rules | when the user wants a chart |
| `task_scheduling` | process | task propose flow + the full 7-section Quartz cron rules | when the user wants to create/modify a task |
| `es_query` | knowledge (by source type) | ES's `.keyword`/size/Top-N pitfalls | when the target source is ES |
| `<source>_guide` | knowledge (by source) | per-source/per-domain definitions and dedicated retrieval methods (configure 1 for the demo finance case first) | when that source enters scope |

> After the split, `_DATA_AGENT_INSTRUCTIONS` retains only: the role definition + the main flow "look up a recipe first → check the structure → retrieve data" + one line "when you need chart/task/ES details, load_skill the corresponding skill first". The resident drops from ~1K to ~250 tok.

## 5. Data model changes (`ai_skill`)

Two new columns (mysql + pg + ALTER on the running DB):

| Column | Type | Description |
|---|---|---|
| `skill_type` | varchar(20) default 'process' | 'process' process-type / 'knowledge' knowledge-type |
| `datasource_codes` | varchar(500) | datasource codes bound to a knowledge-type skill (comma-separated); empty = not bound |

- Reuse existing: `content` (SKILL.md), `resources` (attached files), `ref_skills` (soft references), `built_in`, `status`.
- The VO gets `skill_type` / `datasource_codes` in sync; the frontend SkillEditor's basic-info section gets a "type" dropdown + an "associated datasources" multi-select (shown only for knowledge-type).

## 6. Assembly logic changes

### 6.1 `AiSkillService.resolve_agent_skills(db, skill_ids, *, scope_codes=None)`
- Adds the `scope_codes` parameter (datasource codes the current conversation can access).
- Each skill dict gains `skill_type` / `ds_codes`; the `catalog` decision changes to:
  - process → `catalog=True`
  - knowledge → `catalog = bool(set(ds_codes) & set(scope_codes or []))` (ordinary conversation passes scope None → knowledge-type catalog=False, surfaced via §6.3)
- The BFS soft-reference expansion logic is unchanged (referenced ones still have `catalog=False` but remain loadable).

### 6.2 `build_skill_catalog(skills)`
- Unchanged (already filtered by `catalog`). Grouped display is optional: `### Process skills` / `### Datasource-dedicated skills`.

### 6.3 `search_datasource_knowledge(datasource_code, query)` (data_agent_tools.py)
- Append a section at the end: if the source has enabled skills with `skill_type='knowledge'` bound to this source → "dedicated skills available for this datasource: X —— load_skill('X') to get the operating manual".
- This way, in ordinary conversation a knowledge-type skill "surfaces as soon as the source is identified", with no need to be resident.

### 6.4 `_build_agent` / `chat_services`
- Pass `datasource_scope` as `scope_codes` into `resolve_agent_skills`.
- Swap `_DATA_AGENT_INSTRUCTIONS` for the slimmed-down constant.

## 7. Token accounting & trade-offs (align expectations carefully)

- **The savings are real**: simple queries dominate; moving out the chart/task/es three packs saves ~700 tok on every one of those turns.
- **Offset 1 — one extra hop**: when that knowledge pack is needed, +1 `load_skill` round-trip. Net benefit depends on the traffic mix (lots of querying, few task creations → worthwhile).
- **Offset 2 — prompt caching**: if Anthropic prompt caching is in effect, a large resident instruction is nearly free within a session, weakening the money-saving motive. **Confirm whether caching is enabled before landing this** (currently only disabling parallel tool calls is confirmed; caching is unknown).
- **The sure-win benefits (unaffected by caching)**:
  - **Focus/accuracy**: the model no longer has to read the cron/ES rules every turn, so its attention stays concentrated (the mechanism behind the article's 21%→95% is "narrowing the search space", not saving money).
  - **Maintainability**: change chart/cron rules in one skill without touching a giant constant; they can also be edited in the UI, imported/exported, and bound on demand by apps.

> Conclusion: the **primary selling point of this proposal is focus + maintainability**; tokens are incidental and conditional. During review, do not treat "how much money it saves" as the sole KPI.

## 8. Phased rollout

**Phase 1 (minimal, safest, validate value first) — extract `task_scheduling`**
- The fattest, least-used, most independent one (decoupled from the retrieval flow).
- Only do: create the built-in skill `task_scheduling` (move the cron/propose sections) → delete the corresponding sections from `_DATA_AGENT_INSTRUCTIONS` → the model can load on demand from the catalog.
- No schema change needed (process-type, not source-bound). Validate: task-creation conversations still work (the model does load_skill('task_scheduling') first, then propose); ordinary query turns have a noticeably shorter resident.

**Phase 2 — extract `chart_building`, add schema**
- Move out the chart-routing section; also slim the `plot_chart` docstring (details move into the skill, the tool description keeps only the signature + one line).
- Add the `skill_type` column.

**Phase 3 — knowledge-type + data binding**
- Add the `datasource_codes` column; `es_query` + the demo finance `<source>_guide`; append the surfacing logic to `search_datasource_knowledge`; add the `scope_codes` filter to `resolve_agent_skills`; add the type/associated-source UI to SkillEditor.

## 9. Risks & rollback

| Risk | Mitigation |
|---|---|
| The model doesn't proactively load the right skill, so what should have been loaded isn't (e.g. missing cron rules → garbage output) | Write the trigger conditions fully in the catalog description; the slimmed core instruction keeps one line "before creating a task/chart you MUST load the corresponding skill first"; observe hit rate in the small Phase 1 scope first |
| Extra hop adds latency | Only make low-frequency topics (task/chart) on-demand; keep the high-frequency retrieval core resident |
| Built-in skill deleted/broken by mistake | `built_in=1` is non-deletable, code-locked; body edits are rollback-able (export a backup) |
| Built-in skill content drifts from the code rules | Following the article's "staleness prevention": later fold built-in skills into seed/versioning; change the skill in sync when changing the related rules (relying on convention for now) |

**Rollback**: each Phase is independent; write the extracted sections back into `_DATA_AGENT_INSTRUCTIONS` and disable the corresponding built-in skill to restore.

## 10. Validation

- **Resident size**: compare the character/tok count of the system section for one ordinary query request before and after the refactor.
- **Functional regression** (fallback model modelId=0):
  - Task creation: "grab X once a day at 9am" → the model does `load_skill('task_scheduling')` → propose, with cron being `0 0 9 * * ? *`.
  - Charting: "draw the trend over the past year" → `load_skill('chart_building')` → correctly routes between plot_chart/code.
  - ES source: terms aggregation goes through `.keyword` (after loading `es_query`).
  - Ordinary query: "how did Kweichow Moutai move today" → none of the above skills is triggered, the resident is shorter.
- **Accuracy** (once eval exists): run a before/after comparison for the task-creation and charting categories.

## 11. Follow-ups (beyond the scope of this doc, listed as next directions)

- Semantic/metrics layer (the layer the article trusts most): a named metric = definition + bound model, which the agent prefers to use.
- Eval harness: offline QA set + ⭐favorites/conversational corrections → eval samples; provenance annotated in the footer.
- Optional adversarial-review sub-agent (+6% accuracy / +32% tok / +72% latency, built as a high-risk toggle).
