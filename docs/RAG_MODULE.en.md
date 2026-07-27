> [简体中文](RAG_MODULE.md) | **English**

# Knowledge Base (RAG) Module — Design Notes

> This document describes the design and implementation of the `module_rag` Knowledge Base (RAG) as the "knowledge layer" of the AI-native data platform.
>
> Note: This document contains development-phase status analysis / evolution records (such as migration trade-offs versus the legacy Flask ezdata); the module has already landed, and its latest actual form should be taken from the code and the README / [DEPLOY.md](DEPLOY.md).
>
> The core idea is consistent with the DAG: **reuse the mature pipeline already proven on master (extractor / cleaner / splitter / hybrid retrieval / rerank / QA), but replace the two hardcoded foundations (vector store = ES, embedding/rerank = DashScope) with the pluggable abstractions already present in v2.0** (`module_data` vector handler + `module_ai` model management), and align it with FastAPI / async / multi-tenancy / data permissions / unified storage.

---

## 1. Current State (verified against code)

### v2.0 current branch
- There is **no** knowledge base / RAG module, and `web/src/views/rag/` does not exist either. This is a capability that needs to be newly built.
- However, the foundations required for the "knowledge layer" are largely in place:
  - **`api/module_ai/`** — AI model management (`ai_models` table: provider / api_key (AES encrypted) / base_url / model_type / max_tokens …), already with CRUD + data permissions. It can serve as a unified source for embedding / rerank / LLM models.
  - **`api/module_data/handlers/`** — vector store handlers: `chromadb_handler` / `milvus_handler` / `qdrant_handler` / `pgvector_handler`, with a unified base class `vector_base.py:VectorConnector` (delegating to Agno vectordb, providing `similarity_search` / `write` / `query` / `test_connection` / `list_tables`). **This is a multi-vector-store abstraction that master does not have.**
  - **`api/config/env.py:AiSettings/AiConfig`** — LLM environment-variable fallback (`LLM_TYPE/LLM_MODEL/LLM_API_KEY/LLM_URL`), with provider name normalization.
  - **`api/utils/storage_utils.py` + `api/utils/storage/`** — object storage abstraction (local/s3/minio/oss/azure/gcs/cos/oci), already ported. RAG file upload/download can reuse it directly.
  - **Celery** (`CelerySettings`) + **task logging** (`TaskLogSettings`, file/db/es) + **DAG/task scheduling** (`module_task_schedule`). Long-running jobs like document training can run on Celery, and can even be orchestrated as DAG nodes.
  - **Multi-tenancy** (`TenantMixin` automatically stamps `tenant_id`), **data permissions** (`data_scope_sql`), and **APIRouterPro** auto-registers controllers.

### master branch (original ezdata production code, Flask)
The knowledge base module lives in `api/web_apps/rag/`; it is a **lightweight but fully functional** RAG system. The core pipeline (all verified):

| Submodule | Path | Responsibility |
|---|---|---|
| Data models | `rag/db_models.py` | `rag_dataset` (knowledge base) / `rag_document` (document) / `rag_chunk` (chunk, includes QA pairs, linked to datasource/datamodel) / `rag_embedding` (embedding cache, pickled into MySQL) |
| Extraction | `rag/extractor/` | pdf / excel / csv / html / docx / markdown / txt + Notion + web pages (Firecrawl/HttpUrl); optional Unstructured API; `extract_processor.py` dispatches by extension |
| Cleaning | `rag/cleaner/` | control characters / Unicode / URL / email cleaning + Unstructured-series cleaners |
| Splitting | `rag/splitter/text_splitter.py` | `RecursiveCharacterTextSplitter` (chunk_size=1024 / overlap=200) |
| Embedding | `rag/embedding/cached_embedding.py` + `rag/utils.py` | DashScope embedding, md5 hash hits the `rag_embedding` table cache |
| Vector index | `rag/vector_index/es_vector_index.py` | **ES only** (LangChain `ElasticVectorSearch`), supports score_threshold |
| Full-text index | `rag/text_index/es_text_index.py` | **ES only**, full text on the text field + metadata keyword |
| Rerank | `rag/rerank/` | **DashScope only** rerank (`gte_rerank`) |
| Services | `rag/services/` | `rag_service` (training/retrieval core) + dataset/document/chunk, three API services |
| Endpoints | `rag/views/` | dataset / document / chunk (including `/chunk/retrieval` recall test) |
| Frontend | `web/src/views/rag/` | dataset / document / chunk / retrieval, four pages, **Ant Design Vue + jeecg BasicTable** (the whole jeecg stack, not directly portable) |

