# ezdata 重构计划 —— AI 原生数据平台(数据平台 + Agent 层)

> 分支:`v2.0`(已采用 RuoYi-Vue3-FastAPI 模板分层结构)
> 方向定稿日期:2026-06-17
> 本文档取代旧版《迁移到 RuoYi-Vue3-FastAPI 模板》计划(旧版在 git stash 中保留)。
> 旧版关注"Flask → FastAPI 模板迁移";本版关注"重构为 AI 原生数据平台"的目标架构与选型。

---

## 0. 方向转变(一句话)

把 ezdata 从"表单驱动的数据平台"重构为 **数据平台 + AI Agent 层**:

- **数据源 / 数据管道 / 数据服务仍是一等公民**(表单可配、确定性运行);
- **AI(Agno)作为 build-time copilot**:辅助开发调试阶段生成抽取/转换代码、建数据服务接口;
- **AI 不进生产热路径**:调好的逻辑固化成 JSON spec + 冻结代码,由 Celery 大批次确定性运行。

---

## 1. 现状(v2.0 已落地)

- 模板分层结构已全面落地:`config/ common/ middlewares/ exceptions/ sub_applications/ cli/ alembic/`。
- 已有模块:`module_admin`(系统,完整)、`module_ai`(已集成 **agno==2.4.8**,chat 跑在 Agent/Team/Workflow 抽象上)、`module_alert`、`module_generator`、`module_task_schedule`(Celery + APScheduler + runners:python/shell/dynamic/sandbox)。
- 依赖中**无 langgraph / langchain / mindsdb**——无历史包袱。
- 尚未建:`module_data` / `module_etl` / `module_dataapi`(本计划核心)。
- 已有可复用治理积木:`ApiCache`/`ApiCacheEvict`、接口限流、RBAC + **行级多租户**、日志脱敏、传输加密、自动路由注册 + OpenAPI、存储抽象(local/s3/minio/aliyun/azure/google/tencent/oci)。

---

## 2. 核心架构决策(已定)

### 2.1 三条运行时路径

```
配置面(表单)          构建面(AI copilot, build-time)        运行时
──────────────        ────────────────────────────         ─────────────────────────────────
数据源连接(schema驱动)  Agno Agent + sandbox                  ┌ 批处理:JSON spec → Celery 大批次(写)
ETL spec(JSON)    ◄── introspect → 调试预览 → emit spec ──►  ├ 服务:Data API → FastAPI 请求/响应(读)
Data API spec           (仅开发调试期介入)                    └ 检索:向量/搜索(给 RAG/Knowledge 复用)
```

- **写路径(批 ETL)**:重、后台、Celery;由 dlt 抽取加载 + AI 生成的转换代码(sandbox 执行)。
- **读路径(Data API)**:轻、请求级、低延迟;由薄 native 连接器发参数化 native query。
- **构建面**:Agno copilot 在开发调试期生成代码、实时预览数据,产物冻结成 spec。

### 2.2 选型一览

| 能力 | 选型(已定) | 备注 |
|---|---|---|
| Agent 框架 | **Agno**(已集成) | build-time copilot;Teams/Workflows/HITL/MCP |
| RAG / 知识库 | **Agno Knowledge** | 不建独立 `module_rag`;向量库复用 |
| 批 ETL 抽取+加载 | **dlt** | 库、脚本即 Celery 任务;核心源 + AI 生成自定义源 |
| 转换 | **AI 生成 Python 代码 + sandbox** | 不做内置算子库;代码冻结进 spec |
| 调试期数据预览 | **dlt**(resource 迭代 / DuckDB / `dlt pipeline show` / ibis) | "调试重、生产轻" |
| 治理库 / 已加载数据查询 | **DuckDB + ibis/SQL** | ibis 仅用于已 normalize 的同构数据,**非异构源联邦** |
| Data API 查活源 + introspect | **薄 native 连接器注册表** | SQLAlchemy(1)+ 文件(1)+ Mongo/ES/Neo4j(薄)+ 向量(复用 Agno) |
| 编排 / DAG | **Celery + APScheduler** | JSON spec 即 DAG;不引第三方编排器 |
| 向量库 | Agno 支持的(pgvector/Qdrant/Weaviate…) | ETL 汇 + 检索源 + Knowledge 后端,三位一体 |

**明确不引入**:MindsDB 引擎(vendored)、LangGraph、ibis-as-联邦层、Trino、Prefect/Dagster、内置算子库。
**明确删除**:`bigscreen`、`algorithm` 模块。

### 2.3 为什么这么选(关键理由)

