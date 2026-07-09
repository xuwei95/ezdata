# 数据模块设计说明(数据管理 + 数据集成 + 数据接口)

> 本文描述 `module_data`(数据管理 / 数据集成 / 数据接口)的设计与实现,以已落地代码为准:`module_data/handlers`(60+ 源连接器 + 能力位 + 统一 filters + connection_schema)。

## 0. 一句话

- **数据管理**:Navicat 式工具——左侧「数据源→数据模型」树,右侧 Tab(基本信息 / 数据查询 / 数据接口),Tab 由**能力位**决定显隐。
- **数据集成**:不另造引擎,做成 `module_task_schedule` 的一个**任务组件**(ETL spec → `compile_to_dlt` → 复用调度/重试/监控/告警)。
- **数据接口**:对外只放声明式 `filter`;**原生查询**仅内部/可信用;**AI 取数**给一个"AI 生成原生查询→预览→执行"的口子。

---

## 1. 总体架构

```
                         ┌───────────────── 前端(Vue3+Element Plus+TS)─────────────────┐
                         │  数据管理视图:左树(源→模型) + 右 Tab(信息/查询/接口)         │
                         └───────┬───────────────────┬───────────────────┬──────────────┘
                                 │ schema 表单         │ filter/原生/AI 查询  │ 接口配置
                ┌────────────────▼─────────┐ ┌────────▼─────────┐ ┌────────▼───────────┐
   后端         │ module_data              │ │ 读路径(请求级)   │ │ module_dataapi     │
                │  DataSource / DataModel  │ │  connector.query  │ │  Data API spec     │
                │  connectors(78,已建)    │ │  /search(filters) │ │  动态路由+安全      │
                │  introspect / schema     │ │  AI 取数(Agno)   │ │  复用缓存/限流/脱敏 │
                └─────────┬────────────────┘ └───────────────────┘ └────────────────────┘
                          │ ETL spec(数据集成)
                ┌─────────▼──────────────────────────────┐
                │ module_task_schedule(复用)             │
                │  task_template: data_integration         │
                │  runner: compile_to_dlt(spec) → dlt       │
                │  调度/队列/重试/task_instance/告警 全复用 │
                └──────────────────────────────────────────┘
```

三条运行时:**批 ETL(写)= 任务调度**;**Data API(读)= 请求级 native**;**流式 = 长驻 worker**。

---

## 2. 数据建模(DO 表)

### 2.1 `DataSource`(数据源 = 一个连接)
```
id, name, code(稳定引用), source_type, family, config(JSON 非密钥),
secrets(Text, AES 加密), status(untested/ok/failed), last_test_at, remark
+ TenantMixin(tenant_id/dept_id/create_by)
```
- 提交时按 `connection_schema` 拆 config / secrets(SecretStr 字段加密),返回脱敏。
- `create_handler(source_type, config, secrets)` 直接吃它。

### 2.2 `DataModel`(数据模型 = 源里的某张表/集合/索引/topic)
```
id, name, code, datasource_code(引用 DataSource),
kind(table|collection|index|topic|custom_query),
object_name(表/索引/集合名), db_schema, fields(JSON, introspect 缓存),
default_filters(JSON), auth(can_query/can_api/can_extract/can_write 位),
remark + TenantMixin
```
- 树的**叶子节点**;对应旧版 `model` + `model_conf`。
- 一个源下可建多个模型;模型的 `auth` 位 ∩ 连接器 `capabilities` = 实际可用能力。

### 2.3 ETL = 复用 `task`,不新建顶层表
- 新增 `task_template`:`data_integration`,其 `params` = **ETL spec**(下 §4)。
- 一个集成任务 = 一条 `task`(template_code=`data_integration`),调度/实例/日志全用现成的。

### 2.4 `DataApi`(数据接口)
```
id, name, path, method, datamodel_code, query_mode(filter|native),
filter_config(JSON) | native_query(Text), params(JSON 声明),
pagination(default/max), security(auth/rate_limit/cache_ttl/field_mask/tenant_scoped),
status + TenantMixin
```
- 对外 = `query_mode=filter`(只声明式);`native` 仅内部。

---

## 3. 后端接口(module_data)

| 端点 | 作用 | 底层 |
|---|---|---|
| `GET /data/source/types` | 可选源 + 能力位(建源下拉/卡片,带 icon) | `list_source_types()` |
| `GET /data/source/schema/{type}` | 连接参数 JSON Schema(渲表单) | `connection_schema()` |
| `GET /data/operators` | 操作符目录(filter builder) | `query.OPERATORS` |
| `POST /data/source` `PUT/DELETE` `GET` | 数据源 CRUD(secrets 加密/脱敏) | DAO |
| `POST /data/source/test` | 测连接 | `handler.test_connection()` |
| `GET /data/source/{id}/tables` | 列表/索引/集合(建树 + 选模型) | `list_tables()` |
| `GET /data/source/{id}/tables/{t}/columns` | 字段结构 | `get_columns()` |
| `POST /data/model` `...` | 数据模型 CRUD | DAO |
| `POST /data/model/{id}/query` | **数据查询(不分页)**:filters 或 native,**查出多少渲染多少** | `query()` |
| `POST /data/model/{id}/ai-query` | **AI 取数**:NL→原生查询→预览 | module_ai(Agno) |
| `POST /data/model/{id}/integrate` | 生成集成任务(跳任务调度) | module_task_schedule |