**Highlight capabilities (worth keeping)**: hybrid retrieval (`retrieval_type: vector / keyword / all`, multi-threaded concurrent recall + content hash dedup), rerank second-pass reordering + dual score thresholds, QA question-answer pairs (`chunk_type='qa'` + exact question_hash hit), data model training (feeding the `datamodel` schema into the knowledge base), recall test page, and Celery-asynchronous document training.

---

## 2. Evaluation of the master implementation (points to fix this time)

| Issue | master current state | Refactoring direction |
|---|---|---|
| **Vector and full text are two ES indices** | `vector_index/` + `text_index/` each build one index, based on LangChain `ElasticVectorSearch` (old ES) | **Upgrade to ES8 native `dense_vector` + kNN**, putting vector + full text **in the same index**, single-engine hybrid retrieval (see §4.1); reuse the connection/client of v2.0's `elasticsearch_handler` |
| **embedding locked to DashScope** | `utils.py` hardcodes `EMBEDDING_TYPE='dashscope'` | Take the embedding model from `module_ai.ai_models` (model_type='embedding'), falling back to `AiSettings`; supports OpenAI/DashScope/local |
| **rerank locked to DashScope** | `rerank/dashscope_rerank.py` | Take the rerank model likewise from `ai_models` (model_type='rerank'); optionally local bge-reranker |
| **embedding cache pickled into MySQL** | the `rag_embedding` table stores binary | **Keep the cache (persistent)** — it saves embedding calls and enables zero-cost reloading when the vector store loses data (see §4.2); just replace pickle with structured storage + a model tag |
| **Config scattered across Flask SYS_CONF** | `config.SYS_CONF[...]` read all over the place | Consolidate into `RagSettings` in `env.py` + the `ai_models` table |
| **Flask synchronous + no multi-tenancy** | synchronous views, no tenant isolation | FastAPI async + `TenantMixin` automatic tenancy + `data_scope_sql` data permissions |
| **Frontend jeecg stack** | Ant Design Vue + jeecg BasicTable/useModal | Rewrite with v2.0's Element Plus + the existing list/dialog paradigm (consistent with the data source / task scheduling pages) |
| **Training flow is a black box** | celery does it all in one shot via `train_document` | Split into an observable pipeline (extract → clean → split → embed → index), with state persisted to `rag_document.status` and logs going through the task-logging framework |

---

## 3. Market research

| Solution | Positioning | Trade-off |
|---|---|---|
| **Dify** | All-in-one LLMOps (knowledge base + Workflow + Agent + plugin marketplace) | Too heavy, and overlaps with this platform's DAG/Agent positioning; do not adopt wholesale, but borrow its "hybrid retrieval + rerank" and document-chunking UX |
| **RAGFlow** | Deep document understanding RAG engine (strong parsing, explainable recall) | Best-in-class document parsing quality (layout/tables); can serve as a **P2 document-parsing enhancement** (treating its parser as an extractor backend), not as the main framework |
| **FastGPT** | Enterprise knowledge-base Q&A + visual Flow | Consistent with this platform's DAG + AiApp philosophy; borrow its QA dataset and recall-test UX |
| **LangChain / LlamaIndex** | Libraries | master already uses LangChain's splitter / Document types; keep this part but do not bind to its vectorstore |

**Conclusion**: **Do not introduce a heavy platform; build a lightweight RAG layer in-house.** The skeleton follows master (already proven in production), making the three points — vector store / embedding / rerank — pluggable, and wiring them to v2.0's existing `module_data` vector handler + `module_ai` model management + Agno. Hybrid retrieval + rerank is standard for RAG in 2026 (Dify/RAGFlow/FastGPT all default to it), so keep the set master has already implemented. Deep document parsing (RAGFlow) is listed as a P2 enhancement.

---

## 4. Selection summary

