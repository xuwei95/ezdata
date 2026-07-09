# 知识库(RAG)模块 设计说明

> 本文描述 `module_rag` 知识库(RAG)的设计与实现,作为 AI 原生数据平台的「知识层」。
>
> 注:本文含开发期的现状分析/演进记录(如与旧版 Flask ezdata 的迁移取舍);模块已落地,最新实际形态以代码与 README / [DEPLOY.md](DEPLOY.md) 为准。
>
> 核心思想与 DAG 一致:**复用 master 已跑通的成熟链路(extractor / cleaner / splitter / 混合检索 / rerank / QA),但把被写死的两处底座(向量库=ES、embedding/rerank=DashScope)换成 v2.0 已有的可插拔抽象**(`module_data` 向量 handler + `module_ai` 模型管理),并对齐 FastAPI / async / 多租户 / 数据权限 / 统一存储。

---

## 1. 现状(代码已核实)

### v2.0 当前分支
- **没有** 知识库 / RAG 模块,`web/src/views/rag/` 也不存在。这是一块需要新建的能力。
- 但「知识层」所需的底座已基本就位:
  - **`api/module_ai/`** —— AI 模型管理(`ai_models` 表:provider / api_key(AES 加密) / base_url / model_type / max_tokens …),已有 CRUD + 数据权限。可作为 embedding / rerank / LLM 模型的统一来源。
  - **`api/module_data/handlers/`** —— 向量库 handler:`chromadb_handler` / `milvus_handler` / `qdrant_handler` / `pgvector_handler`,统一基类 `vector_base.py:VectorConnector`(委托 Agno vectordb,提供 `similarity_search` / `write` / `query` / `test_connection` / `list_tables`)。**这是 master 所没有的多向量库抽象。**
  - **`api/config/env.py:AiSettings/AiConfig`** —— LLM 环境变量兜底(`LLM_TYPE/LLM_MODEL/LLM_API_KEY/LLM_URL`),provider 名归一化。
  - **`api/utils/storage_utils.py` + `api/utils/storage/`** —— 对象存储抽象(local/s3/minio/oss/azure/gcs/cos/oci),已移植。RAG 文件上传下载可直接复用。
  - **Celery**(`CelerySettings`)+ **任务日志**(`TaskLogSettings`,file/db/es)+ **DAG/任务调度**(`module_task_schedule`)。文档训练这类长耗时作业可走 Celery,甚至可作为 DAG 节点编排。
  - **多租户**(`TenantMixin` 自动盖 `tenant_id`)、**数据权限**(`data_scope_sql`)、**APIRouterPro** 自动注册控制器。

### master 分支(原版 ezdata 生产代码,Flask)
知识库模块在 `api/web_apps/rag/`,是一套**轻量但功能完整**的 RAG 系统。核心链路(均已核实):

| 子模块 | 路径 | 职责 |
|---|---|---|
| 数据模型 | `rag/db_models.py` | `rag_dataset`(知识库)/ `rag_document`(文档)/ `rag_chunk`(分段,含 QA 对、关联 datasource/datamodel)/ `rag_embedding`(embedding 缓存,pickle 存 MySQL) |
| 抽取 | `rag/extractor/` | pdf / excel / csv / html / docx / markdown / txt + Notion + 网页(Firecrawl/HttpUrl);可选接 Unstructured API;`extract_processor.py` 按扩展名分发 |
| 清洗 | `rag/cleaner/` | 控制字符 / Unicode / URL / 邮箱清理 + Unstructured 系列清洗器 |
| 切分 | `rag/splitter/text_splitter.py` | `RecursiveCharacterTextSplitter`(chunk_size=1024 / overlap=200) |
| Embedding | `rag/embedding/cached_embedding.py` + `rag/utils.py` | DashScope embedding,md5 hash 命中 `rag_embedding` 表缓存 |
| 向量索引 | `rag/vector_index/es_vector_index.py` | **仅 ES**(LangChain `ElasticVectorSearch`),支持 score_threshold |
| 全文索引 | `rag/text_index/es_text_index.py` | **仅 ES**,text 字段全文 + metadata keyword |
| Rerank | `rag/rerank/` | **仅 DashScope** rerank(`gte_rerank`) |
| 服务 | `rag/services/` | `rag_service`(训练/检索核心)+ dataset/document/chunk 三个 API service |
| 接口 | `rag/views/` | dataset / document / chunk(含 `/chunk/retrieval` 召回测试) |
| 前端 | `web/src/views/rag/` | dataset / document / chunk / retrieval 四页,**Ant Design Vue + jeecg BasicTable**(整套 jeecg 体系,不可直接移植) |

