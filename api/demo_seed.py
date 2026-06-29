"""财经 demo 种子(幂等,自包含):服务启动后手动跑一次即可,平台默认是空项目。

只影响 demo 命名空间(按固定 id 先删后插),不碰用户/权限/其他数据源任务等系统数据:
- seed_metadata():  建数据源(akshare_cn/demo_es/ccxt_okx) + 16 个 DataIntegrationTask
                    + 16 个 data_model + 1 个 AI 应用。参数化原生 SQL,multiline 代码零转义,可反复执行。
- dispatch_demo_tasks(): 把 16 个任务派发到 Celery(异步),由 worker 取数填充 demo_es 的 fin_* 索引。
- seed_demo():      先 seed_metadata 再 dispatch(整体初始化)。

用法(容器内镜像无此文件,经 stdin 喂入即可,无需重建镜像):
    docker exec -i ezdata-backend-my python - < api/demo_seed.py
agent 对话出图还需配 LLM(环境变量 LLM_TYPE/LLM_MODEL/LLM_API_KEY,或 AI 模型管理建一个)。
"""

import datetime
import json

from sqlalchemy import text

from module_task_schedule.sync_db import get_sync_session_local

TENANT = 100
ES = 'demo_es'
AK = 'akshare_cn'
CCXT = 'ccxt_okx'


def load(idx: str) -> dict:
    return {'datasource_code': ES, 'table': idx, 'mode': 'replace', 'dataset': 'public', 'format': 'csv'}


def native(func: str, params: dict | None, idx: str, transform: str = '') -> str:
    stmt = {'func': func}
    if params:
        stmt['params'] = params
    return json.dumps({
        'extract': {'datasource_code': AK, 'object': func, 'native': stmt},
        'transform': {'enabled': bool(transform), 'code': transform},
        'load': load(idx),
    }, ensure_ascii=False)


def code(ds: str, src: str, idx: str) -> str:
    return json.dumps({
        'extract': {'mode': 'code', 'datasource_codes': [ds], 'code': src},
        'transform': {'enabled': False, 'code': ''},
        'load': load(idx),
    }, ensure_ascii=False)


# 市场活跃度 value 列混合类型(家数=int / 活跃度/日期=str),ES 动态映射会类型冲突 → 统一转字符串
TF_STR_VALUE = "def transform(row):\n    row['value'] = str(row.get('value', ''))\n    return row"

C_STOCK_DAILY = """
symbols = {'sh600519':'贵州茅台','sz300750':'宁德时代','sz002594':'比亚迪',
           'sh688981':'中芯国际','sh601318':'中国平安','sz000651':'格力电器'}
result = []
for c, nm in symbols.items():
    rows = handler.query('stock_zh_a_daily', {'symbol': c, 'adjust': 'qfq'})
    for r in rows[-250:]:
        r['symbol'] = c; r['name'] = nm
        result.append(r)
log('stock_daily rows=%d' % len(result))
"""

C_INDEX_DAILY = """
idx = {'sh000001':'上证指数','sz399001':'深证成指','sh000300':'沪深300','sz399006':'创业板指'}
result = []
for c, nm in idx.items():
    rows = handler.query('stock_zh_index_daily', {'symbol': c})
    for r in rows[-250:]:
        r['symbol'] = c; r['name'] = nm
        result.append(r)
log('index rows=%d' % len(result))
"""

C_CONCEPT_CONS = """
boards = handler.query('stock_board_concept_name_em')
boards = sorted(boards, key=lambda x: x.get('涨跌幅') or 0, reverse=True)[:8]
result = []
for b in boards:
    cname = b['板块名称']
    for s in handler.query('stock_board_concept_cons_em', {'symbol': cname}):
        s['concept'] = cname; s['concept_code'] = b.get('板块代码')
        result.append(s)
log('concept_cons concepts=%d rows=%d' % (len(boards), len(result)))
"""

C_CRYPTO_DAILY = """
result = []
for sym in ['BTC/USDT','ETH/USDT','SOL/USDT','BNB/USDT']:
    for r in handler.query('fetch_ohlcv', {'symbol': sym, 'timeframe': '1d', 'limit': 200}):
        r['symbol'] = sym
        result.append(r)
log('crypto rows=%d' % len(result))
"""

C_MACRO = """
result = []
for func, tag in [('macro_china_cpi','CPI'),('macro_china_ppi','PPI'),
                  ('macro_china_pmi','PMI'),('macro_china_money_supply','货币供应')]:
    for r in handler.query(func, {}):
        r['indicator'] = tag
        result.append(r)
log('macro rows=%d' % len(result))
"""

C_NEWS = """
result = []
for c in ['600519','300750','000651']:
    for r in handler.query('stock_news_em', {'symbol': c}):
        r['query_symbol'] = c
        result.append(r)
log('news rows=%d' % len(result))
"""

