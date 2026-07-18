# 设计文档:数据目录检索收窄(Catalog Retrieval)—— 全量注入 → 向量 Top-K

> 状态:草案 / 待评审
> 范围:`module_ai`(上下文装配 `build_data_catalog`、chat_services)、`module_data`(data_model 同步钩子)、复用 `module_rag`(embedding + 向量检索)
> 参考:WrenAI「intent → 向量检索相关表 → 生成」;Anthropic「别让 Agent 在百万字段硬搜,先收窄到几十个精选文件」。

---

## 1. Context

现状 `build_data_catalog()` 每轮把**最多 30 源 × 12 表**的清单塞进 system prompt,认源靠 LLM 自己扫。两个问题:
- **不随规模伸缩**:数据源/表一多,常驻 token 线性涨、且信息发散(大部分表和当轮问题无关)。
- **只有表名没有列**:agent 认出表后仍要 `get_table_schema` 补列,多一轮往返。

而 ezdata **已经有向量检索基建**(`module_rag`:embedding + ES8 向量库 + `retrieve()`,用于 KB/解法),只是没用在**表/字段选择**上。本设计把"全量灌目录"换成"按问题向量检索 Top-K 相关表",对齐 WrenAI 的 `intent→retrieve→generate`,兑现前几轮讨论的"省 token + 聚焦"。

## 2. Goals / Non-goals

**Goals**
1. 数据目录注入从「全量」改「按当轮问题检索 Top-K 表(带关键列)」,常驻 token **随 K 恒定、不随总表数涨**。
2. 复用 `module_rag` 的 embedding/向量库,不新建检索引擎。
3. **永不比现状差**:检索不可用/小库时自动回退当前全量行为。

**Non-goals(本期不做)**
- 不改 agent 的工具与漏斗(list_datasources/get_table_schema 仍在,做兜底)。
- 不做指标/技能的统一检索(预留扩展位,见 §10)。
- 不引入新 embedding 依赖(复用 RAG 已配的 embedding 兜底)。

## 3. 原则
- **分层**:源级(便宜、常驻)+ 表级(检索、Top-K)+ 钻取(工具、按需)。
- **收窄不遮蔽**:检索没命中的表,agent 仍能用工具钻取(follow-up/漏检兜底)。
- **就近同步**:data_model 变更即增量更新索引;失败不影响对话。

## 4. 架构:三层目录

```
Tier A 源级(常驻,极小):列出所有可访问数据源 code+name+type(不含表)
        —— 让 agent 知道"有哪些源",几百 token 封顶
Tier B 表级(按问题检索 Top-K):向量检索与当轮问题最相关的 K 张表,
        注入 表名=业务名 + 关键列(带描述)+ 备注 —— 顺带省掉 get_table_schema 一轮
Tier C 钻取(按需,工具):list_datasources / get_table_schema —— 检索漏掉的照旧能查
```

## 5. 索引设计(复用 module_rag)

**索引单元 = 一个 data_model(表)**。文档文本(供 embedding):
```
数据源 {source_name}({source_type}) · 表 {object_name} · 业务名 {model_name}
字段: col1(desc), col2(desc), ...        # data_model 已存的列元数据;缺则留空
备注: {remark}
```
元数据:`{datasource_code, object_name, model_id, tenant_id}`。

**存储**:独立系统索引(如 ES `ez_catalog_index`),**复用 module_rag 的 embedding 客户端与 ES 连接**,但与用户 KB dataset **物理隔离**(内容异构、生命周期不同,不污染用户知识库)。
> 备选:在 module_rag 里注册一个每租户的系统 dataset `__catalog__`,复用 `retrieve(dataset_ids=[__catalog__])`。二选一按 rag 现有抽象哪个改动小。

**Embedding**:复用 `AiConfig`/RAG 兜底 embedding(DashScope 等);Contextual 前缀已含源上下文,利于召回。

## 6. 同步(增量 + 全量)

- **增量**:`data_model` 保存/停用/删除 → upsert/delete 对应索引文档(挂在 model service 的写路径;异步、失败仅告警)。
- **全量重建**:一个命令/任务 `rebuild_catalog_index(tenant?)`,首次上线或漂移时跑。
- **租户隔离**:文档带 tenant_id,检索按 tenant 过滤(超管 bypass 同现有)。