- **不用统一 SQL 联邦(MindsDB/ibis/Trino)**:ES(检索)、Neo4j(图)、向量(相似度)压成 SQL 会丢原生语义;且与"AI 生成代码 + Celery 批跑"的代码驱动模型不同构。
- **dlt 契合**:库、脚本即任务、官方主推"通用核心源 + AI 生成自定义源",和本架构同构;轻(几个 pip 依赖) vs MindsDB 1541 文件 + conda。
- **dlt 只写不读**:查询要么直查活源(native 连接器),要么查 dlt 搬好的治理库(DuckDB/SQL);故连接器注册表不可省。
- **维护面其实很小**:SQLAlchemy 一份 schema 吃下所有 SQL 库;真正自写 ≈ 1 SQL + 4 个小模型(ES/Neo4j/Mongo/向量),且可由 AI 生成。

---

## 3. 数据源管理设计(`module_data`)

### 3.1 问题:异构源参数各不相同

保留"JSON 存连接参数"的灵活性,但补齐纯 JSON blob 的四个痛点:无校验、无法自动渲染表单、密钥明文、不可查询。

### 3.2 表结构:结构化列 + JSON config + 密钥分离

```python
class DataSource(Base, TenantMixin):       # 复用行级多租户
    id: str
    name: str
    code: str                # ETL spec / Data API 用它稳定引用
    source_type: str         # 'mysql' | 'elasticsearch' | 'neo4j' | 's3' | 'qdrant' ...
    family: str              # 'rdbms' | 'warehouse' | 'file' | 'document' | 'search' | 'graph' | 'vector'
    config: JSON             # 非密钥的类型专属参数(保留 JSON 灵活性)
    secrets: Text            # 密钥单独存,AES 加密(复用 crypto_util)
    status: str              # 'untested' | 'ok' | 'failed'
    last_test_at: datetime
    remark: str
    # tenant_id / dept_id / create_by 来自 TenantMixin
```

要点:可查询/治理/隔离字段提成真列;密钥从 config 抽出单独加密;变化的连接参数继续放 config JSON。

### 3.3 每类型连接 Schema(驱动校验 + 表单 + 密钥 + 适配)

每种源类型注册一份 Pydantic 连接模型,挂在连接器注册表上。SQL 家族共用一份 + dialect 区分:

```python
class SqlAlchemyConn(BaseModel):           # rdbms + SQL 数仓全用这一份
    dialect: Literal['mysql','postgresql','oracle','mssql','clickhouse','sqlite']
    host: str; port: int; database: str; username: str
    password: SecretStr                    # SecretStr = 自动识别为密钥
    options: dict = {}

class ESConn(BaseModel):
    hosts: list[str]; verify_certs: bool = True
    api_key: SecretStr | None = None
    username: str | None = None; password: SecretStr | None = None

class Neo4jConn(BaseModel):
    uri: str; username: str; password: SecretStr; database: str = 'neo4j'

class S3Conn(BaseModel):
    bucket: str; endpoint_url: str | None = None     # MinIO/OSS 兼容
    access_key: SecretStr; secret_key: SecretStr
```

### 3.4 表单自动渲染:多来源 schema → 统一 JSON Schema

```
GET /data/source/schema/{type}
   ├─ Pydantic 模型           → model_json_schema()      # 自己的 SqlAlchemyConn + 4 个小模型
   ├─ dlt configspec(可选)   → 反射字段 → JSON Schema    # 文件/cloud creds/destinations
   └─ MindsDB connection_args(可选,仅借元数据不跑引擎) → JSON Schema  # 想广覆盖时
→ 前端用 JSON-Schema 驱动渲染器动态渲表单(Element Plus)
```

新增源类型 = 一个 Pydantic 模型 + 注册一行,前端零改动。

### 3.5 密钥与运行时适配

- 提交时按 schema 把字段拆成 config(非密钥) + secrets(SecretStr 字段),secrets AES 加密入库。
- 连接时才解密合并;API 返回时密钥脱敏(`******`)。
- 进阶:支持 `${ENV_VAR}` / vault 引用。
- 连接器用同一份 config + 解密 secrets,按需产出 **native client**(Data API/introspect)与 **dlt source/destination 凭据**(批 ETL)。**dlt 凭据运行时从库注入,不用 secrets.toml**——DB 是唯一真相源。
- native client 按 `source_id + config_hash` 缓存(连接池),编辑后失效重建。

---

## 4. ETL 引擎设计(`module_etl`)

### 4.1 spec 形态(声明式抽取/加载 + 冻结转换代码)

```jsonc
{
  "name": "...",
  "extract": { "source_code": "...", "type": "sql|cypher|es_dsl|mongo|file|rest",
               "query_or_resource": "...", "incremental_key": "created_at" },
  "transform": { "kind": "python_code", "code": "<AI 生成、调试通过后冻结的转换代码>" },
  "load":    { "sink_code": "...", "table": "...", "write_mode": "append|merge|replace" },
  "schedule": { "cron": "..." }
}
```