# (task_id, 名称, params_json, 索引, 业务名)
TASKS = [
    ('demo_fin_spot', 'A股全市场快照→ES', native('stock_zh_a_spot_em', None, 'fin_stock_spot'), 'fin_stock_spot', 'A股全市场快照'),
    ('demo_fin_zt', '涨停池(当日)→ES', native('stock_zt_pool_em', {'date': '20260629'}, 'fin_zt_pool'), 'fin_zt_pool', '涨停池'),
    ('demo_fin_act', '市场活跃度→ES', native('stock_market_activity_legu', None, 'fin_market_activity', TF_STR_VALUE), 'fin_market_activity', '市场活跃度'),
    ('demo_fin_cptboard', '概念板块快照→ES', native('stock_board_concept_name_em', None, 'fin_concept_board'), 'fin_concept_board', '概念板块快照'),
    ('demo_fin_indsum', '行业板块一览→ES', native('stock_board_industry_summary_ths', None, 'fin_industry_summary'), 'fin_industry_summary', '行业板块一览'),
    ('demo_fin_cptsum', '概念板块解析→ES', native('stock_board_concept_summary_ths', None, 'fin_concept_summary'), 'fin_concept_summary', '概念解析(驱动事件/龙头)'),
    ('demo_fin_cxg', '技术选股创新高→ES', native('stock_rank_cxg_ths', {'symbol': '创月新高'}, 'fin_cxg'), 'fin_cxg', '技术选股·创新高'),
    ('demo_fin_lxsz', '技术选股连涨→ES', native('stock_rank_lxsz_ths', None, 'fin_lxsz'), 'fin_lxsz', '技术选股·连续上涨'),
    ('demo_fin_ipo', '新股申购→ES', native('stock_ipo_ths', {'symbol': '全部A股'}, 'fin_ipo'), 'fin_ipo', '新股申购与中签'),
    ('demo_fin_cb', '可转债数据→ES', native('bond_zh_cov_info_ths', None, 'fin_cb'), 'fin_cb', '可转债数据中心'),
    ('demo_fin_daily', '多股日线→ES', code(AK, C_STOCK_DAILY, 'fin_stock_daily'), 'fin_stock_daily', '多只个股日线'),
    ('demo_fin_index', '主要指数日线→ES', code(AK, C_INDEX_DAILY, 'fin_index_daily'), 'fin_index_daily', '主要指数日线'),
    ('demo_fin_cptcons', '概念成分股→ES', code(AK, C_CONCEPT_CONS, 'fin_concept_cons'), 'fin_concept_cons', '概念→成分股'),
    ('demo_fin_btc', '多币种日线→ES', code(CCXT, C_CRYPTO_DAILY, 'fin_crypto_daily'), 'fin_crypto_daily', '多币种日线'),
    ('demo_fin_macro', '宏观经济→ES', code(AK, C_MACRO, 'fin_macro'), 'fin_macro', '宏观经济(CPI/PPI/PMI/货币)'),
    ('demo_fin_news', '个股新闻→ES', code(AK, C_NEWS, 'fin_news'), 'fin_news', '个股新闻'),
]

# 数据源(自包含:不依赖 ezdata.sql 的 demo 段)。(id, name, code, source_type, family, config_dict)
DATASOURCES = [
    ('seed-akshare-cn', 'AKShare 财经数据', AK, 'akshare', 'api', {}),
    ('seed-demo-es', '演示-Elasticsearch', ES, 'elasticsearch', 'search',
     {'hosts': 'http://ezdata-es:9200', 'user': 'elastic', 'password': 'ezdata123456'}),
    ('seed-ccxt-okx', 'OKX 交易所', CCXT, 'ccxt', 'api', {'exchange': 'okx'}),
]

APP_ID = 9001
APP_PROMPT = """# 角色
你是「财经数据分析助手」,擅长用平台已沉淀的财经数据回答行情、板块、情绪、宏观与加密货币问题,并产出图表。

## 数据
所有数据在数据源 `demo_es`(Elasticsearch)的 fin_* 索引里,例如:
- fin_stock_spot(A股全市场快照)、fin_stock_daily(多只个股日线)、fin_index_daily(主要指数)
- fin_zt_pool(当日涨停池)、fin_market_activity(市场活跃度)、fin_cxg/fin_lxsz(技术选股)
- fin_concept_board(概念板块)、fin_concept_cons(概念→成分股)、fin_concept_summary(概念解析)、fin_industry_summary(行业)
- fin_crypto_daily(多币种日线)、fin_macro(宏观)、fin_ipo(新股)、fin_cb(可转债)、fin_news(个股新闻)
也可用 `akshare_cn`/`ccxt_okx` 实时取最新数据。

## 工作流程
1. 先用 get_table_schema 查相关索引的字段(中文字段如 涨跌幅/所属行业,加密货币为英文 close/symbol)。
2. 用 run_datasource_query 对 demo_es 写 ES DSL 取数或聚合(query/aggs);需要实时数据再查 akshare_cn/ccxt_okx。
3. 在沙箱用 pandas 计算、用 pyecharts 绘图(图表会内联展示给用户)。
4. 给出简明结论 + 图/表。

## 限制
- 数据为演示快照,涨停池/活跃度为当日,不要臆造不存在的历史。
- 取数失败先看字段名(ES 文本字段聚合用 .keyword)。
"""
APP_CONFIG = {
    'prompt': APP_PROMPT,
    'prologue': '你好!我是财经数据分析助手。我可以分析 A股行情/涨停/概念板块/宏观/加密货币等数据并画图,试试下面的预设问题,或直接问我。',
    'presetQuestions': [
        '贵州茅台近一年日线走势,画K线图并简要点评',
        '今天涨停池里涨停家数最多的行业 Top5,用柱状图展示',
        'BTC/ETH/SOL 近30天收盘价走势对比折线图',
        '哪个概念板块的成分股数量最多?列出前8',
        'A股全市场今日涨幅榜前20',
    ],
    'quickCommands': ['查行情', '看涨停', '概念分析', '币圈走势', '宏观数据'],
    'toolIds': [], 'datasetIds': [], 'datasourceCodes': [ES, AK, CCXT],
    'enableMemory': False, 'model': {'modelId': 0, 'temperature': None, 'maxTokens': None},
}

