# 设计文档:内置 Skill 化 + Skill×数据绑定 —— 精简 agent 常驻上下文

> 状态:草案 / 待评审
> 范围:`module_ai`(对话 agent 装配、Skills)、`module_data`(数据源/模型元数据,仅读)
> 参考:Anthropic《How Anthropic enables self-service data analytics with Claude》——知识型/流程型 Skill、漏斗式渐进披露、"无 Skill 21% → 有 Skill 95%+"。

---

## 1. 背景与问题

当前普通对话每轮往上下文里**恒定注入**三块,其中一大半是"条件性知识却每轮全额付费":

| 来源 | 内容 | 注入时机 | 估算 |
|---|---|---|---|
| `ai_chat_service._DATA_AGENT_INSTRUCTIONS` | 取数流程 + 出图分流 + ES 坑 + 任务/cron 规则 | **每轮常驻** | ~900–1100 tok |
| `data_agent_tools.build_data_catalog()` | 数据源 + 已建模表清单 | **每轮常驻** | 数百~1K+(随源数) |
| `skill_tools.build_skill_catalog()` | 所有启用技能的 code+名+描述 | **每轮常驻** | 随技能数线性涨 |
| 工具 schema(`plot_chart`/`run_datasource_query` docstring) | 出图/取数用法 | 每轮随工具定义 | plot_chart 一段就很长 |

**核心问题**:`_DATA_AGENT_INSTRUCTIONS` 把「不可省的核心流程」和「条件性专题(出图、ES、建任务/cron)」混在一个常量里。用户只是"查贵州茅台今天涨跌"时,cron 规则、出图分流、ES `.keyword` 坑一条都用不上,却每轮全额付。

**同时**:刚落地的 Skill 体系与数据是**松耦合**——技能不知道自己"服务于哪个数据源/模型",数据侧硬知识反而堆在常驻大指令里,没走 Skill 的按需通道。

## 2. 目标 / 非目标

**目标**
1. 把 `_DATA_AGENT_INSTRUCTIONS` 里的条件性专题拆成**内置 Skill**,按需 `load_skill` 加载,常驻只留核心。
2. 让 Skill **绑定数据源**,知识型技能只在相关源进入 scope 时才被感知(不无脑塞全部)。
3. 收益优先级:**聚焦度/准确率 > 可维护性 > 省 token**(见 §7 权衡)。

**非目标(本期不做)**
- 语义/指标层(compiled metrics)——另立项。
- 评测 harness(离线 eval + 纠正收割)——另立项。
- 二进制资源 / 沙箱文件系统——受沙箱限制,维持"脚本即文本"。

## 3. 设计原则(承接文章)

- **漏斗式渐进披露**:常驻只放"收窄范围"的核心;细节按需拉。
- **两类 Skill**:
  - **流程型(process)**:一次查询/建任务的标准步骤 + 可复用分析模式。全局适用 → 常驻在 L1 目录。
  - **知识型(knowledge)**:某数据源/域的口径、坑、专属取数法。**绑数据源** → 该源被触及时才浮现。
- **内置 Skill(`built_in=1`)**:出厂自带、不可删、code 锁定,内容可微调。

## 4. 架构设计

### 4.1 三层结构(改造后)

```
常驻(每轮):
  ├─ build_data_catalog()                # 数据源/表目录(收窄用,保留)
  ├─ _DATA_AGENT_INSTRUCTIONS(瘦身版)   # 只剩核心漏斗流程 ~150 tok
  └─ build_skill_catalog()               # 只列 流程型 + 命中 scope 的知识型
按需(load_skill 触发):
  ├─ chart_building / task_scheduling / es_query …(内置流程/知识型正文)
  └─ 每源知识型技能正文 + 附加文件(read_skill_file)
```

### 4.2 Skill × 数据绑定规则

| 技能类型 | 是否进 L1 目录 | 触发被感知的方式 |
|---|---|---|
| 流程型(process) | **总是** | 常驻目录 |
| 知识型(knowledge)+ 绑定源 | **仅当绑定源 ∈ 当前 scope** | ① 应用绑定了该源;② `search_datasource_knowledge(该源)` 返回里追加"本源可用技能 X,可 load_skill('X')" |

