"""ezdata.utils —— 纯工具(过滤 DSL 适配、只读护栏、JSON 清洗、序列化)。

- etl_util:只读校验 / json_safe 清洗 / 记录序列化 / 流式语句 / 错误截断;
- query:过滤规则 DSL → 各源查询(sqlalchemy/ES/Mongo)适配 + 查询串解析 + 操作符表。
"""