**亮点能力(值得保留)**:混合检索(`retrieval_type: vector / keyword / all`,多线程并发召回 + content hash 去重)、rerank 二次重排 + 双重 score 阈值、QA 问答对(`chunk_type='qa'` + question_hash 精确命中)、数据模型训练(把 `datamodel` 的 schema 灌进知识库)、召回测试页面、文档训练 Celery 异步化。

---

## 2. master 实现评估(本次应修掉的点)

| 问题 | master 现状 | 重构方向 |
|---|---|---|
| **向量、全文是两个 ES 索引** | `vector_index/` + `text_index/` 各建一个索引,基于 LangChain `ElasticVectorSearch`(老 ES) | **升级到 ES8 原生 `dense_vector` + kNN**,向量 + 全文 **放同一个索引**,单引擎混合检索(见 §4.1);复用 v2.0 `elasticsearch_handler` 的连接/客户端 |
| **embedding 锁死 DashScope** | `utils.py` 写死 `EMBEDDING_TYPE='dashscope'` | embedding 模型从 `module_ai.ai_models`(model_type='embedding')取,落到 `AiSettings` 兜底;支持 OpenAI/DashScope/本地 |
| **rerank 锁死 DashScope** | `rerank/dashscope_rerank.py` | rerank 模型同样从 `ai_models`(model_type='rerank')取;可选 bge-reranker 本地 |
| **embedding 缓存用 pickle 存 MySQL** | `rag_embedding` 表存二进制 | **保留缓存(持久化)**——它能省 embedding 调用、且向量库丢数时可零成本重灌(见 §4.2);只是把 pickle 换成结构化存储 + 打上 model 标记 |
| **配置散落 Flask SYS_CONF** | `config.SYS_CONF[...]` 到处读 | 收敛到 `env.py` 的 `RagSettings` + `ai_models` 表 |
| **Flask 同步 + 无多租户** | 同步视图,无 tenant 隔离 | FastAPI async + `TenantMixin` 自动租户 + `data_scope_sql` 数据权限 |
| **前端 jeecg 体系** | Ant Design Vue + jeecg BasicTable/useModal | 用 v2.0 的 Element Plus + 现有列表/弹窗范式重写(与数据源/任务调度页一致) |
| **训练流程黑盒** | celery 一把梭 `train_document` | 拆为可观测的流水线(抽取→清洗→切分→embed→入库),状态落 `rag_document.status`,日志走任务日志框架 |

---

## 3. 市面调研

| 方案 | 定位 | 取舍 |
|---|---|---|
| **Dify** | 一站式 LLMOps(知识库 + Workflow + Agent + 插件市场) | 太重,且与本平台 DAG/Agent 定位重叠;不整体引入,借鉴其「混合检索 + rerank」与文档分段 UX |
| **RAGFlow** | 深度文档理解 RAG 引擎(强解析、可解释召回) | 文档解析(版面/表格)质量最好;可作为 **P2 文档解析增强**(把它的 parser 当一个 extractor 后端),不作为主框架 |
| **FastGPT** | 企业知识库问答 + 可视化 Flow | 与本平台 DAG + AiApp 思路一致,可借鉴 QA 数据集与召回测试 UX |
| **LangChain / LlamaIndex** | 库 | master 已用 LangChain 的 splitter / Document 类型;保留这部分,但不绑定其 vectorstore |

**结论**:**不引入重型平台,自建轻量 RAG 层**。骨架沿用 master(已在生产跑通),把向量库 / embedding / rerank 三处可插拔化,接到 v2.0 已有的 `module_data` 向量 handler + `module_ai` 模型管理 + Agno 上。混合检索 + rerank 是 2026 年 RAG 的标配(Dify/RAGFlow/FastGPT 均默认),保留 master 已实现的这套。深度文档解析(RAGFlow)列为 P2 增强。

---

## 4. 选型总结