_DS_SQL = text("""INSERT INTO data_source (id,name,code,source_type,family,config,secrets,status,remark,create_by,create_time,tenant_id)
VALUES (:id,:name,:code,:stype,:family,:config,NULL,'ok',:remark,'admin',:now,:tenant)""")
_TASK_SQL = text("""INSERT INTO task (id,template_code,task_type,run_type,name,params,status,built_in,trigger_type,priority,retry,countdown,run_queue,create_by,create_time,remark,tenant_id)
VALUES (:id,'DataIntegrationTask',1,1,:name,:params,1,0,1,1,0,60,'default','admin',:now,:remark,:tenant)""")
_MODEL_SQL = text("""INSERT INTO data_model (id,name,code,datasource_code,kind,object_name,auth,status,remark,create_by,create_time,tenant_id)
VALUES (:id,:name,:code,:ds,'index',:obj,'query,extract,api',1,:remark,'admin',:now,:tenant)""")
_APP_SQL = text("""INSERT INTO ai_app (app_id,name,description,app_type,status,config,user_id,create_by,create_time,tenant_id)
VALUES (:id,:name,:desc,:atype,'0',:config,1,'admin',:now,:tenant)""")


def seed_metadata() -> int:
    """幂等写入数据源/任务/数据模型/AI应用。返回任务数。"""
    now = datetime.datetime.now()
    db = get_sync_session_local()()
    try:
        for sid, name, dcode, stype, family, cfg in DATASOURCES:
            db.execute(text('DELETE FROM data_source WHERE id=:id'), {'id': sid})
            db.execute(_DS_SQL, {'id': sid, 'name': name, 'code': dcode, 'stype': stype, 'family': family,
                                 'config': json.dumps(cfg), 'remark': '演示数据源', 'now': now, 'tenant': TENANT})
        for tid, name, params, idx, label in TASKS:
            db.execute(text('DELETE FROM task WHERE id=:id'), {'id': tid})
            db.execute(_TASK_SQL, {'id': tid, 'name': name, 'params': params, 'remark': label, 'now': now, 'tenant': TENANT})
            dm = 'dm_' + idx
            db.execute(text('DELETE FROM data_model WHERE id=:id'), {'id': dm})
            db.execute(_MODEL_SQL, {'id': dm, 'name': label, 'code': idx, 'ds': ES, 'obj': idx,
                                    'remark': label, 'now': now, 'tenant': TENANT})
        db.execute(text('DELETE FROM ai_app WHERE app_id=:id'), {'id': APP_ID})
        db.execute(_APP_SQL, {'id': APP_ID, 'name': '财经数据分析助手',
                              'desc': '基于 akshare/ccxt 沉淀到 ES 的财经数据,对话取数+绘图分析', 'atype': '数据分析',
                              'config': json.dumps(APP_CONFIG, ensure_ascii=False), 'now': now, 'tenant': TENANT})
        db.commit()
        return len(TASKS)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def dispatch_demo_tasks() -> int:
    """把所有 demo 任务派发到 Celery(异步,由 worker 取数填充 ES)。返回派发数。"""
    from module_task_schedule import dispatch
    n = 0
    for tid, *_ in TASKS:
        dispatch.run_task(tid)
        n += 1
    return n


def seed_demo() -> None:
    """整体初始化:播种元数据 + 派发 ETL 到 Celery 填充 ES。幂等(按固定 demo id 先删后插),可重复执行。"""
    n = seed_metadata()
    print(f'OK: 数据源 {len(DATASOURCES)} + 任务 {n} + 数据模型 {n} + AI应用 1(app_id={APP_ID}) 已写入')
    m = dispatch_demo_tasks()
    print(f'已派发 {m} 个 ETL 任务到 Celery,worker 后台取数填充 ES(约 2-3 分钟)')


if __name__ == '__main__':
    seed_demo()