> 查询走 `query()` 直接返回整个结果集(行数由用户的 filters / 原生 SQL 的 LIMIT 自己控),前端 vxe 虚拟滚动渲染;**不做服务端分页**。
> **分页只在数据接口**(§6):连接器另补 `search(table, filters, page, pagesize) → {records,total}`(SQL=LIMIT/OFFSET+COUNT、ES=from/size、Mongo=skip/limit),供 Data API 用。

---

## 4. 数据集成(任务组件)

**ETL spec(task.params):**
```jsonc
{
  "mode": "batch|stream",
  "extract": { "datamodel_code": "...", "filters": [...], "incremental_key": "start_time" },
  "transform": { "kind": "python_code", "code": "<AI 生成、调试通过后冻结;sandbox 执行>" },
  "load": { "sink": "sqlalchemy|filesystem|duckdb|csv|excel", "datasource_code": "...", "table": "...", "mode": "append|merge|replace" }
}
```
**runner = `compile_to_dlt(spec)`(已验证可行):**
```
解析 datamodel → create_handler → handler.extract(filters, incremental_key)  # extract
   → resource.add_map(sandbox(transform.code))                                # transform
   → dlt.pipeline(destination=build_dest(load)).run(...)                      # load
```
- **批**:挂 Celery 队列 + APScheduler cron,进度写 `task_instance`,失败重试/告警全复用。
- **流**:`mode=stream` → 长驻 worker,`handler.stream()` 微批 → sink(binlog/kafka)。

---

## 5. 数据查询(读路径,三档)—— 不分页,查出多少渲染多少

> 数据查询 Tab 是交互式探索(Navicat 式):跑查询 → 直接渲染整个结果集(vxe 虚拟滚动扛行数),**不做服务端分页**;数据量由用户在 filters / 原生 SQL 里自己控(如 LIMIT)。
> (可选)后端留一个**安全上限**(如 5万行)兜底,超限提示用户加条件,而非分页。

1. **filter(表单)**:`filters` 统一结构 → 各源翻译器 → `query()` 返回全部结果。**字段白名单**(只允 introspect 出的列)。
2. **native(内部/可信)**:直接 `query(原生 SQL/DSL/pipeline)`,参数化,查出什么渲染什么。
3. **AI 取数**:`ai-query`(NL + schema → Agno 生成原生查询)→ 预览 → 人工确认 → 可存为 native Data API。AI 只在构建期,不进对外热路径。

---

## 6. 数据接口(module_dataapi)—— **必须分页**

- 与数据查询相反:对外接口**强制分页**(防止外部一次拉爆),走 `connector.search(filters, page, pagesize)` 返回 `{records, total, page, pagesize}`。
- spec 落库 → **动态 FastAPI 路由**:校验声明参数 → 构造 filters(白名单)→ 分页 `search()` → 脱敏/缓存/限流 → 返回。
- `pagination`:`{default, max}`(请求 pagesize 超 max 截断);默认带 `page`/`pagesize` 参数。
- 复用现成积木:`ApiCache`/限流装饰器/RBAC+行级多租户/`crypto`/自动 OpenAPI。
- 对外强制 `query_mode=filter`;native 仅内部接口。

---

## 7. 前端(Navicat 式)

```
┌──────────────┬───────────────────────────────────────────────┐
│ [+新建数据源] │  ┌ 基本信息 ┐ ┌ 数据查询 ┐ ┌ 数据接口 ┐         │
│ ▼ MySQL(ok)  │  │ 连接参数(脱敏)/测连接/能力徽章/字段表    │  │
│   ├ task_inst │  │ ──数据查询──:filter builder + 数据网格   │  │
│   └ task_log  │  │   + 原生查询编辑器(高级) + AI 取数框    │  │
│ ▼ ES(ok)     │  │ ──数据接口──:本模型的 API 列表/新建/测试 │  │
│   └ logs      │  └───────────────────────────────────────────┘  │
│ ▶ Qdrant      │  (Tab 按 模型.auth ∩ 连接器.capabilities 显隐)   │
└──────────────┴───────────────────────────────────────────────┘
```
- **左树**:源(icon by source_type,状态点)→ 模型(懒加载 introspect)→ 字段。
- **右 Tab**:
  - **基本信息**:元信息 + 连接参数(脱敏)+ 测连接 + 能力徽章 + 字段表。
  - **数据查询**(有 READ 才显):filter builder(列下拉 + OPERATORS + 值)+ **vxe-table 数据网格(行/列虚拟滚动)**,**不分页、查出多少渲染多少**;高级:原生查询编辑器(Monaco);AI 取数输入框。
  - **数据接口**(有 GEN_API 才显):该模型的 Data API 列表/新建(filter spec)/生成 URL/测试。