| 层 | 选型 | 说明 |
|---|---|---|
| 后端框架 | FastAPI + async SQLAlchemy | 与 v2.0 一致 |
| 新模块 | `api/module_rag/`(controller/service/dao/entity 标准分层) | APIRouterPro 自动注册 |
| **向量库 + 全文库** | **ES8(主)**——`dense_vector`(kNN/HNSW)+ BM25 同库混合 | 复用 `elasticsearch_handler` 连接;一套 ES 兼做日志 / 向量 / 数据服务 |
| 向量库(备选) | `module_data` `VectorConnector`(Agno):Milvus/Qdrant/PgVector/Chroma | 通过 `dataset.vector_source_id` 指向不同 data_source,接口抽象,后续可换 |
| Embedding / Rerank | `module_ai.ai_models`(model_type=embedding/rerank)+ `AiSettings` 兜底 | 多 provider,密钥 AES |
| **Embedding 缓存** | 持久表 `rag_embedding`(hash+model → 向量) | 省调用 + 灾备重灌;可选 Redis 热层 |
| 文档抽取 | 移植 master `extractor/`(P1);RAGFlow parser(P2) | 文件来源走 `storage_utils` |
| 切分 / 清洗 | 移植 master `splitter/` + `cleaner/`(LangChain splitter 保留) | chunk_size/overlap 走文档级 `chunk_strategy` |
| 异步训练 | v2.0 Celery + 任务日志框架 | 文档状态机 + 可观测日志 |
| 前端 | Vue3 + Element Plus(对齐数据源/任务页) | 重写四页 |
| AI 集成 | 知识库作为 Agno `Knowledge` / Agent 工具 | AiApp 挂知识库,RAG 检索作为工具 |

### 4.1 ES8 一套三用(日志 / 向量库 / 数据服务)

一套 ES8 集群同时承担三种角色,索引互相隔离、互不串:

| 角色 | 索引 | 现状 | RAG 改动 |
|---|---|---|---|
| **日志存储** | `task_logs`(`task_es_*` 配置) | 已用(`task_logger` / `es_log_dao`) | 不动 |
| **数据服务(数据源)** | 用户自有索引 | 已用(`elasticsearch_handler`,query/scan/bulk) | 不动 |
| **向量 + 全文库(RAG)** | 每个知识库一个 `rag_ds_{dataset_id}` | 新增 | 见下 |

**为什么向量库选 ES8 而不是 PgVector/Milvus**:① 这套栈本就依赖 ES(日志、数据源),不引入新组件;② ES8 原生 `dense_vector` + kNN(HNSW)+ BM25,**向量召回和关键词召回在同一引擎、同一索引**完成,混合检索天然;③ 运维面收敛。代价是单点压力集中(见 §8 风险)。

**索引设计**(每个知识库一个索引,维度随其 embedding 模型而定,所以必须 per-dataset 而非共享):
```jsonc
PUT rag_ds_{dataset_id}
{
  "mappings": {
    "properties": {
      "content":        { "type": "text", "analyzer": "ik_max_word" },   // BM25 全文(中文可装 ik 分词)
      "content_vector": { "type": "dense_vector", "dims": <embedding 维度>,
                          "index": true, "similarity": "cosine",
                          "index_options": { "type": "hnsw", "m": 16, "ef_construction": 100 } },
      "tenant_id":   { "type": "keyword" },   // 多租户隔离 filter
      "document_id": { "type": "keyword" },   // 按文档删除
      "chunk_id":    { "type": "keyword" },
      "chunk_type":  { "type": "keyword" },   // chunk / qa
      "question":    { "type": "text" },
      "meta":        { "type": "object", "enabled": false }
    }
  }
}
```

**写入**:`elasticsearch.helpers.bulk` 批量 upsert(`_id`=chunk_id),向量来自 §4.2 缓存或现算。
**按文档删除**:`delete_by_query { term: document_id }`。
**混合检索(单请求)**:一条 `_search` 同时带 `knn`(向量)和 `query`(BM25),都挂 `filter: [tenant_id, dataset 内]`:
```jsonc
POST rag_ds_{id}/_search
{ "knn":   { "field": "content_vector", "query_vector": [...], "k": 50, "num_candidates": 200,
             "filter": { "term": { "tenant_id": "100" } } },
  "query": { "bool": { "must": { "match": { "content": "用户问题" } },
                       "filter": { "term": { "tenant_id": "100" } } } },
  "size": 50 }
```
> **许可证注意**:ES 内置的 RRF 融合(`retriever`/`rank.rrf`)需要 **Platinum/Enterprise** 许可。basic 免费版下:kNN、`dense_vector`、BM25 都免费,所以 **融合在应用层做**(各自召回 → RRF/分数归一去重 → rerank → top_k),正好复用 master `get_knowledge` 已有的「多线程向量+全文 → content hash 去重」逻辑,零许可证依赖。
> **维度上限**:ES8 `dense_vector` 上限 4096 维,常见 embedding(1024/1536/3072)均可。