- 抽取/加载声明式;**转换是冻结的 Python 代码块**(无算子库)。
- 转换代码**生产批跑也在 sandbox 执行**——`runners/sandbox.py` 从调试工具升级为生产执行路径:隔离、超时、资源限制、依赖白名单按生产标准做。
- 代码需版本化 + 审计(谁生成、改了什么)。

### 4.2 执行

- spec 落到 `module_task_schedule`:APScheduler 触发 → dispatch → Celery 队列 → runner。
- 抽取/加载走 dlt;ES/Neo4j 用 AI 生成的 `@dlt.resource` 包原生驱动。
- 中间统一为 **Arrow/Polars 记录流**做转换(异构源 → 转换 → 异构汇的通用交换格式,**不是 SQL**)。

### 4.3 AI 调试闭环

```
AI 写 dlt resource(抽取) → 跑到本地 DuckDB(调试重 OK)
   → ds.df() / `dlt pipeline show` 实时看数据 → 迭代转换代码(sandbox)
   → 满意 → 冻结成 spec → 生产 Celery 批跑(destination 换数仓/治理库)
```

---

## 5. 数据服务接口设计(`module_dataapi`)

### 5.1 spec 形态

```jsonc
{
  "name": "订单查询", "path": "/api/data/orders", "method": "GET",
  "datasource_code": "...",
  "query": { "type": "sql|cypher|es_dsl|mongo|vector", "body": "... {{filters}} ..." },
  "params": [ {"name":"status","type":"str","operator":"eq"},
              {"name":"start","type":"date","operator":"gte","bind":"created_at"} ],
  "pagination": { "default": 20, "max": 200 },
  "security": { "auth":"rbac|apikey|public", "rate_limit":"60/min",
                "cache_ttl": 30, "field_mask":["phone"], "tenant_scoped": true }
}
```

请求流程:校验参数 → **安全地构造 native query** → 连接器 read → 整形/脱敏 → 缓存 → 返回。

### 5.2 安全(最大工程风险,必须设计死)

跨范式参数注入面:
- **SQL**:仅参数化绑定,绝不拼接;筛选字段/操作符白名单;强制 LIMIT 上限。
- **Cypher**:`$param` 参数化,禁止拼接。
- **ES DSL**:程序化构造 query 对象,不做模板注入。
- **Mongo**:白名单字段构造 filter dict,拦截 `$where`/`$gt` 等操作符注入。
- **向量**:`top_k` 上限、维度校验。
- 统一做法:params 声明式 + 每连接器实现"安全的参数→native query 构造器",模板只允许预声明占位符。

### 5.3 复用现成治理积木

`ApiCache`/`ApiCacheEvict`(缓存)、限流装饰器(rate_limit)、RBAC + 行级多租户(鉴权 + tenant_scoped)、脱敏(field_mask)、传输加密、自动 OpenAPI(接口文档)。

### 5.4 分层建议

默认引导走 `源 → ETL → 治理表 → Data API`(对外暴露可控结果集),而非直接透传生产库。查治理表 = DuckDB/数仓 SQL;透传活源 = native 连接器。

---

## 6. AI 层(`module_ai`,Agno)

- **build-time copilot**:工具 = introspect(取 schema/样本)、run_in_sandbox(拿样本跑候选代码)、emit_spec(导出 ETL/Data API 的 JSON)。人审核 → 存库 → 排程。
- **RAG = Agno Knowledge**:向量库与数据侧向量库连接器复用同一套。
- chat 已跑在 Agent/Team/Workflow 抽象上,继续演进。

---

## 7. 数据源族 → 连接器/工具映射

| 源族 | 典型 | 查询范式 | 驱动 | 批 ETL(dlt) | 服务/查询 |
|---|---|---|---|---|---|
| 关系库 | MySQL/PG/Oracle/MSSQL/SQLite | SQL | SQLAlchemy(1 连接器) | `sql_database` | native + ibis |
| 数仓 | ClickHouse/Doris/Snowflake/BigQuery | SQL(方言) | SQLAlchemy/native | source + **destination** | SQL |
| 文件/对象存储 | CSV/Excel/Parquet/JSON,S3/OSS/MinIO | 路径+读取 | fsspec + polars/pyarrow | `filesystem` | DuckDB 读 |
| 文档库 | MongoDB | 文档/聚合 | pymongo/motor | verified 源 | native |
| 搜索 | Elasticsearch/OpenSearch | Query DSL | elasticsearch-py | AI 生成 `@dlt.resource` | native search |
| 图库 | Neo4j | Cypher | neo4j driver | AI 生成 `@dlt.resource` | native cypher |
| 向量库 | Milvus/Qdrant/Weaviate/pgvector | 相似度 | Agno / 各 SDK | **destination** | vector search |