- **能力位驱动 UI**:READ→查询 Tab,GEN_API→接口 Tab,EXTRACT→「新建集成」按钮,STREAM→流式集成,WRITE→写。

### 7.1 组件选型(已定)

| 用途 | 选型 | 说明 |
|---|---|---|
| 整体框架 | **Vue3 + Element Plus + TS** | 周边 UI(布局/按钮/弹窗/Tab/表单)统一 Element Plus;**不引 antd** |
| **数据网格(渲染大量数据)** | **vxe-table 4.x + vxe-pc-ui** | 行/列**虚拟滚动**,上万行不卡;UI 框架无关,与 Element Plus 共存。自封 `DataGrid.vue` 薄封装。**数据查询场景:全量渲染不分页**(虚拟滚动扛);数据接口场景才分页 |
| 左侧源/模型树 | Element Plus `el-tree`(lazy) | 懒加载:展开源 → introspect 表;节点 icon = 78 handler 的 `icon.svg`、状态点 |
| 连接表单 | JSON-Schema 渲染器(`@form-create/element-ui` 或 form-render) | 由 `GET /data/source/schema/{type}` 驱动,新增源类型前端零改动 |
| filter builder | 自写组件 | 列下拉(来自 introspect)+ 操作符下拉(来自 `GET /data/operators`)+ 值;产出统一 `filters` |
| 原生查询编辑器 | Monaco Editor | SQL / JSON(ES DSL / Mongo pipeline)高亮;内部/AI 取数用 |
| 源类型选择 | 卡片网格 | 用 78 个 `icon.svg` + 能力徽章 |
| 弹窗/布局/分栏 | Element Plus(`el-dialog`/`el-tabs`/`el-splitter` 或 split-pane) | — |

> ⚠️ **不扳** jeecg 的 `JVxeTable` 封装(antd/jeecg 强耦合,会把 antd 拽回来);只采用其底层 **vxe-table** 本体,自己写 Element Plus 风格的薄 `DataGrid.vue`(虚拟滚动 + 服务端分页 + 列从 introspect 动态生成)。
>
> 性能分两种场景:
> - **数据查询(交互探索)**:不分页,`query()` 全量返回 → vxe **虚拟滚动**渲染;行数由用户查询自控,后端可留安全上限兜底。
> - **数据接口(对外)**:**服务端分页** `search(filters,page,pagesize)`,每次只返回一页。
> 海量导出另走流式下载。

---

## 8. 模块分工

| 模块 | 职责 | 状态 |
|---|---|---|
| `module_data` | 数据源 + 数据模型 + 连接器 + introspect/查询端点 | 连接器层**已建**,模型/端点待建 |
| `module_task_schedule` | + `data_integration` 模板 + `compile_to_dlt` runner | 调度底座已有,加组件 |
| `module_dataapi` | Data API spec + 动态路由 + 安全 | 新建 |
| `module_ai`(Agno) | AI 取数(NL→原生查询)+ 转换 codegen | 已集成 Agno,加工具 |
| 前端 | 数据管理视图 | 新建 |

---

## 9. 里程碑

```
M1  module_data 后端:DataSource/DataModel 模型+DAO+service + 端点(types/schema/test/introspect/query/search)+ 字段白名单
M2  前端:三栏布局 + schema 连接表单 + 左树(源→模型)+ 基本信息 Tab
M3  数据查询 Tab:filter builder + 数据网格 + 分页 + 原生编辑器
M4  数据集成:data_integration 任务模板 + compile_to_dlt runner,挂 module_task_schedule(批)
M5  module_dataapi:filter-only Data API spec + 动态路由 + 缓存/限流/脱敏/多租户
M6  AI 取数:Agno NL→原生查询(introspect→生成→预览→存为 native API)
M7  流式集成:binlog/kafka 长驻 worker;e2e + 数据兼容验证
```

---

## 10. 关键决策(已定)

1. 对外接口只放声明式 `filter`;原生查询仅内部;AI 取数走"生成原生查询→预览→执行"口子。
2. 数据集成 = 任务调度组件(不自建 ETL 引擎),ETL spec 编译进 dlt 执行。
3. 连接器层 connection-centric;数据模型(表/集合)= 引用源 + object + 规则的独立实体。
4. 能力位(连接器)∩ auth(模型)驱动前端 Tab/按钮显隐。
5. 向量库委托 Agno;ES 半 engine 不用(原生 client)。
6. 前端:**数据网格用 vxe-table(虚拟滚动,扛大量数据)**,周边用 Element Plus;不扳 jeecg 的 JVxeTable 封装(避免引回 antd)。
```
