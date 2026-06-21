# DAG 工作流编排 重构方案

> 目标:在现有任务调度模块(`module_task_schedule`)之上,增加 DAG(有向无环图)工作流编排能力 ——
> 多任务按依赖关系串/并行执行、可视化画布编辑、运行态监控。不引入重型外部引擎,复用现有 Celery + runner 执行底座。

---

## 1. 现状(代码已核实)

| 维度 | 现状 |
|---|---|
| 执行底座 | ✅ 扎实:APScheduler(cron)→ `dispatch.run_task` → Celery 队列 → `executor.execute_task` → `runner.run()` → `TaskInstance` 记录状态。多租户、重试、告警钩子齐全。 |
| Runner 注册表 | ✅ `register_runner('Template')` + `BaseRunner` + `get_runner`;已有 PythonTask / ShellTask / DataIntegrationTask。无状态、与编排解耦。 |
| 单任务 | ✅ 完整:CRUD、单次/定时触发、实例记录、明细日志(DB/ES)。 |
| DAG 占位 | ⚠️ 仅 3 个占位:`Task.task_type=2`(dag工作流)、`TaskInstance.parent_id`、`TaskInstance.node_id`。**背后零逻辑**。 |
| DAG 定义表 | ❌ 无 node/edge/依赖表。 |
| 编排引擎 | ❌ 无依赖解析、无上游→下游触发、无 DAG 运行实例跟踪。 |
| 前端画布 | ❌ 无。任务管理只有表单/列表。 |

**结论**:执行核心(Celery + runner + 实例记录)可直接复用,编排层是绿地新建。`execute_task(task_id, instance_id)` 的契约天然支持"一个节点一次执行",缺的是**节点依赖解析 + 事件驱动的下游触发 + DAG 运行态**。

## 2. master 分支 DAG 实现评估(原版 ezdata 生产代码)

**master 上已有一套完整可用的 DAG**,是本次重构最直接的参照(很多可移植):

- **前端**:`web/src/views/task/dag_task/dag-editor/`(**AntV X6**,`graph/Node.vue` 自定义节点 + `dag-editor.vue` + `DagRunningModal`/`NodeInfoTab`)。✅ 印证选型;运行态靠前端轮询 `get_dag_task_node_status`(按 `parent_id` 聚合节点实例)。
- **DAG 工具**:`api/utils/dag.py` 的 `DAG` 类(`add_node/add_edge(加边即校验防环)/predecessors/downstream/all_downstreams/topological_sort/ind_nodes/validate`)—— 成熟,**可直接复用**。
- **后端编排**:`api/tasks/dag_tasks.py`:`dag_task` 解析 X6 cells(`shape: container-node|edge`,`data.params={template_code, task_conf, retry, countdown, error_type, label}`)→ `CeleryDag` 构造 **静态 Celery Canvas**(按拓扑分层 `group | group`)或单进程顺序跑;节点 = `dag_node_task`(查 runner_dict 执行)。`run_type`:1 分布式 / 2 单进程。

### 优化点(master 实现的问题,本次应修掉)

| # | 问题 | 影响 | 改法 |
|---|---|---|---|
| 1 | **DAG 主状态过早置成功**:`dag_task` 提交 canvas(异步)后**立刻** `status=SUCCESS, progress=100`,节点还没跑;真实进度逻辑被注释,只能靠前端轮询 | 主实例状态/进度失真,失败不汇总 | **事件驱动**:末节点完成回填终态,失败聚合为失败 |
| 2 | **失败语义反了**:`if error_type != 'break': raise e` —— `'break'` 反而吞异常、下游照跑;非 break 才中断 | 中断/继续控制混乱,命名与行为相反 | 明确 `fail_fast`/`continue`,下游正确置 `SKIPPED` |
| 3 | **静态 Canvas 的层屏障浪费并行**:`group \| group` 按拓扑层串联,下游要等**上一整层**全部完成,即便只依赖其中一个;菱形依赖尤甚 | 快分支被慢的无关分支拖住 | **事件驱动 `advance_dag`**:节点只等**直接上游**完成即触发,按真实依赖并行 |
| 4 | `schedule_node` 递归 + `al_schedule_nodes` 边遍历边改,逻辑脆弱;残留 `print` 调试 | 可维护性差 | DB 状态机 + 拓扑就绪判定,逻辑直白 |
| 5 | 进度只能前端轮询(后端不维护) | 无后端可观测/告警依据 | 后端按 `已完成/总数` 实时维护 DAG run 进度 |
| 6 | 无"从失败节点重跑" | 整图重跑,浪费 | 重置失败节点及其下游重跑 |
| 7 | `once={'graceful': True}` 用全参做幂等键 | 可能误去重 | 幂等键用 `dag_run_id + node_key` |
| 8 | 无条件分支 / 无节点间传参(XCom) | 数据管道串联弱 | 边条件 + context 传参(P2) |