- **普通对话**(scope=全部):知识型技能**不无脑进目录**,而是在 agent 调 `search_datasource_knowledge(源)` 认源后,由返回顺带告知"该源有专属技能"。这样技能数量涨,常驻目录也不膨胀,且发现时机贴合漏斗(先认源→再拿该源专属操作手册)。
- **应用对话**(scope=绑定的若干源):这些源的知识型技能直接进目录。

### 4.3 内置 Skill 清单

| code | 类型 | 从哪搬来 | 何时被 load |
|---|---|---|---|
| `data_query_flow` | process | 取数漏斗核心 + 可复用分析模式(留存/漏斗/同环比) | 复杂分析时;核心步骤仍留常驻 |
| `chart_building` | process | 现 3.5 段:plot_chart vs 代码分流 + native 规则 | 用户要出图 |
| `task_scheduling` | process | 任务 propose 流程 + 7 段 Quartz cron 全套规则 | 用户要建/改任务 |
| `es_query` | knowledge(按源类型) | ES 的 `.keyword`/size/Top-N 坑 | 目标源是 ES |
| `<source>_guide` | knowledge(按源) | 每源/每域口径与专属取数法(demo 财经先配 1 个) | 该源进 scope |

> 拆分后 `_DATA_AGENT_INSTRUCTIONS` 只保留:角色定义 + "先查解法→查结构→取数"主流程 + 一句"需要出图/建任务/ES 细节时,先 load_skill 对应技能"。常驻从 ~1K 降到 ~250 tok。

## 5. 数据模型改动(`ai_skill`)

新增两列(mysql + pg + 运行库 ALTER):

| 列 | 类型 | 说明 |
|---|---|---|
| `skill_type` | varchar(20) default 'process' | 'process' 流程型 / 'knowledge' 知识型 |
| `datasource_codes` | varchar(500) | 知识型绑定的数据源 code(逗号分隔);为空=不绑 |

- 复用已有:`content`(SKILL.md)、`resources`(附加文件)、`ref_skills`(软引用)、`built_in`、`status`。
- VO 同步加 `skill_type` / `datasource_codes`;前端 SkillEditor 基础信息加"类型"下拉 + "关联数据源"多选(仅知识型显示)。

## 6. 装配逻辑改动

### 6.1 `AiSkillService.resolve_agent_skills(db, skill_ids, *, scope_codes=None)`
- 新增 `scope_codes` 入参(当前对话可访问的数据源 code)。
- 每个技能 dict 增 `skill_type` / `ds_codes`;`catalog` 判定改为:
  - process → `catalog=True`
  - knowledge → `catalog = bool(set(ds_codes) & set(scope_codes or []))`(普通对话 scope 传 None → 知识型 catalog=False,靠 §6.3 浮现)
- BFS 软引用展开逻辑不变(被引用的仍 `catalog=False` 但可加载)。

### 6.2 `build_skill_catalog(skills)`
- 不变(已按 `catalog` 过滤)。分组展示可选:`### 流程技能` / `### 数据源专属技能`。

### 6.3 `search_datasource_knowledge(datasource_code, query)`(data_agent_tools.py)
- 末尾追加一段:该源若有 `skill_type='knowledge'` 且绑定含此源的启用技能 → "本数据源可用专属技能:X —— load_skill('X') 获取操作手册"。
- 这样普通对话里知识型技能"认源即浮现",无需常驻。

### 6.4 `_build_agent` / `chat_services`
- 把 `datasource_scope` 作为 `scope_codes` 传入 `resolve_agent_skills`。
- `_DATA_AGENT_INSTRUCTIONS` 换成瘦身版常量。

## 7. Token 账与权衡(务必对齐预期)