### 4.2 Embedding 缓存(省成本 + 灾备重灌)

保留 master 的缓存思想,但持久化、结构化、带 model 标记:

- 表 `rag_embedding`:`hash`(content 的 md5)+ `model_id` 联合唯一 → `vector`(JSON 数组 / PG 可用原生数组)+ `dim` + `created_at`。
- **embed 时**:先按 `(model_id, hash)` 查缓存,命中跳过模型调用 → 省钱、提速、相同文本天然去重。
- **灾备/迁移**:ES 索引若损坏、或要换 embedding 模型以外的事情(扩容、改 HNSW 参数、迁向量库),可直接 **从 `rag_chunk` + `rag_embedding` 批量重灌 ES,完全不调 embedding 模型**。
- 可选 Redis 作热层(key=`emb:{model_id}:{hash}`),DB 仍是真相源。

---

## 5. 重构方案

### 5.1 数据模型(`api/module_rag/entity/do/rag_do.py`)
沿用 master 三张主表,去掉 pickle 缓存表,统一加 `TenantMixin`:

- **`rag_dataset`**(知识库):`id` / `name` / `description` / `embedding_model_id`(指向 ai_models)/ `vector_source_id`(指向 data_source,即向量库连接)/ `index_name` / `built_in` / `status` / Tenant + 审计字段。
  - **关键决策**:每个知识库**绑定一个 embedding 模型 + 一个向量库连接**(向量维度由 embedding 模型决定,建库后不可改 embedding,与 Dify 一致)。
- **`rag_document`**(文档):`id` / `dataset_id` / `document_type`(upload_file / notion / website / datamodel)/ `name` / `status`(1待训练 2训练中 3成功 4失败)/ `meta_data`(JSON,存来源:file_key / url / notion_id / datamodel_id)/ `chunk_strategy`(JSON:chunk_size / overlap / 清洗规则)/ `error`(失败原因)+ Tenant。
- **`rag_chunk`**(分段):`id` / `dataset_id` / `document_id` / `chunk_type`('chunk' / 'qa')/ `content` / `question` / `question_hash` / `answer` / `hash`(content 去重)/ `position` / `status` / `star_flag` + Tenant。(`chunk_id` 即 ES `_id`,无需单列 vector_id。)
- **保留 `rag_embedding`**(见 §4.2):`hash` + `model_id` 唯一 → `vector` + `dim`。作用是省 embedding 调用 + ES 丢数时零成本重灌。

> 与 DAG「图按版本存」不同,知识库不需要版本化文档;但 `chunk_strategy` 存在文档级,便于按文档重训。`rag_chunk` + `rag_embedding` 一起构成 ES 索引的「可重建真相源」。

### 5.2 训练流水线(`service/rag_train_service.py`,Celery 异步)
文档训练拆成可观测的 5 步,每步更新 `rag_document.status` 并写任务日志:

```
1. extract  抽取   —— storage_utils 下载文件 → extractor 按类型解析 → 原始文本/表格
2. clean    清洗   —— CleanProcessor 去噪
3. split    切分   —— RecursiveCharacterTextSplitter(按 chunk_strategy) → chunks
4. embed    向量化 —— 取 dataset.embedding_model_id 对应模型(Redis 缓存)→ 向量
5. index    入库   —— VectorConnector.write 写向量库 + 全文索引;chunk 落 rag_chunk
```
- 入口 `train_document(document_id)` 由 controller `apply_async` 投递到 Celery;失败 status=4 并记 `error`。
- `train_datamodel(dataset_id, datamodel_id)`:把数据模型 schema/样例转文本灌库(移植 master 逻辑)。
- QA:`train_qa(dataset_id, question, answer)` → `chunk_type='qa'`,question_hash 精确命中走捷径。

### 5.3 检索 / 召回(`service/rag_retrieval_service.py`)
移植并增强 master 的 `get_knowledge` / `query_knowledge`:
- 入参:`query` / `dataset_ids[]` / `top_k` / `retrieval_type`(vector / keyword / hybrid)/ `score_threshold` / `rerank`(bool)/ `rerank_score_threshold`。
- **hybrid**:并发向量召回 + 全文召回 → 按 content hash 去重 → (可选)rerank 重排 → score 阈值过滤 → 取 top_k。
- **QA 捷径**:命中 question_hash 直接返回标星答案。
- rerank 模型从 `ai_models`(model_type='rerank')取。
- 返回 `{total, records:[{content, chunk_id, dataset_id, document_id, score, ...}]}`,供召回测试页与 Agent 工具共用。