**结论**:master 的 **X6 画布 + `utils/dag.py` + 节点=template+runner** 直接移植到 v2.0;**编排引擎换成事件驱动 DB 状态机**(替代静态 Canvas),一举修掉 #1/#2/#3/#5。这正是本方案 §5.2 的设计。

## 2.2 master 前端 DAG 评估(不可直接移植,需重写)

master 前端整套基于**旧项目技术栈**,与 v2.0(Vue3 + Element Plus + JS)不兼容,且本身质量不高:

**技术栈不兼容(必须重写,不能照搬)**
- **UI 库混用**:编辑器用 **Arco Design**(`a-button`/`icon-play-arrow`),弹窗用 **Ant Design Vue + vben**(`BasicModal`/`useModal`/`Modal`/`Icon ant-design:*`/`Authority`/`a-card`/`a-descriptions`)—— 两套 UI + 两套图标混在一起,风格割裂。v2.0 应纯 **Element Plus**。
- **TypeScript**(`lang="ts"`)+ 旧项目组件别名(`/@/components/Modal`、`useMessage`、`v-auth`)—— v2.0 是 JS + RuoYi 体系。
- `graph/Node.vue` 用 **Vue2 Options API** 写,注释还写"用 vue2 写感觉渲染快一些"(无依据),在 Vue3 项目里别扭。

**调试残留 / 逻辑问题(就是你说的"调试")**
- 满屏 `console.log`,还带 `666`/`777` 调试标记:`'init data666'`、`'current666'`、`'click777'`、`'init'`、`'updateStatus'`、裸 `console.log(res)`… 明显的调试遗留。
- **错误处理 = `console.log('error', res)`**,静默失败,无任何用户提示(没有 message 提示)。
- **拼写 bug**:监控弹窗 `selectedNode.stauts`(应为 `status`)→ "任务状态"永远空。
- `selectedNode` 用 `ref('')`(字符串)却当对象用,类型混乱。
- `node.setData({...data}); node.setData({...item})` —— **连续 setData 两次**(先铺旧的再覆盖),冗余。
- 轮询 `setInterval` 靠 `res.is_ok` 标志 `clearInterval`,无退避/超时兜底。

**丑点 / UX**
- **节点图标/状态图标用阿里云远程 CDN 图片**(`https://gw.alipayobjects.com/...`)—— 外部依赖,离线/内网即裂,加载慢,跟 Element Plus 图标不统一。
- 工具栏 **"适应屏幕"和"保存"用了同一个 `icon-save` 图标**(复制粘贴遗留),易混淆。
- "适应屏幕"缩放用 `1 - graph.zoom()` 的 hack(还重复两处),应直接 `graph.zoomToFit()` / `zoomTo(1)`。
- 组件菜单(stencil)是 `v-show` 的浮层 300px + `z-index:999`,布局是拼的,不是干净的侧栏。
- 颜色写死 Antd 调色板(`#52c41a`/`#ff4d4f`…),非 Element Plus 主题变量。
- 拖入节点即 `node:added` 自动触发 `nodeClick`+`nodeDbClick` 弹配置框,体验略突兀。

**可复用/借鉴的(仅 X6 这一层)**
- `@antv/x6` 引擎本身 + `flow-graph` 的画布配置(stencil/history/minimap/snapline/连线规则)思路可参考。
- 设计上"左画布 + 右节点信息/日志"的运行监控分屏、运行态给边加流动虚线动画、按 `parent_id` 拉节点状态 —— 交互思路可留。