| Layer | Selection | Notes |
|---|---|---|
| Backend framework | FastAPI + async SQLAlchemy | Consistent with v2.0 |
| New module | `api/module_rag/` (standard controller/service/dao/entity layering) | Auto-registered by APIRouterPro |
| **Vector store + full-text store** | **ES8 (primary)** — `dense_vector` (kNN/HNSW) + BM25 hybrid in the same store | Reuse the `elasticsearch_handler` connection; one ES set doubles as logs / vectors / data services |
| Vector store (alternative) | `module_data` `VectorConnector` (Agno): Milvus/Qdrant/PgVector/Chroma | Point at different data_sources via `dataset.vector_source_id`; the interface is abstracted, so it can be swapped later |
| Embedding / Rerank | `module_ai.ai_models` (model_type=embedding/rerank) + `AiSettings` fallback | Multi-provider, keys AES-encrypted |
| **Embedding cache** | Persistent table `rag_embedding` (hash+model → vector) | Save calls + disaster-recovery reload; optional Redis hot layer |
| Document extraction | Port master `extractor/` (P1); RAGFlow parser (P2) | File sources go through `storage_utils` |
| Splitting / cleaning | Port master `splitter/` + `cleaner/` (keep the LangChain splitter) | chunk_size/overlap driven by a document-level `chunk_strategy` |
| Async training | v2.0 Celery + task-logging framework | Document state machine + observable logs |
| Frontend | Vue3 + Element Plus (aligned with the data source / task pages) | Rewrite the four pages |
| AI integration | Knowledge base as an Agno `Knowledge` / Agent tool | AiApp attaches a knowledge base, RAG retrieval as a tool |

### 4.1 One ES8 set, three uses (logs / vector store / data services)

A single ES8 cluster simultaneously serves three roles, with indices isolated from one another and never crossing:

| Role | Index | Current state | RAG change |
|---|---|---|---|
| **Log storage** | `task_logs` (`task_es_*` config) | In use (`task_logger` / `es_log_dao`) | Unchanged |
| **Data services (data sources)** | User-owned indices | In use (`elasticsearch_handler`, query/scan/bulk) | Unchanged |
| **Vector + full-text store (RAG)** | One `rag_ds_{dataset_id}` per knowledge base | New | See below |

**Why choose ES8 as the vector store rather than PgVector/Milvus**: (1) this stack already depends on ES (logs, data sources), so no new component is introduced; (2) ES8 natively provides `dense_vector` + kNN (HNSW) + BM25, so **vector recall and keyword recall happen in the same engine and the same index**, making hybrid retrieval natural; (3) it keeps the operations surface tight. The cost is concentrated single-point pressure (see §8 Risks).

**Index design** (one index per knowledge base, with dimensions dictated by its embedding model, which is why it must be per-dataset rather than shared):
```jsonc
PUT rag_ds_{dataset_id}
{
  "mappings": {
    "properties": {
      "content":        { "type": "text", "analyzer": "ik_max_word" },   // BM25 full text (for Chinese, install the ik tokenizer)
      "content_vector": { "type": "dense_vector", "dims": <embedding dimension>,
                          "index": true, "similarity": "cosine",
                          "index_options": { "type": "hnsw", "m": 16, "ef_construction": 100 } },
      "tenant_id":   { "type": "keyword" },   // multi-tenant isolation filter
      "document_id": { "type": "keyword" },   // delete by document
      "chunk_id":    { "type": "keyword" },
      "chunk_type":  { "type": "keyword" },   // chunk / qa
      "question":    { "type": "text" },
      "meta":        { "type": "object", "enabled": false }
    }
  }
}
```

**Writing**: `elasticsearch.helpers.bulk` batch upsert (`_id`=chunk_id), with vectors coming from the §4.2 cache or computed on the fly.
**Delete by document**: `delete_by_query { term: document_id }`.
**Hybrid retrieval (single request)**: one `_search` carrying both `knn` (vector) and `query` (BM25), each with `filter: [tenant_id, within dataset]`:
```jsonc
POST rag_ds_{id}/_search
{ "knn":   { "field": "content_vector", "query_vector": [...], "k": 50, "num_candidates": 200,
             "filter": { "term": { "tenant_id": "100" } } },
  "query": { "bool": { "must": { "match": { "content": "user question" } },
                       "filter": { "term": { "tenant_id": "100" } } } },
  "size": 50 }
```
> **License note**: ES's built-in RRF fusion (`retriever`/`rank.rrf`) requires a **Platinum/Enterprise** license. On the free basic edition, kNN, `dense_vector`, and BM25 are all free, so **fusion is done at the application layer** (recall each independently → RRF/score-normalized dedup → rerank → top_k), which conveniently reuses master's existing `get_knowledge` logic of "multi-threaded vector + full text → content hash dedup", with zero license dependency.
> **Dimension limit**: ES8 `dense_vector` caps at 4096 dimensions; common embeddings (1024/1536/3072) all fit.