### 5.4 向量库 / embedding / rerank 抽象接入
- **向量库(主:ES8)**:复用 `elasticsearch_handler` 的连接配置/客户端,在 `module_rag` 侧加一层 `EsVectorStore`(建索引 mapping、bulk upsert、kNN+BM25 检索、按 document_id 删除),见 §4.1。每个 dataset 独立索引 `rag_ds_{dataset_id}`。
- **向量库(备选)**:若 `dataset.vector_source_id` 指向非 ES 的 data_source,则走 `module_data` 的 `VectorConnector`(Milvus/Qdrant/PgVector/Chroma)。检索接口统一,上层不感知后端。
- **embedding**:`AiUtil.get_embedding_model(model_id)`(新增,类比现有 `get_model_from_factory`),provider 走 ai_models;无则落 `AiSettings`。embed 前查 `rag_embedding` 缓存(§4.2)。
- **rerank**:同上,`get_rerank_model(model_id)`。
- 维度校验:建库时把 embedding 维度写进 dataset 与 ES mapping `dims`;之后该库 embedding 模型不可改(改则需重建索引)。

### 5.5 与 AI 层集成(P2)
- 知识库可作为 **Agno `Knowledge`** 注入 Agent,或暴露为 Agent 的「知识检索」工具(调用 5.3 的检索接口)。
- AiApp(若移植)新增「关联知识库」配置(`dataset_ids`),对话时先检索后生成(RAG)。

### 5.6 前端(Element Plus 重写)
对齐数据源 / 任务调度页的列表 + 抽屉/弹窗范式,四个页面:
- **知识库列表** `views/rag/dataset/`:CRUD;建库时选 embedding 模型 + 向量库连接。
- **文档管理** `views/rag/document/`:上传文件 / 填网页 URL / 选数据模型;训练按钮触发异步训练 + 状态轮询(待训练/训练中/成功/失败);失败看 error。
- **分段管理** `views/rag/chunk/`:查看/编辑/删除分段,标星,手动加 QA 对。
- **召回测试** `views/rag/retrieval/`:输入 query + 检索参数(top_k / 模式 / 阈值 / rerank),展示命中分段 + score(复用 5.3 接口)。

### 5.7 API(`api/module_rag/controller/`,前缀 `/rag`)
```
# 知识库
GET    /rag/dataset/list           列表(task 权限 rag:dataset:list)
POST   /rag/dataset                新建
PUT    /rag/dataset/{id}           编辑
DELETE /rag/dataset/{ids}          删除(连带 chunk + 向量库 collection)

# 文档
GET    /rag/document/list          列表(dataset_id 过滤)
POST   /rag/document               新建(上传/URL/datamodel)
DELETE /rag/document/{ids}         删除
POST   /rag/document/{id}/train    触发训练(异步)
GET    /rag/document/{id}/status   训练状态轮询

# 分段
GET    /rag/chunk/list             列表
POST   /rag/chunk                  新增/编辑(含 QA)
DELETE /rag/chunk/{ids}            删除
POST   /rag/chunk/{id}/star        标星

# 召回
POST   /rag/retrieval              召回测试 / Agent 检索入口
```
权限点:`rag:dataset:*` / `rag:document:*` / `rag:chunk:*` / `rag:retrieval`。菜单挂在「数据管理」或新增「知识库」一级菜单(与 DAG 同样走 `ezdata.sql` / `ezdata-pg.sql` seed)。

---

## 6. 复用与最小改造点

| 来源 | 复用什么 | 改造 |
|---|---|---|
| master `rag/extractor/` | 整套抽取器(pdf/excel/csv/html/docx/md/txt/notion/web) | 去 Flask config,文件来源改 `storage_utils`;LangChain Document 保留 |
| master `rag/cleaner/` `rag/splitter/` | 清洗 + 递归切分 | 基本照搬,参数走 `chunk_strategy` |
| master `rag/services/rag_service.py` | 训练 + 混合检索 + rerank + QA 算法 | 拆服务、async 化、接抽象层 |
| v2.0 `elasticsearch_handler` | ES 连接配置/客户端/bulk/scan(主向量库) | 加 `dense_vector` mapping + kNN 检索(`EsVectorStore`) |
| v2.0 `module_data` 向量 handler | 备选向量库(Milvus/Qdrant/PgVector/Chroma) | RAG 的 collection 命名/批量 upsert(仅备选路径) |
| v2.0 ES 日志(`task_es_*`) | 同一 ES 集群,验证连接/认证范式 | 复用配置思路,RAG 用独立索引 |
| v2.0 `module_ai` | embedding/rerank/LLM 模型来源 | 新增 `get_embedding_model` / `get_rerank_model` |
| v2.0 `storage_utils` | 文件存取 | 直接用 |
| v2.0 Celery + 任务日志 | 异步训练 + 可观测日志 | 直接用 |
| v2.0 多租户 / 数据权限 / APIRouterPro | 隔离 + 鉴权 + 路由 | 直接用 |