**v2.0 前端重写要点(纯 Element Plus + JS)**
1. 只保留 `@antv/x6` + `@antv/x6-vue-shape`;其余全部用 Element Plus 重写(工具栏 `el-button`、弹窗 `el-dialog`、抽屉 `el-drawer`、描述 `el-descriptions`)。
2. 节点用 **Vue3 SFC + Element Plus 图标**(去掉阿里云 CDN 图);状态色用主题变量。
3. **节点配置抽屉直接复用现有任务模板组件**(`getTaskComponent(template_code)`,如 `DataIntegrationTask.vue`)—— 和单任务表单一套。
4. 清除所有 `console.log`;错误统一 `ElMessage` 提示;修 `stauts`、双 `setData`、缩放 hack、重复图标等。
5. 运行监控:左 X6(只读 + 状态着色)+ 右节点详情/日志(复用现有明细日志组件);轮询带超时与退避,DAG 终态由后端事件驱动(配合 §5.2)而非纯前端判定。
6. 保存的图 JSON 精简(只存 node_key/template_code/params/坐标 + edges),不必整存 X6 原始 `toJSON()` 的全部属性。

## 3. 市面工作流组件调研

### 3.1 后端编排引擎

| 组件 | 模型 | 适配度 | 备注 |
|---|---|---|---|
| **Apache Airflow** | Python 定义 DAG + Operator,调度器轮询 + Executor(Celery/K8s) | 参考其**模型与语义**(DAG run / task instance / XCom / trigger rules / backfill) | 重,Python-as-config,自带调度器;直接引入会和现有 Celery/APScheduler 打架 |
| **DolphinScheduler** | DB 存 DAG(process_definition + task_definition + relation)+ Master/Worker,可视化拖拽 | ⭐ **最贴近本项目**:DB 驱动 + 画布 + 分布式 worker,Java | 借鉴其**数据模型与画布交互**;不引入 Java 栈 |
| **Dagster / Prefect** | 资产/流(asset/flow),Python 装饰器 | 参考可观测性、重跑 | 偏 Python 数据栈,生态独立 |
| **Temporal** | 工作流即代码(持久化执行) | 参考可靠性语义 | 重,改变编程模型 |
| **Argo Workflows** | K8s CRD,YAML DAG | 不适用(无 K8s 依赖) | — |
| **n8n / Node-RED** | 节点式低代码,画布原生 | 借鉴**节点+连线交互**与触发器节点 | 偏集成自动化,非批调度 |
| **Celery Canvas**(chain/group/chord) | 代码内静态编排 | 局部可用 | 静态、难做条件分支与 UI 可观测;**不作为主引擎**,只在纯线性子链可选 |

**选型结论(后端)**:**自建轻量 DB 驱动编排器**(DolphinScheduler / Airflow 的模型),跑在现有 Celery 执行层之上。理由与连接器层一致 —— 复用自有底座、避免重型耦合;DB 存图 + 状态便于 UI 观测、重跑、回填。

### 3.2 前端 DAG 画布 —— X6 vs Vue Flow 详细对比(已定:**AntV X6**)

两者都是 MIT、都能在 Vue3 做 DAG,但设计哲学相反:**X6 = 电池全包的图编辑引擎**(编辑能力内建);**Vue Flow = 地道的 Vue3 原生流程图库**(轻,但很多要自己拼)。按本项目 DAG 编辑器的刚需逐项比:

| 维度 | **AntV X6** | **Vue Flow** |
|---|---|---|
| 渲染 | SVG + HTML,自有渲染引擎,MVC(数据/视图分离) | 节点即 Vue 组件(DOM),CSS transform 缩放;最"Vue 化" |
| Vue3 集成 | 框架无关,Vue 节点靠 `@antv/x6-vue-shape`;**命令式 API**(`graph.addNode`/`graph.on`),数据走 `setData`/`change:data` | **原生 Vue3**,节点=SFC,响应式,`useVueFlow()`;DX 最顺 |
| 构建 | TS 写、JS 可用;**Vite 需配 alias**(`@antv/x6`、`x6-vue-shape`,已知坑) | 无特殊构建坑 |
| 拖拽组件面板 Stencil | ✅ **内建** | ❌ 自己实现(drag+drop) |
| 撤销/重做 | ✅ **内建** `graph.history` | ❌ 自己做 |
| 对齐辅助线 snapline | ✅ **内建** | ❌ 无(仅网格吸附) |
| 小地图/缩放控件 | ✅ 内建 | ✅ 独立包 `@vue-flow/minimap`/`controls` |
| 框选/剪贴板/快捷键 | ✅ 内建 | ❌ 多数自己做 |
| 端口 + 连线校验 | ✅ 强(ports/`validateConnection`/磁吸规则) | ✅ handles + `isValidConnection`(够用,需多接) |
| 边路由/导出 PNG/SVG/JSON | ✅ 丰富 + 内建导出 | 一般;PNG 需外接 html-to-image |
| 自动布局 / 防环 | `@antv/layout`;防环自写 | 外接 dagre/elkjs;防环自写 |
| 体积/性能 | 较大;大图(上千节点)更稳 | 核心轻;DOM 节点多了偏重(任务 DAG 几十节点无差) |
| 生态/案例 | AntV(阿里),中英文档全,**企业级 DAG 案例多**(DolphinScheduler 同类);**master 已用它** | 在涨,文档好,但企业调度类案例少 |

| **LogicFlow**(滴滴) | 中 | 流程图框架,BPMN 友好,Vue3 集成历史上略糙 —— 不选 |

**选型结论(前端):定 AntV X6。** 理由:
1. 本项目 DAG 编辑器的刚需 —— **拖拽组件面板 / 撤销重做 / 对齐线 / 小地图 / 连线校验 / 运行态着色** —— 恰好是 X6 全内建,而 Vue Flow 这些基本要全自研;综合工作量 **X6 反而更省**。
2. **master 已用 X6 跑通**,结构与交互可参考(虽代码栈不兼容需重写,见 §2.6),且企业级 DAG 案例多。
3. 节点配置抽屉照样用 Element Plus + 复用现有任务模板组件,X6 只负责画布那层,"命令式 / 非响应式"那点别扭影响有限。

**代价(接受)**:命令式 API、Vite 配 alias、节点内与 Vue 响应式略隔。
**何时才选 Vue Flow**:只要极简编辑器 + 极致 Vue3 可维护性,且愿意自己写面板/撤销 —— 本项目不属于此情形。

来源见文末。

## 4. 选型总结

- **后端**:自建 DB 驱动编排器,复用 Celery + 现有 runner;模型借鉴 DolphinScheduler/Airflow。
- **前端**:**已定 AntV X6**(详见 §3.2 对比)+ `@antv/x6-vue-shape`;画布用 X6,其余 UI 纯 Element Plus,节点配置复用现有"任务模板组件"体系(`templates/*.vue`)。
- **不引入**:Airflow/Dagster/Temporal/Argo 等重型引擎。

## 5. 重构方案

### 5.1 数据模型(图按版本存,Dify/n8n 范式)

**核心思想**:DAG 复用 `task`(task_type=2)做容器(调度/触发/告警/实例全免费);**图作为一个整体文档按版本存**到 `dag_graph`,而不是拆成 node/edge 行。草稿(draft)可变、发布版(published)不可变,正式运行只跑最新发布版。运行态复用 `task_instance`,零新增运行表。

为什么不拆 node/edge 行:画布是文档级原子编辑(拖一下=改一行 JSON),拆行则每次 save 要 diff/upsert 一堆行;且不可变发布版**天然就是运行快照**,改图绝不影响在跑/历史的运行;版本回溯/对比也免费。代价仅"模板被哪些 DAG 引用"这类低频查询,用 JSON 查或发布时写派生索引缓解。