### 4.2 Embedding cache (cost savings + disaster-recovery reload)

Keep master's caching idea, but make it persistent, structured, and model-tagged:

- Table `rag_embedding`: `hash` (md5 of content) + `model_id` jointly unique → `vector` (JSON array / native array on PG) + `dim` + `created_at`.
- **When embedding**: first look up the cache by `(model_id, hash)`; a hit skips the model call → saves money, speeds things up, and dedups identical text naturally.
- **Disaster recovery / migration**: if the ES index is corrupted, or for anything other than changing the embedding model (scaling out, changing HNSW parameters, migrating the vector store), you can directly **bulk-reload ES from `rag_chunk` + `rag_embedding` without calling the embedding model at all**.
- Optionally use Redis as a hot layer (key=`emb:{model_id}:{hash}`), with the DB still the source of truth.

---

## 5. Refactoring plan

### 5.1 Data models (`api/module_rag/entity/do/rag_do.py`)
Follow master's three main tables, drop the pickle cache table, and uniformly add `TenantMixin`:

- **`rag_dataset`** (knowledge base): `id` / `name` / `description` / `embedding_model_id` (points to ai_models) / `vector_source_id` (points to data_source, i.e. the vector-store connection) / `index_name` / `built_in` / `status` / Tenant + audit fields.
  - **Key decision**: each knowledge base is **bound to one embedding model + one vector-store connection** (the vector dimension is determined by the embedding model, and the embedding cannot be changed after the base is built, consistent with Dify).
- **`rag_document`** (document): `id` / `dataset_id` / `document_type` (upload_file / notion / website / datamodel) / `name` / `status` (1 pending training, 2 training, 3 success, 4 failed) / `meta_data` (JSON, stores the source: file_key / url / notion_id / datamodel_id) / `chunk_strategy` (JSON: chunk_size / overlap / cleaning rules) / `error` (failure reason) + Tenant.
- **`rag_chunk`** (chunk): `id` / `dataset_id` / `document_id` / `chunk_type` ('chunk' / 'qa') / `content` / `question` / `question_hash` / `answer` / `hash` (content dedup) / `position` / `status` / `star_flag` + Tenant. (`chunk_id` is the ES `_id`, so no separate vector_id column is needed.)
- **Keep `rag_embedding`** (see §4.2): `hash` + `model_id` unique → `vector` + `dim`. Its purpose is to save embedding calls + reload at zero cost when ES loses data.

> Unlike the DAG where "graphs are stored per version", knowledge bases do not need versioned documents; but `chunk_strategy` lives at the document level, making it easy to retrain per document. `rag_chunk` + `rag_embedding` together form the "rebuildable source of truth" for the ES index.

### 5.2 Training pipeline (`service/rag_train_service.py`, Celery async)
Document training is split into 5 observable steps, each updating `rag_document.status` and writing a task log:

```
1. extract  extract    —— storage_utils downloads the file → extractor parses by type → raw text/tables
2. clean    clean       —— CleanProcessor removes noise
3. split    split       —— RecursiveCharacterTextSplitter (per chunk_strategy) → chunks
4. embed    vectorize   —— take the model for dataset.embedding_model_id (Redis cache) → vectors
5. index    index        —— VectorConnector.write writes to the vector store + full-text index; chunks land in rag_chunk
```
- The entry point `train_document(document_id)` is dispatched to Celery by the controller via `apply_async`; on failure status=4 and `error` is recorded.
- `train_datamodel(dataset_id, datamodel_id)`: converts the data model's schema/samples to text and feeds the base (porting master's logic).
- QA: `train_qa(dataset_id, question, answer)` → `chunk_type='qa'`, and an exact question_hash hit takes the shortcut.

### 5.3 Retrieval / recall (`service/rag_retrieval_service.py`)
Port and enhance master's `get_knowledge` / `query_knowledge`:
- Inputs: `query` / `dataset_ids[]` / `top_k` / `retrieval_type` (vector / keyword / hybrid) / `score_threshold` / `rerank` (bool) / `rerank_score_threshold`.
- **hybrid**: concurrent vector recall + full-text recall → dedup by content hash → (optionally) rerank → filter by score threshold → take top_k.
- **QA shortcut**: on a question_hash hit, return the starred answer directly.
- The rerank model is taken from `ai_models` (model_type='rerank').
- Returns `{total, records:[{content, chunk_id, dataset_id, document_id, score, ...}]}`, shared by the recall-test page and the Agent tool.

