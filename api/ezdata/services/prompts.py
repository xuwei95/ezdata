"""ezdata 查询/转换提示词构造(纯函数,无 db、无 AI 调用)。

给定 handler(数据源连接器) + 表名 + 自然语言需求 → 生成喂给 LLM 的提示词。
AI 的"执行"(模型配置、调用)由 web/cli/mcp 各自处理;这里只负责"怎么问"这一数据语义部分,
使 cli/mcp/skill 做 NL→查询时可直接复用同一套跨源提示词逻辑。
"""

import json
from typing import Any

from ezdata.handlers import Capability

# 不指定主表时,最多喂给 AI 的表数(保护 token,大库会截断并提示)
SCHEMA_TABLE_CAP = 40
# native 为 SQL 文本的源族(出 SELECT);其余非 api 源统一走"原生查询"(各用各自查询语法)
_SQL_FAMILIES = {'rdbms', 'timeseries'}


def build_query_prompt(handler: Any, object_names: list[str] | None, question: str) -> str:
    """跨源查询提示词入口:按源族分流(api 出函数调用 JSON / SQL 族出 SELECT / 其余出原生 DSL)。"""
    family = getattr(handler, 'family', '')
    # api 族(akshare/ccxt 等):原生查询是"接口函数调用",出 {func, params} JSON
    if family == 'api':
        return _api_query_prompt(handler, object_names, question)
    # SQL 文本族(mysql/pg/tdengine…):出只读 SELECT
    if family in _SQL_FAMILIES:
        schema_ctx = _schema_context(handler, object_names)
        return (
            f'你是 {handler.name} 数据库的查询专家。{schema_ctx}'
            f'请根据下面的自然语言需求,写一条**只读**抽取查询(可按需连表 join;单条语句、不要注释、不要 markdown 代码块)。'
            f'只输出查询本身:\n需求:{question}'
        )
    # 其余非 SQL 源(ES/Mongo/图/KV/向量…):统一"原生查询",让模型用该源自身的查询语法/DSL
    return _native_query_prompt(handler, object_names, question)


def _api_query_prompt(handler: Any, object_names: list[str] | None, question: str) -> str:
    """api 族(akshare/ccxt)取数提示词:其"查询"是调用一个数据接口函数,需输出 {func, params} JSON。"""
    labels = handler.table_labels() if hasattr(handler, 'table_labels') else {}
    names = [n for n in (object_names or []) if n]
    if not names:  # 没选函数:给出白名单里前若干个候选,让模型自行挑选
        try:
            names = [t for t in handler.list_tables()][:SCHEMA_TABLE_CAP]
        except Exception:  # noqa: BLE001
            names = list(labels.keys())[:SCHEMA_TABLE_CAP]
    blocks: list[str] = []
    for t in names:
        desc = labels.get(t, '')
        doc = ''
        if hasattr(handler, 'describe'):
            try:
                doc = (handler.describe(t) or '').strip()
            except Exception:  # noqa: BLE001
                doc = ''
        block = f'- {t}' + (f':{desc}' if desc else '')
        if doc:
            block += '\n' + '\n'.join('    ' + ln for ln in doc.splitlines()[:30])
        blocks.append(block)
    funcs = '\n'.join(blocks) or '(无可用接口信息)'
    return (
        f'你是 {handler.name} 接口数据源的取数专家。该数据源的"原生查询"**不是 SQL**,'
        f'而是调用一个数据接口函数(函数名 + 参数)。\n'
        f'可用接口函数及其参数说明:\n{funcs}\n\n'
        f'请根据下面的需求,选最合适的函数并填好参数。**只输出一行 JSON 对象**'
        f'(不要 SQL、不要注释、不要 markdown 代码块):\n'
        f'{{"func": "函数名", "params": {{"参数名": "值"}}}}\n'
        f'无参数时 params 写 {{}}。参数取值参考上面的函数说明。\n需求:{question}'
    )