```
task                       -- 复用,task_type=2 即 DAG 容器
  ...(调度/cron/触发/告警/run_queue/重试 全复用普通任务字段)
  published_version_id  -> dag_graph.id   当前生效的发布版(可空=未发布,仅有草稿)

dag_graph                  -- 图文档,按版本存(核心新表)
  id            PK
  dag_task_id   -> task.id
  version       'draft' | 版本号(发布时间戳 / 自增序号)
  status        draft | published | archived
  graph         JSON  整张图:
                {
                  nodes: [{ node_key, name, template_code, params, pos:{x,y},
                            retry, timeout, error_policy:'fail_fast'|'continue' }],
                  edges: [{ source, target, condition? }],
                  viewport: {...}            -- 画布视图态(缩放/位移/X6 渲染细节)
                }
  remark        发布说明
  create_by, create_time
  unique(dag_task_id, version)

dag_node_ref               -- 可选派生索引(发布时顺带写),仅为加速"模板被哪些 DAG 引用"
  dag_task_id, version, template_code
```

> 节点 = `template_code + 内嵌 params`(自包含),**不引用独立 task 行**(避免生命周期耦合)。模板复用现有任务模板注册表(PythonTask/ShellTask/DataIntegrationTask/...)。

**关键流程**
- **编辑**:始终读写该 DAG 的 `version='draft'` 行(无则建);画布即 `draft.graph`,拖拽 = 改这一行。
- **发布**:校验无环 → 复制 draft 为一条不可变 `published` 版(version=时间戳)→ 更新 `task.published_version_id`(并写 `dag_node_ref`)。
- **正式运行**:跑 `published_version_id` 指向的版本;DAG run 实例记 `dag_version_id`,可追溯跑的哪个版本。
- **试运行/调试**:直接跑 `draft`(不发布),run 实例标记来源=draft。
- **回滚**:`published_version_id` 指回某历史发布版(或"恢复历史版为 draft 再发布");版本都在,随时回。
- **历史/对比**:按 `dag_task_id` 列版本,看/diff 任意版。
- **列表**:普通任务列表过滤 `task_type=1`;DAG 列表 `task_type=2`,单开入口。

**运行态:复用 `TaskInstance`,零新增表**
- **DAG run**:一条 `TaskInstance`,`parent_id=NULL`、`node_id=NULL`、`task_id=dag_task_id`,扩展记 `dag_version_id`(跑的哪个图版本)+ 来源(published/draft)。
- **节点 run**:每节点一条 `TaskInstance`,`parent_id=<DAG run id>`、`node_id=<node_key>`。
- worker/进度/起止/result/日志 字段直接复用;前端按 `parent_id` 聚合出一次运行的全部节点状态。

> 不可变发布版 = 免费运行快照:run 只需记 `dag_version_id`,无需再拷贝图。

**三种存储方案对比(最终选第三种)**

| | master(图塞 task.params) | 拆 dag_node/dag_edge 行 | **dag_graph 版本文档(采用)** |
|---|---|---|---|
| 编辑 | 一行,但无版本 | 拆行 upsert,烦 | draft 一行,原子 ✅ |
| 版本/回滚 | 无 | 要另做 | 天然 ✅ |
| 运行一致性 | 实时读会乱 | 要手动快照 | 发布版不可变,免费快照 ✅ |
| 模板用量查询 | 难 | 易 | 较难(派生索引 `dag_node_ref` 缓解) |

### 5.2 执行引擎(编排器)

**事件驱动 + DB 状态机**(不是 Celery Canvas 静态编排):

```
run_dag(dag_task_id, source='published'|'draft'):
  1. 取图:published → task.published_version_id 指向的 dag_graph;draft → version='draft' 行
  2. 建 DAG run 实例(TaskInstance, status=STARTED),记 dag_version_id + 来源
  3. 解析 graph.nodes/edges → 找入度为 0 的根节点 → 逐个 dispatch(复用 dispatch.run_task,带 dag_run_id + node_key)
节点执行(复用 execute_task,节点 run 实例落 parent_id/node_id):
  4. 节点 SUCCESS/FAILURE 后回调 advance_dag(dag_run_id)
advance_dag(dag_run_id):  # 幂等 + 行锁防并发重复派发
  5. 对 DAG run 行加锁;按 run 记录的版本读图 + 各节点最新状态
  6. 找"全部上游已 SUCCESS 且自身未派发"的节点 → dispatch
  7. 若有节点 FAILURE:按策略(默认 fail-fast)标记 DAG run FAILURE,下游标 SKIPPED
  8. 若全部终态且无失败 → DAG run SUCCESS
```