### 5.4 Vector store / embedding / rerank abstraction wiring
- **Vector store (primary: ES8)**: reuse `elasticsearch_handler`'s connection config/client, and add an `EsVectorStore` layer on the `module_rag` side (build index mapping, bulk upsert, kNN+BM25 retrieval, delete by document_id); see §4.1. Each dataset has its own index `rag_ds_{dataset_id}`.
- **Vector store (alternative)**: if `dataset.vector_source_id` points to a non-ES data_source, go through `module_data`'s `VectorConnector` (Milvus/Qdrant/PgVector/Chroma). The retrieval interface is unified, so the upper layer is unaware of the backend.
- **embedding**: `AiUtil.get_embedding_model(model_id)` (new, analogous to the existing `get_model_from_factory`), with the provider coming from ai_models; if none, fall back to `AiSettings`. Before embedding, check the `rag_embedding` cache (§4.2).
- **rerank**: same as above, `get_rerank_model(model_id)`.
- Dimension validation: at build time, write the embedding dimension into the dataset and the ES mapping `dims`; thereafter the embedding model for that base cannot be changed (changing it requires rebuilding the index).

### 5.5 Integration with the AI layer (P2)
- The knowledge base can be injected into an Agent as an **Agno `Knowledge`**, or exposed as the Agent's "knowledge retrieval" tool (calling the §5.3 retrieval interface).
- AiApp (if ported) gains an "associated knowledge base" config (`dataset_ids`), retrieving first and then generating during conversation (RAG).

### 5.6 Frontend (Element Plus rewrite)
Aligned with the list + drawer/dialog paradigm of the data source / task scheduling pages, four pages:
- **Knowledge base list** `views/rag/dataset/`: CRUD; when building a base, select an embedding model + a vector-store connection.
- **Document management** `views/rag/document/`: upload files / enter a web URL / choose a data model; the train button triggers async training + status polling (pending training / training / success / failed); on failure, view the error.
- **Chunk management** `views/rag/chunk/`: view/edit/delete chunks, star them, manually add QA pairs.
- **Recall test** `views/rag/retrieval/`: enter a query + retrieval parameters (top_k / mode / threshold / rerank), and display hit chunks + scores (reusing the §5.3 interface).

### 5.7 API (`api/module_rag/controller/`, prefix `/rag`)
```
# Knowledge base
GET    /rag/dataset/list           list (task permission rag:dataset:list)
POST   /rag/dataset                create
PUT    /rag/dataset/{id}           edit
DELETE /rag/dataset/{ids}          delete (along with chunks + vector-store collection)

# Document
GET    /rag/document/list          list (filter by dataset_id)
POST   /rag/document               create (upload/URL/datamodel)
DELETE /rag/document/{ids}         delete
POST   /rag/document/{id}/train    trigger training (async)
GET    /rag/document/{id}/status   training status polling

# Chunk
GET    /rag/chunk/list             list
POST   /rag/chunk                  create/edit (including QA)
DELETE /rag/chunk/{ids}            delete
POST   /rag/chunk/{id}/star        star

# Recall
POST   /rag/retrieval              recall test / Agent retrieval entry point
```
Permission points: `rag:dataset:*` / `rag:document:*` / `rag:chunk:*` / `rag:retrieval`. The menu hangs under "Data Management" or as a new top-level "Knowledge Base" menu (seeded via `ezdata.sql` / `ezdata-pg.sql` just like the DAG).

---

## 6. Reuse and minimal-change points

| Source | What to reuse | Change |
|---|---|---|
| master `rag/extractor/` | the whole set of extractors (pdf/excel/csv/html/docx/md/txt/notion/web) | Remove Flask config, switch the file source to `storage_utils`; keep LangChain Document |
| master `rag/cleaner/` `rag/splitter/` | cleaning + recursive splitting | Basically copied over, with parameters driven by `chunk_strategy` |
| master `rag/services/rag_service.py` | training + hybrid retrieval + rerank + QA algorithms | Split the service, make it async, wire it to the abstraction layer |
| v2.0 `elasticsearch_handler` | ES connection config/client/bulk/scan (primary vector store) | Add a `dense_vector` mapping + kNN retrieval (`EsVectorStore`) |
| v2.0 `module_data` vector handler | alternative vector stores (Milvus/Qdrant/PgVector/Chroma) | RAG collection naming / batch upsert (alternative path only) |
| v2.0 ES logs (`task_es_*`) | same ES cluster, validating the connection/auth paradigm | Reuse the config approach; RAG uses a separate index |
| v2.0 `module_ai` | embedding/rerank/LLM model source | Add `get_embedding_model` / `get_rerank_model` |
| v2.0 `storage_utils` | file storage/retrieval | Use directly |
| v2.0 Celery + task logging | async training + observable logs | Use directly |
| v2.0 multi-tenancy / data permissions / APIRouterPro | isolation + auth + routing | Use directly |

