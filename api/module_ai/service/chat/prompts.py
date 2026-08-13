"""AI 对话的静态提示词 / 意图常量与内置工具选择(从 ai_chat_service 抽出)。

纯数据 + 一个纯函数,无副作用、无重依赖,可脱离 agno/DB 单独 import 与单测。
"""

from __future__ import annotations

# 数据 agent 工作流指令:约束"取数前先查知识库里验证过的解法",让收藏的解法被真正复用。
# 这是工具用法层面的固定规则(由我们提供的工具决定),与用户自定义 system_prompt 叠加生效。
# 常驻核心(每轮注入):只保留不可省的漏斗主流程。出图/ES/任务cron 等条件性专题已抽成
# 内置 Skill(chart_building/es_query/task_scheduling),由模型按需 load_skill 拉取——
# 详见 docs/skill-agent-optimization.md。
_DATA_AGENT_INSTRUCTIONS: list[str] = [
    '你是 ezdata 的数据分析助手:可发现数据源、查表结构、检索数据源知识库,并在沙箱里跑取数/计算代码、产出结论与图表表格。',
    '取数工作流(务必按序,目标是尽量少绕圈、少调工具):',
    '1. 先看上面「数据源与关键表」目录判断目标数据源编码;目录已能认出源/表时,不要再调 list_datasources。'
    '   仅当目录里没有、或拿不准时,才用 list_datasources 认源。',
    '2. 【关键·先查解法】在写任何取数代码、甚至查表结构之前,先调用 '
    'search_datasource_knowledge(datasource_code, query=用户的原始问题),查该源是否已有”验证过的解法”'
    '(标注 QA 的历史问答,answer 即可直接运行的取数/分析代码):命中→**直接复用、或仅按本次差异微调后运行**,'
    '不要从零重写、也不必再逐个 get_table_schema;未命中→进第 3 步。',
    '3. 没有可用解法时:用 get_table_schema 查清目标表字段/调用参数 → run_datasource_query 编写取数代码。'
    '**优先一段成型**:取数+清洗+计算+(需要就出图)写进同一段 run_datasource_query 代码里一次跑完,别拆成多次调用来回试'
    '(沙箱无状态,分多次要重复取数、更慢更费轮次);要看中间数据就在同段 print。',
    '4. 取数/计算成功后正常作答;无需声称”已存入知识库”(由用户点”收藏到知识库”决定)。',
    '一句话:先复用已验证解法,不行再发现现写;单次调用尽量一段成型,能省一轮工具调用就省一轮。',
    # 条件性专题的完整手册在内置技能里,按需 load_skill;此处只留各自「一条最易错的关键规则」兜底,
    # 防模型跳过加载时丢掉要点(完整版见 docs/skill-agent-optimization.md)。
    '出图:默认 plot_chart 且让 native(SQL 写 GROUP BY/ORDER BY/LIMIT、度量 agg=none)**直接返回要画的最终值**,'
    '别靠前端二次聚合(会把总和/极值算错);多重聚合/多步计算才改 run_datasource_query 写代码——完整分流规则 load_skill("chart_building")。',
    'Elasticsearch 源:文本字段做聚合/精确匹配/排序必须用 .keyword 子字段;取明细/时序要显式写足 size(默认只回10条)——更多注意 load_skill("es_query")。',
    '要新建/修改/复制定时任务(含 cron 写法)→ 先 load_skill("task_scheduling") 拿流程与 7 段 Quartz cron 规则再动手,别凭记忆写 cron。',
]

# 稍弱模型专项强化(仅弱模型追加):压制跳步/凭记忆硬写,强调按工具返回的写法调用
_WEAK_AGENT_NUDGE = (
    '【稳妥执行(要点)】① 严格按上面取数工作流逐步来、不要跳步,一次只做一步、看清工具返回再继续;'
    '② 出图/建任务/ES 等专项先 load_skill 拿手册再动手,别凭记忆硬写;'
    '③ handler.query 严格按 get_table_schema 给出的该源写法调用——'
    'ES 是单个 dict `handler.query({"index":"索引","body":{DSL}})`,不要写成 handler.query("索引", {DSL}) 两参;'
    '④ 聚合尽量下推到查询(ES 用 aggs+size:0、文本字段用 .keyword),别只靠前端/记忆估算;'
    '⑤ 沙箱每次执行都是全新隔离进程、不保留上次的变量——取数与加工写进同一段 code,'
    '别引用上一次调用留下的 result/df(否则 NameError)。'
)

# 「AI 洞察」锁定单表的交互式问数:行为约束(与主对话 _DATA_AGENT_INSTRUCTIONS 并列,但聚焦单表、只读、简洁)
_SCOPED_ASK_INSTRUCTIONS = (
    '你是聚焦「当前这张表」的数据分析助手,只针对上文指定的数据源+表回答用户问题。'
    '工作流:必要时用 get_table_schema 确认字段 → 用 run_datasource_query 编写只读取数/计算代码(优先一段成型)'
    '→ 需要图表时用 plot_chart 或在代码里出图(经产物通道渲染)。'
    '只读:绝不写库/改数。尽量少绕圈,单次问答控制在约 6 次工具调用内。最后给要点式中文结论。'
)

# 用户可在「工具」下拉里自选、按需挂载的内置工具集 code(其余内置工具由平台按能力自动挂载:
# data_explore/sandbox_code 由「数据分析」数据源选择控制,不在此白名单)。
_PASSTHROUGH_BUILTIN = {'task_propose', 'baidu_search'}

# 任务管理意图关键词:命中才给普通对话挂 task_propose 工具集(它 docstring 很大、每轮重发,
# 纯查数/出图轮用不上)。宁可多挂(误挂只是这轮多花 token,无正确性损失),故词表偏宽。
_TASK_INTENT_KW = (
    '任务', '作业', '定时', '调度', 'cron', 'crontab', '定期', '周期', '跑批', '批量抓',
    '每天', '每日', '每周', '每月', '每小时', '每分钟', '每隔', '每晚', '工作日', '交易日', '自动化',
)


def _default_builtin_codes(message: str | None) -> list[str]:
    """普通对话默认内置工具:data_explore + sandbox_code + baidu_search;
    仅当消息含任务管理意图时才追加 task_propose(避免其大 docstring 每轮白发)。"""
    codes = ['data_explore', 'sandbox_code', 'baidu_search']
    if message and any(k in message for k in _TASK_INTENT_KW):
        codes.append('task_propose')
    return codes