要点:
- **图来源固定**:run 启动即锁定 `dag_version_id`,全程按该版本(不可变发布版)解析,改图不影响在跑的运行。
- **下游触发**:在 `executor.execute_task` 结束处加钩子:若该实例属于某 DAG run(parent_id 非空),调用 `advance_dag`。
- **并行**:`advance_dag` 一次派发所有就绪节点,Celery 天然并发执行。
- **幂等/防重**:`advance_dag` 对 DAG run 行 `SELECT ... FOR UPDATE`;派发前检查节点是否已有进行中/完成实例,避免多个上游同时完成时重复派发同一下游(菱形依赖)。
- **执行复用**:节点跑的还是 `execute_task` + `runner.run()` —— 与单任务**同一条执行路径**,只是多传 `dag_run_id/node_key` 上下文。

### 5.3 调度 / 触发

- **手动**:`run_dag_once(dag_task_id)` → 建 run → 派发根节点。
- **定时**:复用现有 APScheduler(`sys_job` + `invoke_target='...dispatch.run_dag'`),与单任务 cron 同机制。
- **触发方式**沿用 `Task.trigger_type`(1 单次 / 2 定时),DAG 容器任务即 `task_type=2`。

### 5.4 失败语义 / 重试 / 幂等

- **节点重试**:复用 Celery 重试(`retry`/`countdown`),节点级可覆盖。
- **DAG 失败策略**(`dag` 级配置):`fail_fast`(默认,一个失败即终止,下游 SKIPPED)/ `continue`(失败仅阻断其下游,其余分支继续)。
- **边触发规则**(P2,借鉴 Airflow trigger_rules):`all_success`(默认)/ `all_done` / `one_success`。
- **重跑**(P2):从失败节点/指定节点重跑(只重置该节点及其下游)。

### 5.5 节点间数据传递(P2,借鉴 Airflow XCom)

- DAG run 维护一个 `context`(KV,落 DAG run 实例的扩展字段或独立 kv 表)。
- 节点 `runner.run()` 返回值的关键字段写入 context;下游节点 params 支持 `${{ node_key.output_field }}` 模板插值,派发前渲染。
- ETL 场景:上游"抽取"产出表名/路径 → 下游"装载/转换"引用,串成数据管道。

### 5.6 前端画布(AntV X6)

- **画布**:X6 + `@antv/x6-vue-shape`;节点 = Vue 组件(图标 + 模板名 + 状态徽标),端口连线,连线校验(禁止成环 → 提交前 DAG 校验)。
- **节点配置**:双击节点 → 抽屉里渲染**现有任务模板组件**(`getTaskComponent(template_code)`,如 DataIntegrationTask.vue)→ 完全复用已建的低代码/内置表单体系。
- **运行态**:监控视图按 `parent_id` 拉节点实例,节点按状态着色(灰/蓝running/绿/红),点节点看该节点日志(复用现有明细日志);可叠加甘特/拓扑视图。
- **保存**:画布 → `{nodes[], edges[], viewport}` → 写 **draft 版**(`dag_graph` version='draft');点"发布"才生成不可变发布版。
- **版本**:工具栏给"发布 / 版本历史 / 回滚 / 试运行(跑 draft)";运行监控可选某历史版本查看。
- Vite 需为 `@antv/x6`、`@antv/x6-vue-shape` 配 alias(已知坑)。

### 5.7 API(新增 `module_task_schedule` 内)