---

## 7. Phased rollout

- **P0 skeleton + ES validation**: `module_rag` layering + three-table DDL (`ezdata.sql` / `ezdata-pg.sql`, including `rag_embedding`) + dataset CRUD + menu/permission seed. **First get the minimal loop running on ES8 with `EsVectorStore`: build mapping → bulk write vectors → kNN+BM25 → delete** (see §8).
- **P1 training + retrieval loop**: port extractor/cleaner/splitter; wire embedding to `module_ai`; Celery async training + state machine; hybrid retrieval + rerank; recall test page. **End-to-end: build base → upload document → train → recall.**
- **P1.5 four frontend pages**: Element Plus rewrite, status polling.
- **P2 enhancements**: multiple selectable vector stores (Milvus/Qdrant/ES); QA datasets; data model training; RAGFlow deep parsing as an optional extractor backend; Redis embedding cache.
- **P3 AI integration**: attach the knowledge base to an Agno Agent / AiApp; RAG conversation.

---

## 8. Risks and trade-offs

- **Embedding dimension bound to the vector store**: changing the embedding model requires rebuilding the index (ES `dims` is fixed). Lock the embedding at build time, and clearly indicate this in the UI (consistent with Dify).
- **Single-point pressure of one ES set, three uses**: high-frequency log writes + vector kNN (CPU/memory intensive) + data source queries all crammed into the same cluster may interfere with each other. Mitigation: RAG uses a separate index, and when necessary a dedicated ES node/sharding strategy; for production it is recommended to at least separate logs and vectors into different index shards, and later possibly separate clusters. **This is the trade-off of exchanging "one fewer component" for "single-point blast radius"; the ES specs need to be confirmed with operations.**
- **ES8 version and license**: requires ES **8.x** (`dense_vector`+kNN); built-in RRF fusion requires Platinum, and this plan avoids it by doing fusion at the application layer (§4.1). For Chinese full-text search it is recommended to install the ik tokenizer plugin.
- **EsVectorStore is new code**: master uses the old `ElasticVectorSearch`, and ES8's native kNN syntax is different. **P0 must first validate with a small index: build mapping → bulk write vectors → kNN+BM25 retrieval → delete_by_query, get it working before rolling out.**
- **Document parsing quality**: master's extractor is mediocre for complex PDFs/tables; P2 introduces RAGFlow parsing or Unstructured as an optional backend.
- **Large-file training time / worker blocking**: run on Celery asynchronously, embedding long documents in batches; note that this does not conflict with dlt's single-worker constraint (see [[connector-engine-strategy]]) — RAG training can use its own queue.
- **Celery prefork incompatible with some libraries' fork**: if the embedding/parsing libraries have fork issues, handle it as with the DAG/dlt's `WORKERS=1`.
- **Multi-tenant vector isolation**: put the tenant in the collection name or filter by in-store metadata to avoid cross-tenant recall.
- **Cost**: embedding/rerank calls are billed; the Redis cache + question_hash shortcut reduce cost.

---

### References
- Dify hybrid retrieval + Rerank: https://dify.ai/blog/hybrid-search-rerank-rag-improvement
- Open-source Agent/RAG platform comparison (n8n/Dify/RAGFlow/Coze): https://jimmysong.io/blog/open-source-ai-agent-workflow-comparison/
- Dify vs RAGFlow: https://slashdot.org/software/comparison/Dify-vs-RAGFlow/
- master source: `api/web_apps/rag/` (db_models / extractor / cleaner / splitter / embedding / vector_index / text_index / rerank / services / views)
- v2.0 foundations: `api/module_ai/`, `api/module_data/handlers/` (vector_base + chroma/milvus/qdrant/pgvector), `api/utils/storage_utils.py`, `api/config/env.py` (AiSettings)