- **省的是真的**:简单查询占多数,chart/task/es 三包挪走,这些轮每轮省 ~700 tok。
- **抵消项 1——多一跳**:需要那包知识时 +1 次 `load_skill` 往返。净收益取决于流量结构(查数多、建任务少 → 划算)。
- **抵消项 2——prompt caching**:若 Anthropic 提示缓存生效,常驻大指令在会话内近乎免费,省钱动机减弱。**落地前先确认缓存是否开启**(现状仅确认禁并行工具调用,缓存未知)。
- **稳赚的收益(不受缓存影响)**:
  - **聚焦/准确率**:模型每轮不用再读 cron/ES 规则,注意力集中(对应文章 21%→95% 的机理是"收窄搜索空间",非省钱)。
  - **可维护**:出图/cron 规则改一处 skill,不动巨型常量;还能在 UI 里编辑、导入导出、被应用按需绑定。

> 结论:本方案**首要卖点是聚焦度+可维护性**,token 是顺带且有前提。评审时不要以"省多少钱"为唯一 KPI。

## 8. 分阶段落地

**Phase 1(最小、最稳,先验证价值)——拆 `task_scheduling`**
- 最肥、最少用、最独立(与取数流程解耦)。
- 只做:建内置 skill `task_scheduling`(搬 cron/propose 段)→ 从 `_DATA_AGENT_INSTRUCTIONS` 删对应段 → catalog 里模型能按需 load。
- 无需 schema 改动(process 型,不绑源)。验证:建任务对话仍正常(模型先 load_skill('task_scheduling') 再 propose);普通查数轮常驻明显变短。

**Phase 2——拆 `chart_building`,加 schema**
- 搬出图分流段;顺便 `plot_chart` docstring 瘦身(细节移进 skill,工具描述只留签名+一句话)。
- 加 `skill_type` 列。

**Phase 3——知识型 + 数据绑定**
- 加 `datasource_codes` 列;`es_query` + demo 财经 `<source>_guide`;`search_datasource_knowledge` 追加浮现逻辑;`resolve_agent_skills` 加 `scope_codes` 过滤;SkillEditor 加类型/关联源 UI。

## 9. 风险与回滚

| 风险 | 缓解 |
|---|---|
| 模型不主动 load 对应 skill,导致该 load 没 load(如漏了 cron 规则乱写) | catalog 描述写足触发条件;瘦身版核心指令保留一句"建任务/出图前必先 load 对应 skill";Phase 1 先小范围观察命中率 |
| 多一跳增加延迟 | 只对低频专题(task/chart)按需化;高频取数核心留常驻 |
| 内置 skill 被误删/改坏 | `built_in=1` 不可删、code 锁定;正文改动可回滚(导出备份) |
| 内置 skill 内容与代码规则漂移 | 承接文章的"防过期":后续把内置 skill 纳入 seed/版本;改相关规则时同步改 skill(暂靠约定) |

**回滚**:每个 Phase 独立;把搬出的段落写回 `_DATA_AGENT_INSTRUCTIONS`、停用对应内置 skill 即可复原。

## 10. 验证方式

- **常驻体量**:对比改造前后一轮普通查数请求的 system 段字符数/tok。
- **功能回归**(兜底模型 modelId=0):
  - 建任务:"每天 9 点抓一次 X" → 模型 `load_skill('task_scheduling')` → propose,cron 为 `0 0 9 * * ? *`。
  - 出图:"画个近一年走势" → `load_skill('chart_building')` → 正确分流 plot_chart/代码。
  - ES 源:terms 聚合走 `.keyword`(load `es_query` 后)。
  - 普通查数:"贵州茅台今天涨跌" → 不触发上述任何 skill,常驻更短。
- **准确率**(有 eval 后):对建任务/出图两类做前后对照。

## 11. 后续(超出本文范围,列出承接方向)

- 语义/指标层(文章信任度最高一层):命名指标=定义+绑定模型,agent 优先用。
- 评测 harness:离线 QA 集 + ⭐收藏/对话纠正 → 评测样本;来源标注页脚。
- 可选对抗性审查子 agent(+6% 准确率 / +32% tok / +72% 延迟,做成高风险开关)。