def _native_query_prompt(handler: Any, object_names: list[str] | None, question: str) -> str:
    """非 SQL/非 api 源(ES/Mongo/图/KV 等)的统一"原生查询"提示词。

    不为每种源写一套:只声明数据源类型 + 字段 + 该源原生查询的样例结构(handler.sample_query 自描述),
    让模型用该源自身的查询语法/DSL 编写——模型本就知道各系统的查询语言,明确要求即可。
    """
    schema_ctx = _schema_context(handler, object_names)
    names = [n for n in (object_names or []) if n]
    example = ''
    if names and hasattr(handler, 'sample_query'):
        try:
            sq = handler.sample_query(names[0], 50)
            example = f'该数据源原生查询的结构形如(请在此基础上按需求改写):\n{json.dumps(sq, ensure_ascii=False)}\n'
        except Exception:  # noqa: BLE001
            example = ''
    return (
        f'你是 {handler.name} 数据查询专家。{schema_ctx}'
        f'该数据源的"原生查询"**不是 SQL**,请用 {handler.name} 自身的查询语法/DSL 编写。\n'
        f'{example}'
        f'请根据下面的需求写一条**只读**查询,**只输出查询本身**'
        f'(按该源语法,通常是 JSON/DSL;不要 SQL、不要注释、不要 markdown 代码块):\n需求:{question}'
    )


def _schema_context(handler: Any, object_names: list[str] | None) -> str:
    """构造喂给 AI 的表结构上下文(同步,放线程池调用)。"""
    if not handler.has(Capability.SCHEMA):
        return ''
    names = [n for n in (object_names or []) if n]
    if names:  # 选了表:只喂这些表(1 张或多张,支持连表)
        parts = _tables_schema(handler, names)
        if not parts:
            return ''
        label = '相关表结构(可连表查询):' if len(parts) > 1 else '主表字段:'
        return f'{label}\n' + '\n'.join(parts) + '\n\n'
    # 没选表:喂全库结构(滤掉 dlt 内部表),大库截断
    try:
        tables = [t for t in handler.list_tables() if not t.startswith('_dlt')]
    except Exception:  # noqa: BLE001
        return ''
    shown = tables[:SCHEMA_TABLE_CAP]
    parts = _tables_schema(handler, shown)
    if not parts:
        return ''
    note = (f'(全库共 {len(tables)} 张表,仅列出前 {len(shown)} 张;'
            f'如需其它表请在主表里指定)\n') if len(tables) > len(shown) else ''
    return '可用表结构(可连表查询):\n' + note + '\n'.join(parts) + '\n\n'


def _tables_schema(handler: Any, tables: list[str]) -> list[str]:
    """逐表 introspect,返回 ['表 `t`: col type, ...', ...],取不到的表跳过。"""
    parts = []
    for t in tables:
        try:
            cols = handler.get_columns(t)
            parts.append(f'表 `{t}`: ' + ', '.join(f'{c.name} {c.type}' for c in cols))
        except Exception:  # noqa: BLE001
            continue
    return parts


def build_transform_prompt(columns: list[str] | None, question: str) -> str:
    """逐行转换函数生成提示词:NL + 字段 → def transform(row)。"""
    cols = ('可用字段:' + ', '.join(columns) + '\n\n') if columns else ''
    return (
        f'你是 Python 数据处理专家。{cols}'
        f'请根据需求写一个函数 `def transform(row):`,入参 row 是一条记录(dict),返回处理后的 dict。'
        f'只输出函数代码本身(不要注释外的解释、不要 markdown 代码块):\n需求:{question}'
    )


def build_extract_code_prompt(datasource_codes: list[str] | None, question: str) -> str:
    """取数代码(爬虫/任意取数)生成提示词:NL → 产出 result(list[dict])的 Python。"""
    codes = [c for c in (datasource_codes or []) if c]
    srcs = (f'可用数据源(用 get_handler("编码") 取连接,有 .query()/.extract() 等只读取数方法):'
            f'{", ".join(codes)}\n') if codes else ''
    return (
        '你是 Python 数据抓取/取数专家。请根据需求写一段 Python 代码,把抓取/整理到的数据'
        '组织成 list[dict](每个 dict 是一行记录),并赋值给变量 `result`。\n'
        '【大量/分页抓取时用流式】若数据量大或需要翻页,优先反复调用 `emit(rows)`(rows 为 list[dict])'
        '分批产出——平台会边抓边入库,单页失败不影响已抓批次、也不占大内存;用了 emit 就不必再设 result。'
        '数据量小则直接把全部结果赋值给 `result` 即可(emit 与 result 二选一)。\n'
        '可用库:requests(HTTP 请求)、bs4 的 BeautifulSoup(HTML 解析)、lxml、json、re、'
        'pandas、numpy、datetime、time 等;可用 print() 打印进度(即日志)。'
        '不要文件/系统/子进程操作,不要 markdown 代码块,只输出可直接运行的 Python 代码本身。\n'
        f'{srcs}'
        f'需求:{question}'
    )