```
# DAG 列表/容器(task_type=2)
GET    /task/dag/list            DAG 任务分页列表(task_type=2)
POST   /task/dag                 新建 DAG(建 task 容器 + 空 draft)
DELETE /task/dag/{id}            删除

# 图编辑(草稿)
GET    /task/dag/{id}/draft      读草稿图(无则返回空图)
PUT    /task/dag/{id}/draft      存草稿(画布拖拽即存此;校验无环)

# 版本(发布/历史/回滚)
POST   /task/dag/{id}/publish    校验无环 → 草稿发布为不可变版本 → 置为 published_version
GET    /task/dag/{id}/versions   版本列表(draft + 各发布版)
GET    /task/dag/{id}/version/{ver}   读某版本图(查看/对比)
POST   /task/dag/{id}/rollback/{ver}  回滚:将该历史版设为当前发布版

# 运行
POST   /task/dag/{id}/run        正式运行(跑 published_version)
POST   /task/dag/{id}/debug      试运行(跑 draft,不发布)
GET    /task/dag/{id}/runs       运行历史(DAG run 实例列表,含跑的版本)
GET    /task/dag/run/{run_id}    一次运行的全部节点状态(按 parent_id 聚合)
POST   /task/dag/run/{run_id}/rerun   从失败/指定节点重跑(P2)
POST   /task/dag/run/{run_id}/stop    终止(复用实例 stop)
```
权限位:`task:dag:list/edit/publish/run`(并入现有任务调度菜单)。

## 6. 复用与最小改造点

| 复用 | 说明 |
|---|---|
| `execute_task` / runner 注册表 | 节点执行完全复用,**不改 runner** |
| `TaskInstance` | DAG run + 节点 run 都用它(parent_id/node_id 终于派上用场) |
| Celery / dispatch / APScheduler | 派发与定时复用 |
| 任务模板组件(`templates/*.vue`) | 节点配置表单复用 |
| 明细日志 / 告警钩子 / 多租户 | 复用 |

**需新增**:`dag_graph`(图版本文档,draft/published)+ 可选 `dag_node_ref`(派生索引)、`task.published_version_id` 字段、编排器 `dag_orchestrator.py`(`run_dag`/`advance_dag`)、`execute_task` 末尾的 advance 钩子、DAG/版本 服务·DAO·控制器、前端 X6 画布 + 监控视图。

## 7. 分阶段落地

- **P1(MVP,~1.5–2 周)**:数据模型 + 编排器(串行+并行,fail_fast,无条件边)+ DAG CRUD/run/监控 API + X6 画布(增删节点连线、节点配置复用模板组件、保存、手动运行、运行态着色)。能跑通"MySQL抽取 → 转换 → 多目标装载"这类数据管道。
- **P2(~1–1.5 周)**:条件边/触发规则、从节点重跑、节点间 context 传参(XCom 式)、定时 DAG。
- **P3(按需)**:回填/补数(backfill)、节点级 SLA/告警、子 DAG、版本与审计。

## 8. 风险与权衡

- **并发派发重复**:菱形依赖下多个上游同时完成 → 必须行锁 + 幂等检查(已纳入 `advance_dag`)。
- **Worker 崩溃/丢实例**:节点实例 STARTED 卡死 → 需超时巡检(复用现有实例巡检或加心跳)。
- **图校验**:提交即检测环(拓扑排序失败则拒绝);运行期再校验一次。
- **图存储**:采用 `dag_graph` 版本文档(draft/published),发布版不可变 → 编辑原子、运行一致、版本可回溯;"模板被哪些 DAG 引用"用 `dag_node_ref` 派生索引或 JSON 查兜底。
- **X6 学习成本**:比 Vue Flow 略高,但 DAG 内建能力省后续大量自研;若赶原型可先 Vue Flow 再迁。
- **不做的事**:不引入 Airflow/Temporal;不用 Celery Canvas 做主编排(静态、难观测)。

---

### 参考来源
- [AntV X6 — JavaScript Diagramming Library](https://x6.antv.vision/) · [GitHub antvis/X6](https://github.com/antvis/X6)
- [Vue Flow — Vue3 Flowchart Library](https://vueflow.dev/) · [Quickstart & Best Practices](https://dev.to/monsterpi13/vue-flow-quickstart-and-best-practices-482k)
- [LogicFlow Team](https://github.com/Logic-Flow)
- Apache Airflow(DAG / task instance / XCom / trigger rules 模型)、Apache DolphinScheduler(DB 驱动 + 画布 + Master/Worker 模型)— 作为后端编排模型参考