---

## 8. 新模块地图(对比旧计划)

| 模块 | 职责 | 变化 |
|---|---|---|
| `module_data` | 7 族数据源,表单配置(schema 驱动),能力化连接器注册表 | 新建(合并旧 datasource+datamodel) |
| `module_etl` | JSON spec + AI 生成转换代码 + sandbox,Celery 批跑 | 新建(吸收旧 etl 思路,去内置算子) |
| `module_dataapi` | Data API spec + 安全参数构造 + 复用缓存/限流/脱敏 | 新建(旧 data_interface) |
| `module_ai`(Agno) | build-time copilot;RAG 复用 Knowledge | 升级为核心 |
| `module_task_schedule` | 执行底座(Celery/APScheduler/sandbox) | 保留 |
| `module_admin` / `module_alert` / `module_generator` | 系统 / 告警 / 代码生成 | 保留 |
| ~~`module_rag`(独立)~~ | → Agno Knowledge | 删 |
| ~~`module_bigscreen`~~ / ~~`module_algorithm`~~ | — | 删 |
| ~~MindsDB / ibis 联邦 / LangGraph~~ | — | 不引入 |

---

## 9. 待定决策(由你后续拍板)

1. **连接器层最终方案**:
   - A. 薄自建 native 连接器注册表(SQLAlchemy 1 + 文件 1 + Mongo/ES/Neo4j 薄 + 向量复用 Agno)——**当前倾向**;
   - B. MindsDB 当**只读查询网关**(不 vendored,独立服务 + MCP),几乎不写连接器但多运维一个重服务、查询锁 SQL;
   - C. Trino 联邦查询引擎(运维最重)。
2. **是否借用 MindsDB `connection_args` 元数据**(仅取元数据、不跑引擎)来广覆盖连接表单定义。
3. **dlt 自定义源策略**:dlt 原生源 + AI 生成 ES/Neo4j 自定义 resource(默认) vs 更多源都用 AI 生成。
4. **治理库默认 sink**:本地/集中 DuckDB vs 直接数仓。
5. **前端**:新模块(数据源/ETL/Data API/对话/Knowledge)视图统一 TS + Element Plus 重画;旧 antd 残留依赖清理。

---

## 10. 主要风险

1. **同步/异步边界**:Agno/AgentOS async,Celery worker sync,dlt/DuckDB 多 sync——重查询/搬运走线程池或 sync session,勿阻塞事件循环。
2. **sandbox 生产化**:转换代码生产批跑也在 sandbox,隔离/超时/资源限制/依赖白名单要按生产标准。
3. **Data API 注入安全**:跨范式参数构造必须参数化 + 白名单(见 §5.2)。
4. **Agno 版本速度快**(2.x 高频迭代),锁版本 + 关注破坏性变更。
5. **AgentOS 与现有 FastAPI 模板的关系**:子应用挂载 vs 接管入口,路由/鉴权/多租户对齐。

---

## 11. 分阶段实施(里程碑)

```
M0  module_data 骨架:DataSource 模型 + 连接 Schema 注册表 + 表单端点(JSON Schema)+ 测连接
M1  薄 native 连接器:SQLAlchemy / 文件 / Mongo / ES / Neo4j / 向量(复用 Agno),introspect + sample
M2  module_etl:dlt 接入 + sandbox 生产化 + JSON spec 落 Celery;调试预览(DuckDB / dlt show)
M3  module_ai copilot:introspect / run_in_sandbox / emit_spec 工具;Agno Knowledge(RAG)
M4  module_dataapi:Data API spec + 安全参数构造 + 复用缓存/限流/脱敏/多租户
M5  前端:数据源 / ETL / Data API / 对话 / Knowledge 视图(Element Plus, TS)
M6  清理:删 bigscreen/algorithm 残留;清 antd 依赖;e2e + 数据兼容验证
```

---

## 附录:与旧计划的差异摘要

- 旧计划核心是"Flask → 模板迁移";本版核心是"AI 原生数据平台架构"。
- 旧计划保留 MindsDB(vendored)+ 搬入 etl/;本版改为 dlt + 薄连接器,MindsDB/ibis 联邦不引入。
- 旧计划有 `module_rag`(56 文件)、`module_bigscreen`、`module_algorithm`;本版全部删除/并入 Agno Knowledge。
- 旧计划 llm 用 LangGraph/DeepAgents;本版统一 Agno(已落地)。
- 新增"三条运行时路径"模型、连接 Schema 多来源设计、Data API 安全设计、AI build-time copilot 定位。