## 7. 检索与注入

**新增** `CatalogRetrievalService.retrieve_tables(question, scope_codes, k=8)`:
- 向量检索 `ez_catalog_index`(按 tenant + scope_codes 过滤)→ Top-K 表文档。
- 返回结构化 `[{datasource_code, object_name, model_name, columns, remark}]`。

**改造** `build_data_catalog(allowed_codes, *, question=None, k=8)`:
- `question` 有值且索引可用 → 产出 **Tier A(源级全列)+ Tier B(Top-K 表带列)**。
- `question` 为空 / 索引不可用 / **总表数 ≤ 阈值(如 20)** → **回退当前全量行为**(小库直接全给更简单,大库才检索)。

**改造** `chat_services` / `_build_agent`:把 `chat_req.message`(可选拼最近 1–2 轮用户话,缓解 follow-up)作为 `question` 传入。

## 8. Token / 伸缩分析

| | 现状(全量) | 本设计(检索) |
|---|---|---|
| 常驻规模 | 随源×表 线性涨 | **Tier A(源数)+ Tier B(K 恒定)**,与总表数无关 |
| 相关性 | 全表名混杂 | Top-K 命中表 + **关键列**(通常省掉一轮 get_table_schema) |
| 小库(≤20 表) | 直接全给 | 同现状(阈值回退) |

净效果:小库不变、**大库显著收窄且更准**,并可能减少工具往返。

## 9. 回退与护栏(永不比现状差)
- 索引服务异常/为空 → try/except 回退全量 `build_data_catalog`(现有实现原样保留为 fallback)。
- 检索 Top-K 后,**Tier C 工具永远在**:follow-up 或漏检时 agent 仍能 `list_datasources/get_table_schema` 钻取。
- 阈值守卫:表少时不启用检索,避免"为收窄而收窄"。

## 10. 扩展位(与其它设计对齐,本期不做)
同一 `ez_catalog_index` 后续可容纳**指标**(见 semantic-metric-layer-design)与**技能描述**,做**统一检索**:一次向量查询同时召回"相关表 / 相关指标 / 相关技能",彻底把"全量灌目录 + 全量列技能"都换成按需召回。本设计的索引与检索接口按此预留(文档带 `unit_type: table|metric|skill`)。

## 11. 分阶段
- **Phase 1**:`ez_catalog_index` + `CatalogRetrievalService`(复用 rag embedding/ES)+ 全量重建命令 + `build_data_catalog(question=)` 改造 + chat_services 传参 + 阈值/异常回退。种子/demo 库建索引验证。
- **Phase 2**:data_model 写路径增量同步钩子;follow-up 检索查询带历史。
- **Phase 3**:统一检索(表+指标+技能)。

## 12. 验证
1. **回退安全**:关掉索引(或空索引)→ 对话与现状完全一致(全量目录)。
2. **收窄正确**:大库(造 50+ 表)问「贵州茅台日线」→ 注入的 Tier B 命中 `fin_stock_daily` 等相关表、且不含无关表;常驻字符数明显小于全量。
3. **省往返**:Tier B 已带关键列时,agent 直接写取数、少调一次 get_table_schema。
4. **漏检兜底**:问一个检索没召回的冷门表 → agent 用 get_table_schema 仍能取到。
5. **scope/tenant**:应用绑定 3 个源时,检索只在这 3 个源内;跨租户不串。
6. **e2e**:兜底模型对比"检索目录 vs 全量目录"的取数正确率、工具轮数、常驻 token。

## 13. 风险
| 风险 | 缓解 |
|---|---|
| follow-up 短问检索不到相关表 | 查询拼最近 1–2 轮用户话;Tier A 常驻 + Tier C 工具兜底 |
| 索引与 data_model 漂移 | 写路径增量同步 + 全量重建命令;检索仅作"优先召回",钻取兜底 |
| embedding 依赖/成本 | 复用 RAG 已配 embedding;批量/缓存;异常回退全量 |
| 小库过度设计 | 表数阈值守卫,≤20 直接全量 |
| 列元数据缺失(某些源没建模列) | 文档列可空,退化为"表名+业务名"召回,不影响可用性 |