---

## 7. 分阶段落地

- **P0 骨架 + ES 验证**:`module_rag` 分层 + 三表 DDL(`ezdata.sql` / `ezdata-pg.sql`,含 `rag_embedding`)+ dataset CRUD + 菜单/权限 seed。**先用 `EsVectorStore` 在 ES8 上跑通 建mapping→bulk写向量→kNN+BM25→delete 的最小闭环**(见 §8)。
- **P1 训练 + 检索闭环**:移植 extractor/cleaner/splitter;embedding 接 `module_ai`;Celery 异步训练 + 状态机;混合检索 + rerank;召回测试页。**端到端打通:建库→传文档→训练→召回。**
- **P1.5 前端四页**:Element Plus 重写,状态轮询。
- **P2 增强**:多向量库可选(Milvus/Qdrant/ES);QA 数据集;数据模型训练;RAGFlow 深度解析作为可选 extractor 后端;Redis embedding 缓存。
- **P3 AI 集成**:知识库挂 Agno Agent / AiApp;RAG 对话。

---

## 8. 风险与权衡

- **embedding 维度与向量库绑定**:换 embedding 模型须重建索引(ES `dims` 固定)。建库即锁定 embedding,UI 明确提示(与 Dify 一致)。
- **一套 ES 三用的单点压力**:日志高频写入 + 向量 kNN(CPU/内存密集)+ 数据源查询挤在同一集群,可能互相影响。缓解:RAG 用独立索引、必要时独立 ES 节点/分片策略;生产建议日志与向量至少分索引分片,后续可分集群。**这是用「少一个组件」换「单点 blast radius」的权衡,需向运维确认 ES 规格。**
- **ES8 版本与许可**:需 ES **8.x**(`dense_vector`+kNN);内置 RRF 融合要 Platinum,本方案融合放应用层规避(§4.1)。中文全文检索建议装 ik 分词插件。
- **EsVectorStore 是新代码**:master 用的是老 `ElasticVectorSearch`,ES8 原生 kNN 写法不同。**P0 需先用一个小索引验证:建 mapping → bulk 写向量 → kNN+BM25 检索 → delete_by_query,跑通再铺开。**
- **文档解析质量**:master extractor 对复杂 PDF/表格一般;P2 引入 RAGFlow 解析或 Unstructured 作为可选后端。
- **大文件训练耗时 / worker 阻塞**:走 Celery 异步,长文档分批 embed;注意与 dlt 单 worker 约束(见 [[connector-engine-strategy]])不冲突——RAG 训练可独立队列。
- **Celery prefork 与某些库 fork 不兼容**:embedding/解析库若有 fork 问题,参照 DAG/dlt 的 `WORKERS=1` 处理。
- **多租户向量隔离**:collection 名带 tenant 或库内 metadata 过滤,避免跨租户召回。
- **成本**:embedding/rerank 调用计费,Redis 缓存 + question_hash 捷径降本。

---

### 参考来源
- Dify 混合检索 + Rerank:https://dify.ai/blog/hybrid-search-rerank-rag-improvement
- 开源 Agent/RAG 平台对比(n8n/Dify/RAGFlow/Coze):https://jimmysong.io/blog/open-source-ai-agent-workflow-comparison/
- Dify vs RAGFlow:https://slashdot.org/software/comparison/Dify-vs-RAGFlow/
- master 源码:`api/web_apps/rag/`(db_models / extractor / cleaner / splitter / embedding / vector_index / text_index / rerank / services / views)
- v2.0 底座:`api/module_ai/`、`api/module_data/handlers/`(vector_base + chroma/milvus/qdrant/pgvector)、`api/utils/storage_utils.py`、`api/config/env.py`(AiSettings)
