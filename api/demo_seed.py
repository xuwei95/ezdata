"""财经 demo 种子(幂等,自包含):服务启动后手动跑一次即可,平台默认是空项目。

只影响 demo 命名空间(按固定 id 先删后插),不碰用户/权限/其他数据源任务等系统数据:
- seed_metadata():  建数据源(akshare_cn/demo_es) + 28 个 DataIntegrationTask
                    + 27 个 data_model(2 个日线任务共用 fin_stock_daily)+ 1 个 AI 应用 + 1 个多图看板(A股市场总览)。参数化原生 SQL,multiline 代码零转义,可反复执行。
                    每个索引一份独立中英字段 map(MAP_*)+ tf() 编译 transform;任务带详细 remark;定时按数据节奏分档。
- dispatch_demo_tasks(): 把 27 个任务派发到 Celery(异步),由 worker 取数填充 demo_es 的 fin_* 索引。
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


# 中英字段映射:不用一个共享大字典,每个索引/接口配自己那几列(键 = 该 akshare 接口实测返回的中文列名)。
# tf(MAP, keys) 编译出 transform.code:① 按 MAP 改英文列名(未命中原样保留);
# ② 用 keys 指定的英文字段拼接 → md5 作 _id 写入(ES 以 _id 落库 → 追加模式下同键幂等 upsert,不重复)。
# keys 为空则不加 _id。mapping 传 {} 表示只加 _id 不改名(新浪日线/指数本就英文)。
def tf(mapping: dict, keys: list | None = None) -> str:
    body = (
        'def transform(row):\n'
        '    import hashlib\n'
        '    M = ' + repr(mapping) + '\n'
        '    out = {M.get(k, k): v for k, v in row.items()}\n'
    )
    if keys:
        body += (
            '    _k = ' + repr(list(keys)) + '\n'
            "    _raw = '|'.join(str(out.get(x, '')) for x in _k)\n"
            "    out['_id'] = hashlib.md5(_raw.encode('utf-8')).hexdigest()\n"
        )
    body += '    return out'
    return body


# 新浪全市场快照:直接分页拉 sina json_v2(每页 80 只),原始列为英文键,仅统一少数命名。
# 含 per/pb/mktcap/nmc/turnoverratio,比 akshare stock_zh_a_spot 一次拉全量更稳(逐页 emit 流式装载)。
MAP_SPOT = {
    'trade': 'price',
    'pricechange': 'change',
    'changepercent': 'change_pct',
    'settlement': 'pre_close',
    'per': 'pe',
    'mktcap': 'market_cap',
    'nmc': 'float_market_cap',
    'turnoverratio': 'turnover_rate',
    'ticktime': 'tick_time',
}
# 新浪港股全市场快照:分页 getHKStockData(node=qbgg_hk),每页原始英文键,仅统一少数命名。
# 保留 symbol/name/engname/open/high/low/volume/amount/buy/sell/high_52week/low_52week/eps/dividend/stocks_sum 等。
MAP_HK = {
    'lasttrade': 'price',
    'prevclose': 'pre_close',
    'changepercent': 'change_pct',
    'pricechange': 'change',
    'market_value': 'market_cap',
    'pe_ratio': 'pe',
    'ticktime': 'tick_time',
}
# 新浪美股全市场快照:JSONP 分页 US_CategoryService.getList(每页20只),原始英文键,仅统一少数命名。
# 保留 symbol/name(英文名)/cname(中文名)/category(行业)/price/open/high/low/amplitude/volume/pe/market 等。
MAP_US = {
    'diff': 'change',
    'chg': 'change_pct',
    'preclose': 'pre_close',
    'mktcap': 'market_cap',
}
# stock_zh_index_spot_sina(实时指数行情,筛主要指数)——新浪,单接口轻量,适合 5 分钟级高频。
MAP_INDEXRT = {
    '代码': 'code',
    '名称': 'name',
    '最新价': 'price',
    '涨跌额': 'change',
    '涨跌幅': 'change_pct',
    '昨收': 'pre_close',
    '今开': 'open',
    '最高': 'high',
    '最低': 'low',
    '成交量': 'volume',
    '成交额': 'amount',
}
# stock_zt_pool_em(涨停池)
MAP_ZT = {
    '序号': 'seq',
    '代码': 'code',
    '名称': 'name',
    '涨跌幅': 'change_pct',
    '最新价': 'price',
    '成交额': 'amount',
    '流通市值': 'float_market_cap',
    '总市值': 'market_cap',
    '换手率': 'turnover_rate',
    '封板资金': 'seal_amount',
    '首次封板时间': 'first_seal_time',
    '最后封板时间': 'last_seal_time',
    '炸板次数': 'break_count',
    '涨停统计': 'zt_stat',
    '连板数': 'boards',
    '所属行业': 'industry',
}
# stock_board_concept_name_em(概念板块快照)
MAP_CPTBOARD = {
    '排名': 'rank',
    '板块名称': 'board_name',
    '板块代码': 'board_code',
    '最新价': 'price',
    '涨跌额': 'change',
    '涨跌幅': 'change_pct',
    '总市值': 'market_cap',
    '换手率': 'turnover_rate',
    '上涨家数': 'up_count',
    '下跌家数': 'down_count',
    '领涨股票': 'lead_stock',
    '领涨股票-涨跌幅': 'lead_stock_change_pct',
}
# stock_board_industry_summary_ths(行业板块一览)
MAP_INDSUM = {
    '序号': 'seq',
    '板块': 'board_name',
    '涨跌幅': 'change_pct',
    '总成交量': 'total_volume',
    '总成交额': 'total_amount',
    '净流入': 'net_inflow',
    '上涨家数': 'up_count',
    '下跌家数': 'down_count',
    '均价': 'avg_price',
    '领涨股': 'lead_stock',
    '领涨股-最新价': 'lead_stock_price',
    '领涨股-涨跌幅': 'lead_stock_change_pct',
}
# stock_board_concept_summary_ths(概念解析)
MAP_CPTSUM = {
    '日期': 'date',
    '概念名称': 'concept_name',
    '驱动事件': 'driver_event',
    '龙头股': 'leader_stock',
    '成分股数量': 'cons_count',
}
# stock_rank_cxg_ths(技术选股·创新高)
MAP_CXG = {
    '序号': 'seq',
    '股票代码': 'code',
    '股票简称': 'name',
    '涨跌幅': 'change_pct',
    '换手率': 'turnover_rate',
    '最新价': 'price',
    '前期高点': 'prev_high',
    '前期高点日期': 'prev_high_date',
}
# stock_rank_lxsz_ths(技术选股·连续上涨)
MAP_LXSZ = {
    '序号': 'seq',
    '股票代码': 'code',
    '股票简称': 'name',
    '收盘价': 'close',
    '最高价': 'high',
    '最低价': 'low',
    '连涨天数': 'up_days',
    '连续涨跌幅': 'consec_change_pct',
    '累计换手率': 'cum_turnover_rate',
    '所属行业': 'industry',
}
# stock_ipo_ths(新股申购)
MAP_IPO = {
    '股票代码': 'code',
    '股票简称': 'name',
    '申购代码': 'subscribe_code',
    '发行总数（万股）': 'issue_total_wan',
    '网上发行（万股）': 'online_issue_wan',
    '申购上限（万股）': 'subscribe_limit_wan',
    '顶格申购需配市值（万元）': 'max_subscribe_mktcap_wan',
    '发行价格': 'issue_price',
    '发行市盈率': 'issue_pe',
    '行业市盈率': 'industry_pe',
    '申购日期': 'subscribe_date',
    '中签率（%）': 'winning_rate_pct',
    '中签号': 'lucky_number',
    '中签缴款日期': 'payment_date',
    '上市日期': 'list_date',
    '打新收益（元）': 'ipo_profit_yuan',
    '首日最高涨幅': 'first_day_max_gain',
    '连板天数': 'boards_days',
}
# bond_zh_cov_info_ths(可转债)
MAP_CB = {
    '债券代码': 'bond_code',
    '债券简称': 'bond_name',
    '申购日期': 'subscribe_date',
    '申购代码': 'subscribe_code',
    '原股东配售码': 'shareholder_code',
    '每股获配额': 'per_share_alloc',
    '计划发行量': 'planned_issue',
    '实际发行量': 'actual_issue',
    '中签公布日': 'winning_announce_date',
    '中签号': 'lucky_number',
    '上市日期': 'list_date',
    '正股代码': 'stock_code',
    '正股简称': 'stock_name',
    '转股价格': 'convert_price',
    '到期时间': 'maturity_date',
    '中签率': 'winning_rate',
}
# index_stock_cons_sina(主要指数成分股,替代东财 concept_cons_em——新浪更稳;列本就多为英文,仅统一少数命名)
# code 内补 index_code/index_name(已英文)。沪深300含 per/pb/mktcap/turnoverratio,上证50等子集可能缺,稀疏正常。
MAP_IDXCONS = {
    'trade': 'price',
    'pricechange': 'change',
    'changepercent': 'change_pct',
    'settlement': 'pre_close',
    'per': 'pe',
    'mktcap': 'market_cap',
    'nmc': 'float_market_cap',
    'turnoverratio': 'turnover_rate',
    'ticktime': 'tick_time',
}
# 宏观:cpi/ppi/pmi/money_supply 四接口列名的并集(本就是多接口汇到一个索引)+ code 内补的 indicator
MAP_MACRO = {
    '月份': 'month',
    '当月': 'month_val',
    '当月同比增长': 'month_yoy',
    '累计': 'cum',
    '全国-当月': 'national_month',
    '全国-同比增长': 'national_yoy',
    '全国-环比增长': 'national_mom',
    '全国-累计': 'national_cum',
    '城市-当月': 'urban_month',
    '城市-同比增长': 'urban_yoy',
    '城市-环比增长': 'urban_mom',
    '城市-累计': 'urban_cum',
    '农村-当月': 'rural_month',
    '农村-同比增长': 'rural_yoy',
    '农村-环比增长': 'rural_mom',
    '农村-累计': 'rural_cum',
    '制造业-指数': 'mfg_index',
    '制造业-同比增长': 'mfg_yoy',
    '非制造业-指数': 'nonmfg_index',
    '非制造业-同比增长': 'nonmfg_yoy',
    '流通中的现金(M0)-数量(亿元)': 'm0_amount_yi',
    '流通中的现金(M0)-同比增长': 'm0_yoy',
    '流通中的现金(M0)-环比增长': 'm0_mom',
    '货币(M1)-数量(亿元)': 'm1_amount_yi',
    '货币(M1)-同比增长': 'm1_yoy',
    '货币(M1)-环比增长': 'm1_mom',
    '货币和准货币(M2)-数量(亿元)': 'm2_amount_yi',
    '货币和准货币(M2)-同比增长': 'm2_yoy',
    '货币和准货币(M2)-环比增长': 'm2_mom',
}
# stock_news_em(个股新闻):code 内补的 query_symbol(已英文)
MAP_NEWS = {
    '关键词': 'keyword',
    '新闻标题': 'title',
    '新闻内容': 'content',
    '发布时间': 'publish_time',
    '文章来源': 'source',
    '新闻链接': 'url',
}
# stock_market_fund_flow(大盘资金流·时序)
MAP_MKTFLOW = {
    '日期': 'date',
    '上证-收盘价': 'sh_close',
    '上证-涨跌幅': 'sh_change_pct',
    '深证-收盘价': 'sz_close',
    '深证-涨跌幅': 'sz_change_pct',
    '主力净流入-净额': 'main_net',
    '主力净流入-净占比': 'main_net_pct',
    '超大单净流入-净额': 'xlarge_net',
    '超大单净流入-净占比': 'xlarge_net_pct',
    '大单净流入-净额': 'large_net',
    '大单净流入-净占比': 'large_net_pct',
    '中单净流入-净额': 'mid_net',
    '中单净流入-净占比': 'mid_net_pct',
    '小单净流入-净额': 'small_net',
    '小单净流入-净占比': 'small_net_pct',
}
# stock_lhb_detail_em(龙虎榜明细)
MAP_LHB = {
    '序号': 'seq',
    '代码': 'code',
    '名称': 'name',
    '上榜日': 'list_date',
    '解读': 'interpret',
    '收盘价': 'close',
    '涨跌幅': 'change_pct',
    '龙虎榜净买额': 'lhb_net_buy',
    '龙虎榜买入额': 'lhb_buy',
    '龙虎榜卖出额': 'lhb_sell',
    '龙虎榜成交额': 'lhb_amount',
    '市场总成交额': 'market_amount',
    '净买额占总成交比': 'net_buy_pct',
    '成交额占总成交比': 'amount_pct',
    '换手率': 'turnover_rate',
    '流通市值': 'float_market_cap',
    '上榜原因': 'reason',
    '上榜后1日': 'after_1d',
    '上榜后2日': 'after_2d',
    '上榜后5日': 'after_5d',
    '上榜后10日': 'after_10d',
}
# stock_yjbb_em(业绩报表):code 内补的 report_period(已英文)
MAP_YJBB = {
    '序号': 'seq',
    '股票代码': 'code',
    '股票简称': 'name',
    '每股收益': 'eps',
    '营业总收入-营业总收入': 'revenue',
    '营业总收入-同比增长': 'revenue_yoy',
    '营业总收入-季度环比增长': 'revenue_qoq',
    '净利润-净利润': 'net_profit',
    '净利润-同比增长': 'net_profit_yoy',
    '净利润-季度环比增长': 'net_profit_qoq',
    '每股净资产': 'bps',
    '净资产收益率': 'roe',
    '每股经营现金流量': 'ocfps',
    '销售毛利率': 'gross_margin',
    '所处行业': 'industry',
    '最新公告日期': 'announce_date',
}
# stock_industry_pe_ratio_cninfo(行业市盈率·证监会分类)
MAP_INDPE = {
    '变动日期': 'date',
    '行业分类': 'industry_class',
    '行业层级': 'industry_level',
    '行业编码': 'industry_code',
    '行业名称': 'industry_name',
    '公司数量': 'company_count',
    '纳入计算公司数量': 'calc_company_count',
    '总市值-静态': 'market_cap_static',
    '净利润-静态': 'net_profit_static',
    '静态市盈率-加权平均': 'pe_weighted',
    '静态市盈率-中位数': 'pe_median',
    '静态市盈率-算术平均': 'pe_mean',
}
# stock_margin_sse(上交所融资融券·时序)
MAP_MARGIN = {
    '信用交易日期': 'date',
    '融资余额': 'margin_balance',
    '融资买入额': 'margin_buy',
    '融券余量': 'short_volume',
    '融券余量金额': 'short_amount',
    '融券卖出量': 'short_sell',
    '融资融券余额': 'total_balance',
}
# fund_etf_spot_em(ETF 实时快照)
MAP_ETF = {
    '代码': 'code',
    '名称': 'name',
    '最新价': 'price',
    'IOPV实时估值': 'iopv',
    '基金折价率': 'discount_rate',
    '涨跌额': 'change',
    '涨跌幅': 'change_pct',
    '成交量': 'volume',
    '成交额': 'amount',
    '开盘价': 'open',
    '最高价': 'high',
    '最低价': 'low',
    '昨收': 'pre_close',
    '振幅': 'amplitude',
    '换手率': 'turnover_rate',
    '量比': 'volume_ratio',
    '委比': 'commission_ratio',
    '外盘': 'outer_volume',
    '内盘': 'inner_volume',
    '主力净流入-净额': 'main_net',
    '主力净流入-净占比': 'main_net_pct',
    '超大单净流入-净额': 'xlarge_net',
    '超大单净流入-净占比': 'xlarge_net_pct',
    '大单净流入-净额': 'large_net',
    '大单净流入-净占比': 'large_net_pct',
    '中单净流入-净额': 'mid_net',
    '中单净流入-净占比': 'mid_net_pct',
    '小单净流入-净额': 'small_net',
    '小单净流入-净占比': 'small_net_pct',
    '现手': 'current_hand',
    '买一': 'bid1',
    '卖一': 'ask1',
    '最新份额': 'latest_shares',
    '流通市值': 'float_market_cap',
    '总市值': 'market_cap',
    '数据日期': 'data_date',
    '更新时间': 'update_time',
}
# macro_china_gdp(中国 GDP·季度)
MAP_GDP = {
    '季度': 'quarter',
    '国内生产总值-绝对值': 'gdp_abs',
    '国内生产总值-同比增长': 'gdp_yoy',
    '第一产业-绝对值': 'primary_abs',
    '第一产业-同比增长': 'primary_yoy',
    '第二产业-绝对值': 'secondary_abs',
    '第二产业-同比增长': 'secondary_yoy',
    '第三产业-绝对值': 'tertiary_abs',
    '第三产业-同比增长': 'tertiary_yoy',
}
# macro_china_lpr(LPR 利率·时序;原列名为英文大写,统一成小写下划线)
MAP_LPR = {
    'TRADE_DATE': 'trade_date',
    'LPR1Y': 'lpr_1y',
    'LPR5Y': 'lpr_5y',
    'RATE_1': 'rate_1',
    'RATE_2': 'rate_2',
}


def load(idx: str) -> dict:
    # 追加模式:配合 transform 里算的 md5 _id 幂等 upsert(同键覆盖、新键新增),重跑不重复、时序可累积。
    return {'datasource_code': ES, 'table': idx, 'mode': 'append', 'dataset': 'public', 'format': 'csv'}


def native(func: str, params: dict | None, idx: str, transform: str = '') -> str:
    stmt = {'func': func}
    if params:
        stmt['params'] = params
    return json.dumps(
        {
            'extract': {'datasource_code': AK, 'object': func, 'native': stmt},
            'transform': {'enabled': bool(transform), 'code': transform},
            'load': load(idx),
        },
        ensure_ascii=False,
    )


def code(ds: str, src: str, idx: str, transform: str = '') -> str:
    return json.dumps(
        {
            'extract': {'mode': 'code', 'datasource_codes': [ds], 'code': src},
            'transform': {'enabled': bool(transform), 'code': transform},
            'load': load(idx),
        },
        ensure_ascii=False,
    )


def code_multi(dslist: list, src: str, idx: str, transform: str = '') -> str:
    # 多数据源代码取数:src 里用 get_handler('<code>') 分别拿各源 handler(如 demo_es 取代码 + akshare 取日线)。
    return json.dumps(
        {
            'extract': {'mode': 'code', 'datasource_codes': list(dslist), 'code': src},
            'transform': {'enabled': bool(transform), 'code': transform},
            'load': load(idx),
        },
        ensure_ascii=False,
    )


# 市场活跃度 value 列混合类型(家数=int / 活跃度/日期=str),ES 动态映射会类型冲突 → 统一转字符串
TF_STR_VALUE = (
    'def transform(row):\n'
    '    import hashlib\n'
    "    row['value'] = str(row.get('value', ''))\n"
    "    row['_id'] = hashlib.md5(str(row.get('item', '')).encode('utf-8')).hexdigest()\n"
    '    return row'
)

# A股日线增量:只翻新浪全市场快照「第一页」(约80只),从当日快照派生日线 OHLCV,收盘后定时增量(不逐只全抓)。
C_SPOT_DAILY_P1 = """
import requests, json, datetime
from akshare.stock.stock_zh_a_sina import zh_sina_a_stock_url, zh_sina_a_stock_payload
d = datetime.date.today().isoformat()
p = dict(zh_sina_a_stock_payload); p["page"] = 1
rows = json.loads(requests.get(zh_sina_a_stock_url, params=p, timeout=15).text)
result = []
for r in rows or []:
    sym = r.get("symbol", "")
    if not sym.startswith(("sh", "sz", "bj")):  # 快照含全A股(沪/深/北),全保留
        continue
    result.append({"symbol": sym, "name": r.get("name"), "date": d,
                   "open": r.get("open"), "high": r.get("high"), "low": r.get("low"),
                   "close": r.get("trade"), "volume": r.get("volume"), "amount": r.get("amount")})
print("快照第一页派生日线 %d 行 @ %s" % (len(result), d))
"""

# 全A股历史前复权日线:复用「A股全市场快照」产物 fin_stock_spot(demo_es)作全市场代码源,不重复抓全市场;
# 逐只 akshare stock_zh_a_daily(前复权)补历史,emit 流式装载。多数据源(demo_es 取代码 + akshare 取日线)。
C_ALL_STOCK_DAILY = """
es = get_handler('demo_es')
ak = get_handler('akshare_cn')
codes = es.query({'index': 'fin_stock_spot', 'body': {'query': {'match_all': {}}, 'size': 6000, '_source': ['code', 'name']}})
codes = [c for c in codes if str(c.get('code') or '').startswith(('sh', 'sz'))]
print('复用 fin_stock_spot 全市场代码 %d 只(沪深),逐只抓前复权日线…' % len(codes))
done = 0
total = 0
for c in codes:
    sym = c.get('code')
    nm = c.get('name') or ''
    try:
        rows = ak.query('stock_zh_a_daily', {'symbol': sym, 'adjust': 'qfq'})
        for x in rows:
            x['symbol'] = sym
            x['name'] = nm
        if rows:
            emit(rows)
            total += len(rows)
        done += 1
        if done % 200 == 0:
            print('进度 %d/%d,累计 %d 行' % (done, len(codes), total))
    except Exception as e:
        print('跳过 %s: %s' % (sym, e))
print('完成:%d 只 / %d 行 → fin_stock_daily' % (done, total))
result = []
"""

C_INDEX_DAILY = """
idx = {'sh000001':'上证指数','sz399001':'深证成指','sh000300':'沪深300','sz399006':'创业板指'}
result = []
for c, nm in idx.items():
    rows = handler.query('stock_zh_index_daily', {'symbol': c})
    for r in rows[-250:]:
        r['symbol'] = c; r['name'] = nm
        result.append(r)
print('index rows=%d' % len(result))
"""

# 常见指数实时行情:新浪 stock_zh_index_spot_sina 拿全部指数,筛主要几只(单接口轻量,适合 5 分钟级)。
C_INDEX_RT = """
common = {'sh000001','sz399001','sh000300','sz399006','sh000688','sh000016','sh000905','sh000852'}
rows = handler.query('stock_zh_index_spot_sina', {})
result = [r for r in rows if r.get('代码') in common]
print('常见指数实时 %d 条' % len(result))
"""

# 检测新增概念:同花顺概念列表(单接口轻量,返回全部~373;THS 板块 code 越大越新)。
# 只取 code 最大的前 60 个(=最新的概念板块)入库;配 md5(code) 追加 → 新概念(新 code)自动增量落库,已有幂等更新。
# 频率可较快(THS 单次调用,盘中每10分)。
C_CONCEPT_NEW = """
rows = handler.query('stock_board_concept_name_ths', {})
rows = sorted(rows, key=lambda r: str(r.get('code') or ''), reverse=True)[:60]
result = rows
print('概念检测(最新60)%d 条' % len(result))
"""

C_INDEX_CONS = """
idx = {'000300':'沪深300','000016':'上证50','000905':'中证500'}
result = []
for code, nm in idx.items():
    for s in handler.query('index_stock_cons_sina', {'symbol': code}):
        s['index_code'] = code; s['index_name'] = nm
        result.append(s)
print('index_cons rows=%d' % len(result))
"""

C_MACRO = """
result = []
for func, tag in [('macro_china_cpi','CPI'),('macro_china_ppi','PPI'),
                  ('macro_china_pmi','PMI'),('macro_china_money_supply','货币供应')]:
    for r in handler.query(func, {}):
        r['indicator'] = tag
        result.append(r)
print('macro rows=%d' % len(result))
"""

C_NEWS = """
result = []
for c in ['600519','300750','000651']:
    for r in handler.query('stock_news_em', {'symbol': c}):
        r['query_symbol'] = c
        result.append(r)
print('news rows=%d' % len(result))
"""

# —— 以下 4 个走代码模式:akshare 接口需动态日期参数,自动算最近交易日/报告期/时间窗 ——
C_LHB = """
import datetime
now = datetime.datetime.now()
start = (now - datetime.timedelta(days=30)).strftime('%Y%m%d')
end = now.strftime('%Y%m%d')
result = handler.query('stock_lhb_detail_em', {'start_date': start, 'end_date': end})
print('lhb %s~%s rows=%d' % (start, end, len(result)))
"""

C_YJBB = """
import datetime
now = datetime.datetime.now(); today = now.strftime('%Y%m%d')
cands = []
for yy in (now.year, now.year - 1):
    for md in ('1231','0930','0630','0331'):
        c = '%d%s' % (yy, md)
        if c <= today:
            cands.append(c)
cands = sorted(set(cands), reverse=True)
result = []; picked = None
for c in cands:
    try:                                  # 某报告期未披露/接口偶发会抛错,跳过试下一个
        rows = handler.query('stock_yjbb_em', {'date': c})
    except Exception as e:
        print('yjbb skip %s: %s' % (c, e)); continue
    if rows:
        for r in rows:
            r['report_period'] = c
        result = rows; picked = c; break
print('yjbb period=%s rows=%d' % (picked, len(result)))
"""

C_INDPE = """
import datetime
now = datetime.datetime.now()
result = []; picked = None
for back in range(0, 12):
    d = (now - datetime.timedelta(days=back)).strftime('%Y%m%d')
    try:                                  # 非交易日/当日未出数据时 akshare 会抛错(空表赋列名),跳过回溯前一天
        rows = handler.query('stock_industry_pe_ratio_cninfo', {'symbol': '证监会行业分类', 'date': d})
    except Exception as e:
        print('industry_pe skip %s: %s' % (d, e)); continue
    if rows:
        result = rows; picked = d; break
print('industry_pe date=%s rows=%d' % (picked, len(result)))
"""

C_MARGIN = """
import datetime
now = datetime.datetime.now()
start = (now - datetime.timedelta(days=180)).strftime('%Y%m%d')
end = now.strftime('%Y%m%d')
result = handler.query('stock_margin_sse', {'start_date': start, 'end_date': end})
print('margin %s~%s rows=%d' % (start, end, len(result)))
"""

# 涨停池:code 取数,显式取"当日"日期(stock_zt_pool_em 只有最近交易日有数据;非交易日/盘前为空,由 ES 空写建空索引兜底)
C_ZT = """
import pandas as pd
import json
import datetime

handler = get_handler("akshare_cn")
today_str = datetime.datetime.now().strftime("%Y%m%d")
params = {"date": today_str}
print(f"开始抓取涨停板股票池数据，日期：{params['date']} ...")
raw = handler.query("stock_zt_pool_em", params)

if isinstance(raw, pd.DataFrame):
    result = raw.to_dict(orient='records')
elif isinstance(raw, list):
    if raw and isinstance(raw[0], dict):
        result = raw
    else:
        result = [{"item": x} for x in raw]
else:
    result = json.loads(json.dumps(raw))

print(f"抓取完成，共获取 {len(result)} 条记录。")
"""

# A股全市场快照:把新浪 stock_zh_a_spot 的"一次拉全部~70页"拆成逐页抓取 + 逐页 emit 流式装载,
# 单页失败只跳过该页(不拖垮整体),已抓页即时入库;轻微 sleep 躲新浪限流。每页原始 JSON 为英文键。
C_SPOT = """
import requests, json, time
from akshare.stock.stock_zh_a_sina import zh_sina_a_stock_url, zh_sina_a_stock_payload, _get_zh_a_page_count

try:
    pages = _get_zh_a_page_count()
except Exception:
    pages = 70
print(f"A股全市场快照:约 {pages} 页,逐页流式抓取…")
total = 0
for pg in range(1, pages + 1):
    p = dict(zh_sina_a_stock_payload); p["page"] = pg
    ok = False
    for _try in range(3):
        try:
            r = requests.get(zh_sina_a_stock_url, params=p, timeout=15)
            rows = json.loads(r.text)
            ok = True
            break
        except Exception as e:
            time.sleep(1.0)
    if not ok:
        print(f"第 {pg} 页 3 次失败,跳过")
        continue
    if rows:
        emit(rows)
        total += len(rows)
    time.sleep(0.2)
print(f"全市场快照完成,共 {total} 条(逐页流式)")
"""

# 港股全市场快照:新浪 getHKStockData(node=qbgg_hk),逐页抓取(每页80只)+ 逐页 emit 流式装载,
# 空页即到底停止;单页 3 次失败跳过。东财港股走 push2 易限流,故用新浪分页。
C_HK_SPOT = """
import requests, json, time
URL = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHKStockData"
base = {"num": "80", "sort": "symbol", "asc": "1", "node": "qbgg_hk", "_s_r_a": "init"}
total = 0
for pg in range(1, 100):
    p = dict(base); p["page"] = str(pg)
    rows = None
    for _try in range(3):
        try:
            r = requests.get(URL, params=p, timeout=15)
            rows = json.loads(r.text)
            break
        except Exception:
            time.sleep(1.0)
    if not rows:            # 空页/连续失败 → 到底,停
        break
    emit(rows)
    total += len(rows)
    time.sleep(0.2)
print(f"港股全市场快照完成,共 {total} 条(逐页流式)")
"""

# 美股全市场快照:新浪 JSONP US_CategoryService.getList(每页20只,~884页/1.7万只),逐页 emit 流式装载。
# 响应是 JSONP(IO.XSRV2.CallbackList[..](...)),剥壳取内层 JSON;首页拿 count 算页数(上限兜底防跑飞);
# 单页 3 次失败跳过、空页停止。量大,设为美股收盘后每天单次(北京 06:00),约 30 分钟。
C_US_SPOT = """
import requests, json, time
URL = "http://stock.finance.sina.com.cn/usstock/api/jsonp.php/IO.XSRV2.CallbackList[ez]/US_CategoryService.getList"
base = {"num": "20", "sort": "", "asc": "0", "market": "", "id": ""}

def _fetch(pg):
    p = dict(base); p["page"] = str(pg)
    t = requests.get(URL, params=p, timeout=15).text
    inner = t[t.index('(', t.index('CallbackList')) + 1 : t.rindex(')')]
    return json.loads(inner)

total = 0
pages = 0
try:
    first = _fetch(1)
    cnt = int(first.get('count') or 0)
    pages = min((cnt // 20) + 2, 950)   # 上限兜底
    d0 = first.get('data') or []
    if d0:
        emit(d0); total += len(d0)
    print(f"美股全市场:共 {cnt} 只 / 约 {pages} 页,逐页流式抓取…")
except Exception as e:
    print(f"首页失败:{e}")
for pg in range(2, pages + 1):
    rows = None
    for _try in range(3):
        try:
            rows = _fetch(pg).get('data') or []
            break
        except Exception:
            time.sleep(1.0)
    if rows is None:
        print(f"第 {pg} 页 3 次失败,跳过")
        continue
    if not rows:
        break
    emit(rows); total += len(rows)
    time.sleep(0.15)
print(f"美股全市场快照完成,共 {total} 条(逐页流式)")
"""

# 定时策略:按各数据的真实更新节奏分档。cron 为 6 段 Quartz:秒 分 时 日 月 周;日/周用 ? 占位。
# 注意:该 cron 适配器对"星期范围"有坑(会被当成 week-of-year),故只用"每天/每月某日"形态,不用星期。
CRON_CLOSE = '0 0 16 * * ? *'  # 收盘日更 16:00(日线/指数/大盘资金流等 EOD 序列)
CRON_INTRADAY = (
    '0 0/30 9-15 ? * 2-6 *'  # 盘中每30分:周一至周五 9:00-15:59(实时快照:全市场/涨停/活跃度/概念·行业板块/ETF)
)
CRON_EVENING = '0 30 18 * * ? *'  # 盘后晚间 18:30(龙虎榜、两融——交易所/东财收盘后才发布)
CRON_DAWN = '0 30 0 * * ? *'  # 凌晨日更 00:30(概念成分/解析/技术选股/业绩/行业估值/新股/可转债)
CRON_HOUR = '0 0 * * * ? *'  # 每小时(新闻,时效性强)
CRON_MONTH = '0 0 2 1 * ? *'  # 每月1号 02:00(宏观月度/季度:CPI·PPI·PMI·货币/GDP/LPR)
CRON_USCLOSE = '0 0 6 * * ? *'  # 每天北京 06:00(美股收盘后;全量美股~1.7万只逐页流式,约30分钟)
CRON_INDEX5M = '0 0/5 9-15 ? * 2-6 *'  # 盘中每5分:周一至周五 9:00-15:59(常见指数实时、市场活跃度——轻量单接口,低限流)
CRON_CPT1H = '0 0 9-15 ? * 2-6 *'  # 盘中每小时整点:概念板块"检测新增"(THS 接口偏慢~1-4分,概念也不频繁新增,1小时足够)

# (task_id, 任务名, params_json, 索引, 数据模型名, cron, 详细描述)  cron='' 即单次手动(trigger_type=1)
# 任务名简明带"→索引";详细描述写清:数据源/字段/更新节奏/适合的分析。data_model 名用"数据模型名"。
TASKS = [
    (
        'demo_fin_spot',
        'A股全市场实时快照 → fin_stock_spot',
        code(AK, C_SPOT, 'fin_stock_spot', tf(MAP_SPOT, ['code'])),
        'fin_stock_spot',
        'A股全市场快照',
        CRON_INTRADAY,
        '新浪全A股截面行情(code 取数·逐页流式:把新浪全市场分页拆成每页 80 只、逐页 emit 装载,单页失败只跳过、不拖垮整体、躲限流):代码/名称/最新价/涨跌额涨跌幅/买卖盘/昨收今开/最高最低/成交量额/市盈率/市净率/总市值流通市值/换手率。收盘后(16:00)刷新,适合涨跌幅榜、量价与市值分析。',
    ),
    (
        'demo_fin_hkspot',
        '港股全市场快照 → fin_hk_spot',
        code(AK, C_HK_SPOT, 'fin_hk_spot', tf(MAP_HK, ['symbol'])),
        'fin_hk_spot',
        '港股全快照',
        CRON_INTRADAY,
        '新浪港股全市场实时快照(code 取数·逐页流式:node=qbgg_hk 每页80只,逐页 emit、单页失败跳过、md5(symbol)幂等):代码/名称/英文名/最新价/昨收/开高低/成交量额/买卖盘/52周高低/EPS/股息/总股本/市值/市盈率。周一至周五盘中每30分刷新,适合港股涨跌榜、量价与市值分析。',
    ),
    (
        'demo_fin_usspot',
        '美股全市场快照 → fin_us_spot',
        code(AK, C_US_SPOT, 'fin_us_spot', tf(MAP_US, ['symbol'])),
        'fin_us_spot',
        '美股全快照',
        CRON_USCLOSE,
        '新浪美股全市场快照(code 取数·逐页流式:US_CategoryService 每页20只、约884页/1.7万只,逐页 emit、单页失败跳过、md5(symbol)幂等):代码/英文名/中文名/行业/最新价/涨跌额涨跌幅/昨收开高低/振幅/成交量/市值/市盈率/交易所。美股收盘后每天北京 06:00 刷新一次,量大约30分钟。',
    ),
    (
        'demo_fin_indexrt',
        '常见指数实时行情 → fin_index_rt',
        code(AK, C_INDEX_RT, 'fin_index_rt', tf(MAP_INDEXRT, ['code'])),
        'fin_index_rt',
        '常见指数实时',
        CRON_INDEX5M,
        '新浪实时行情筛主要指数(上证/深证成指/沪深300/创业板指/科创50/上证50/中证500/中证1000):最新价/涨跌额涨跌幅/昨收今开/最高最低/成交量额。盘中每5分钟刷新(轻量单接口、低限流风险),md5(code)幂等,适合大盘实时监控。',
    ),
    (
        'demo_fin_cptnew',
        '概念板块·检测新增 → fin_concept_new',
        code(AK, C_CONCEPT_NEW, 'fin_concept_new', tf({}, ['code'])),
        'fin_concept_new',
        '概念检测新增',
        CRON_CPT1H,
        '同花顺概念板块列表,按 code 降序取最新 60 个(THS code 越大越新)入库;追加+md5(code) 幂等 → 新概念(新 code)自动增量落库、已有幂等更新。THS 接口偏慢(~1-4分),概念也不频繁新增,盘中每小时刷新一次即可,适合监测市场新题材/新概念上线。',
    ),
    (
        'demo_fin_zt',
        '涨停板池(当日)→ fin_zt_pool',
        code(AK, C_ZT, 'fin_zt_pool', tf(MAP_ZT, ['code'])),
        'fin_zt_pool',
        '当日涨停池',
        CRON_INTRADAY,
        '东财当日涨停个股(code 取数,显式取当日日期):封板资金/首次与最后封板时间/炸板次数/涨停统计/连板数/所属行业。收盘后(16:00)日更,适合按行业统计涨停家数、连板梯队、封板强度分析。',
    ),
    (
        'demo_fin_act',
        '市场活跃度情绪 → fin_market_activity',
        native('stock_market_activity_legu', None, 'fin_market_activity', TF_STR_VALUE),
        'fin_market_activity',
        '市场活跃度',
        CRON_INDEX5M,
        '乐咕乐股市场情绪快照:上涨/下跌/平盘/涨停/跌停/真跌停/活跃度等家数统计,以 item(指标名)+value(值,统一转字符串避免ES类型冲突)键值对存储。收盘后日更,适合做多空力量、市场温度概览。',
    ),
    (
        'demo_fin_cptboard',
        '概念板块行情快照 → fin_concept_board',
        native('stock_board_concept_name_em', None, 'fin_concept_board', tf(MAP_CPTBOARD, ['board_code'])),
        'fin_concept_board',
        '概念板块行情',
        CRON_INTRADAY,
        '东财全部概念板块:排名/板块名称/板块代码/最新价/涨跌额/涨跌幅/总市值/换手率/上涨下跌家数/领涨股票及其涨跌幅。收盘后日更,适合概念热度排行、强势板块筛选。',
    ),
    (
        'demo_fin_indsum',
        '行业板块一览 → fin_industry_summary',
        native('stock_board_industry_summary_ths', None, 'fin_industry_summary', tf(MAP_INDSUM, ['board_name'])),
        'fin_industry_summary',
        '行业板块一览',
        CRON_INTRADAY,
        '同花顺行业板块汇总:涨跌幅/总成交量/总成交额/净流入/上涨下跌家数/均价/领涨股及其最新价与涨跌幅。收盘后日更,适合行业轮动、资金净流入排行。',
    ),
    (
        'demo_fin_cptsum',
        '概念板块解析(驱动/龙头)→ fin_concept_summary',
        native('stock_board_concept_summary_ths', None, 'fin_concept_summary', tf(MAP_CPTSUM, ['concept_name'])),
        'fin_concept_summary',
        '概念解析',
        CRON_DAWN,
        '同花顺概念解析:日期/概念名称/驱动事件/龙头股/成分股数量。概念定义变动不频繁,凌晨(00:30)日更,适合解读概念逻辑、定位龙头与成分股规模。',
    ),
    (
        'demo_fin_cxg',
        '技术选股·创月新高 → fin_cxg',
        native('stock_rank_cxg_ths', {'symbol': '创月新高'}, 'fin_cxg', tf(MAP_CXG, ['code'])),
        'fin_cxg',
        '技术选股·创新高',
        CRON_DAWN,
        '同花顺技术形态选股(创月新高):股票代码/简称/涨跌幅/换手率/最新价/前期高点及其日期。凌晨日更,适合强势突破股票池。',
    ),
    (
        'demo_fin_lxsz',
        '技术选股·连续上涨 → fin_lxsz',
        native('stock_rank_lxsz_ths', None, 'fin_lxsz', tf(MAP_LXSZ, ['code'])),
        'fin_lxsz',
        '技术选股·连续上涨',
        CRON_DAWN,
        '同花顺连续上涨个股:股票代码/简称/收盘价/最高价/最低价/连涨天数/连续涨跌幅/累计换手率/所属行业。凌晨日更,适合动量与连涨梯队分析。',
    ),
    (
        'demo_fin_ipo',
        '新股申购与中签 → fin_ipo',
        native('stock_ipo_ths', {'symbol': '全部A股'}, 'fin_ipo', tf(MAP_IPO, ['code'])),
        'fin_ipo',
        '新股申购',
        CRON_DAWN,
        '同花顺新股申购:申购代码/发行总数与网上发行量/申购上限/顶格申购需配市值/发行价格/发行与行业市盈率/申购日/中签率/中签号/缴款日/上市日/打新收益/首日最高涨幅/连板天数。凌晨日更以跟进新发。',
    ),
    (
        'demo_fin_cb',
        '可转债申购信息 → fin_cb',
        native('bond_zh_cov_info_ths', None, 'fin_cb', tf(MAP_CB, ['bond_code'])),
        'fin_cb',
        '可转债申购',
        CRON_DAWN,
        '同花顺可转债信息中心:债券代码与简称/申购日与申购代码/原股东配售码/每股获配额/计划与实际发行量/中签公布日/中签号/上市日/正股代码与简称/转股价格/到期时间/中签率。凌晨日更。',
    ),
    (
        'demo_fin_daily_p1',
        'A股日线增量·快照第一页 → fin_stock_daily',
        code(AK, C_SPOT_DAILY_P1, 'fin_stock_daily', tf({}, ['symbol', 'date'])),
        'fin_stock_daily',
        '个股日线',
        CRON_CLOSE,
        '从新浪全市场快照「第一页」(约80只)派生当日日线 OHLCV(open=今开/high=最高/low=最低/close=最新价/volume/amount + symbol/name/date)→ fin_stock_daily。收盘后定时增量(只翻第一页、不逐只全抓),与「全量单次」共用同一索引/模型、md5(symbol+date) 去重。',
    ),
    (
        'demo_fin_index',
        '主要指数日线·近250日 → fin_index_daily',
        code(AK, C_INDEX_DAILY, 'fin_index_daily', tf({}, ['symbol', 'date'])),
        'fin_index_daily',
        '指数日线',
        CRON_CLOSE,
        '新浪四大指数(上证指数/深证成指/沪深300/创业板指)日线 OHLCV(英文字段,无需转换),各取最近250个交易日。收盘后日更,适合大盘走势、指数对比。',
    ),
    (
        'demo_fin_idxcons',
        '主要指数成分股 → fin_index_cons',
        code(AK, C_INDEX_CONS, 'fin_index_cons', tf(MAP_IDXCONS, ['index_code', 'code'])),
        'fin_index_cons',
        '指数成分股',
        CRON_DAWN,
        '新浪主要指数成分股(沪深300/上证50/中证500;替代东财 concept_cons 以提升稳定性):个股代码/名称/最新价/涨跌幅/成交量额/市盈率/市净率/市值/换手率,附 index_code/index_name 归属。凌晨日更,适合"指数→成分股"下钻、成分股权重股分析。',
    ),
    (
        'demo_fin_macro',
        '宏观经济·CPI/PPI/PMI/货币供应 → fin_macro',
        code(AK, C_MACRO, 'fin_macro', tf(MAP_MACRO, ['indicator', 'month'])),
        'fin_macro',
        '宏观经济',
        CRON_MONTH,
        '国家统计局/央行月度宏观:CPI(全国/城市/农村当月与同环比累计)、PPI、PMI(制造业/非制造业)、货币供应(M0/M1/M2 数量与同环比),按 indicator 字段区分来源。月度数据,每月1号(02:00)刷新。',
    ),
    (
        'demo_fin_news',
        '个股新闻资讯 → fin_news',
        code(AK, C_NEWS, 'fin_news', tf(MAP_NEWS, ['query_symbol', 'publish_time', 'title'])),
        'fin_news',
        '个股新闻',
        CRON_HOUR,
        '东财个股新闻(贵州茅台/宁德时代/格力电器):关键词/标题/内容/发布时间/来源/链接,附 query_symbol。时效性强,每小时刷新,适合舆情、事件跟踪。',
    ),
    # —— 新增数据集(2026-06-30):资金面/基本面/估值/杠杆/宏观补充 ——
    (
        'demo_fin_mktflow',
        '大盘资金流向·近120日时序 → fin_market_fund_flow',
        native('stock_market_fund_flow', None, 'fin_market_fund_flow', tf(MAP_MKTFLOW, ['date'])),
        'fin_market_fund_flow',
        '大盘资金流',
        CRON_CLOSE,
        '东财沪深大盘资金流时序(约近120日):主力/超大单/大单/中单/小单净流入的净额与净占比,并含上证、深证收盘价与涨跌幅。收盘后日更,适合主力资金趋势折线、各级别资金对比堆叠图、资金与指数联动。',
    ),
    (
        'demo_fin_lhb',
        '龙虎榜明细·近30日 → fin_lhb',
        code(AK, C_LHB, 'fin_lhb', tf(MAP_LHB, ['code', 'list_date'])),
        'fin_lhb',
        '龙虎榜',
        CRON_EVENING,
        '东财龙虎榜近30日明细:代码/名称/上榜日/解读/收盘价涨跌幅/龙虎榜净买入卖出与成交额/市场总成交额/净买额与成交额占比/换手率/流通市值/上榜原因/上榜后1·2·5·10日涨幅。龙虎榜收盘后发布,18:30 晚间日更,适合游资动向、上榜原因分布、上榜后表现统计。',
    ),
    (
        'demo_fin_yjbb',
        '业绩报表·最近报告期 → fin_yjbb',
        code(AK, C_YJBB, 'fin_yjbb', tf(MAP_YJBB, ['code', 'report_period'])),
        'fin_yjbb',
        '业绩报表',
        CRON_DAWN,
        '东财全A股最近已披露报告期业绩(自动回溯季度末):EPS/营业总收入及同比环比/净利润及同比环比/每股净资产/净资产收益率ROE/每股经营现金流/销售毛利率/所处行业,附 report_period。财报季滚动更新,凌晨日更,适合成长性(净利同比)、盈利能力(ROE/毛利)、行业对比。',
    ),
    (
        'demo_fin_indpe',
        '行业市盈率估值·证监会分类 → fin_industry_pe',
        code(AK, C_INDPE, 'fin_industry_pe', tf(MAP_INDPE, ['industry_code', 'date'])),
        'fin_industry_pe',
        '行业市盈率',
        CRON_DAWN,
        '巨潮资讯证监会行业分类静态市盈率(自动回溯最近交易日):行业名称与编码/公司数量/纳入计算公司数/静态总市值与净利润/静态市盈率的加权平均·中位数·算术平均。凌晨日更,适合行业估值横向对比、高低估筛选。',
    ),
    (
        'demo_fin_margin',
        '融资融券余额·上交所近180日 → fin_margin',
        code(AK, C_MARGIN, 'fin_margin', tf(MAP_MARGIN, ['date'])),
        'fin_margin',
        '融资融券',
        CRON_EVENING,
        '上交所两融时序(约近180日):信用交易日期/融资余额/融资买入额/融券余量及金额/融券卖出量/融资融券总余额。交易所收盘后发布,18:30 晚间日更,适合杠杆资金趋势、市场情绪与风险偏好分析。',
    ),
    (
        'demo_fin_etf',
        'ETF 基金实时快照 → fin_etf',
        native('fund_etf_spot_em', None, 'fin_etf', tf(MAP_ETF, ['code'])),
        'fin_etf',
        'ETF快照',
        CRON_INTRADAY,
        '东财全市场ETF行情:最新价/IOPV实时估值/基金折价率/涨跌幅/成交量额/开高低昨收/振幅/换手率/量比委比/内外盘/各级别资金净流入/最新份额/流通与总市值/数据日期。收盘后日更,适合ETF涨幅榜、折溢价、资金流分析。',
    ),
    (
        'demo_fin_gdp',
        '中国GDP·季度 → fin_gdp',
        native('macro_china_gdp', None, 'fin_gdp', tf(MAP_GDP, ['quarter'])),
        'fin_gdp',
        '中国GDP',
        CRON_MONTH,
        '国家统计局季度GDP:国内生产总值绝对值与同比增长,以及第一/第二/第三产业的绝对值与同比。季度数据,每月1号刷新,适合经济增长趋势、产业结构分析。',
    ),
    (
        'demo_fin_lpr',
        'LPR贷款市场报价利率·时序 → fin_lpr',
        native('macro_china_lpr', None, 'fin_lpr', tf(MAP_LPR, ['trade_date'])),
        'fin_lpr',
        'LPR利率',
        CRON_MONTH,
        '央行LPR利率时序:1年期(lpr_1y)与5年期(lpr_5y)贷款市场报价利率及历史利率(原英文大写列已统一为小写下划线)。每月20号公布,每月1号刷新,适合利率走势、货币政策跟踪。',
    ),
    (
        'demo_fin_stock_daily_all',
        '全A股历史日线回填 → fin_stock_daily',
        code_multi([ES, AK], C_ALL_STOCK_DAILY, 'fin_stock_daily', tf({}, ['symbol', 'date'])),
        'fin_stock_daily',  # 与「个股日线(6只)」共用同一索引/模型:schema 相同,md5(symbol+date) 去重
        '个股日线',
        '',  # cron 空 → trigger_type=1 单次(手动触发一次,全量沪深约5000只、耗时较长)
        'A股前复权日线 OHLCV(date/open/high/low/close/volume/amount/turnover + symbol/name),写入 fin_stock_daily。'
        '全量单次回填:复用 fin_stock_spot 全市场代码,逐只 akshare(stock_zh_a_daily 前复权)补全市场约5000只历史(emit 流式、md5(symbol+date) 幂等)。'
        '日常增量由「A股日线增量·快照第一页」定时任务维护,二者共用同一索引/模型。适合K线/均线/个股走势对比。',
    ),
]

# ============================ 红利低波指数专题 demo ============================
# 标的:中证红利低波动指数(H30269)。指数点位+滚动PE 全历史(2013至今)+ 股息率(累积)+ 10Y国债。
C_DIV_INDEX = f"""
import datetime
h = get_handler('{AK}')
end = datetime.date.today().strftime('%Y%m%d')
result = h.query('stock_zh_index_hist_csindex', {{'symbol': 'H30269', 'start_date': '20130101', 'end_date': end}})
print('红利低波指数历史 %d 行' % len(result))
"""
C_DIV_VAL = f"""
h = get_handler('{AK}')
result = h.query('stock_zh_index_value_csindex', {{'symbol': 'H30269'}})
print('红利低波股息率 %d 行(csindex 近20日,累积成史)' % len(result))
"""
C_DIV_BOND = f"""
h = get_handler('{AK}')
rows = h.query('bond_zh_us_rate', {{'start_date': '20130101'}})
# 取数阶段清洗:剔除 10年收益率为 0/空的脏数据行(到期收益率不可能为 0,多为源站缺失填 0)
result = []
for r in rows:
    v = r.get('中国国债收益率10年')
    if v is None or v == '' or v != v:  # 空/NaN
        continue
    try:
        if float(v) == 0:               # 脏数据:值为 0
            continue
    except (TypeError, ValueError):
        continue
    result.append(r)
print('国债收益率 %d 行(清洗后,原 %d 行)' % (len(result), len(rows)))
"""
TF_DIV_INDEX = (
    'def transform(row):\n'
    '    import hashlib\n'
    "    d = str(row.get('日期', ''))\n"
    '    def f(v):\n'
    '        return None if v is None or v != v else v\n'
    "    return {'date': d, 'open': f(row.get('开盘')), 'high': f(row.get('最高')),\n"
    "            'low': f(row.get('最低')), 'close': f(row.get('收盘')),\n"
    "            'change_pct': f(row.get('涨跌幅')), 'volume': f(row.get('成交量')),\n"
    "            'amount': f(row.get('成交金额')), 'pe': f(row.get('滚动市盈率')),\n"
    "            '_id': hashlib.md5(d.encode('utf-8')).hexdigest()}\n"
)
TF_DIV_VAL = (
    'def transform(row):\n'
    '    import hashlib\n'
    "    d = str(row.get('日期', ''))\n"
    '    def f(v):\n'
    '        return None if v is None or v != v else v\n'
    "    return {'date': d, 'index_code': row.get('指数代码'),\n"
    "            'pe': f(row.get('市盈率1')), 'dividend_yield': f(row.get('股息率1')),\n"
    "            'dividend_yield2': f(row.get('股息率2')),\n"
    "            '_id': hashlib.md5(d.encode('utf-8')).hexdigest()}\n"
)
TF_DIV_BOND = (
    'def transform(row):\n'
    '    import hashlib\n'
    "    d = str(row.get('日期', ''))\n"
    "    v = row.get('中国国债收益率10年')\n"
    "    v = None if v is None or v != v else v\n"
    "    return {'date': d, 'bond_10y': v, '_id': hashlib.md5(d.encode('utf-8')).hexdigest()}\n"
)
# 收盘后日更(交易日 16 点错峰)。(id, name, params, idx, label, cron, desc)
TASKS += [
    ('div_index_h30269', '红利低波指数(H30269)历史',
     code(AK, C_DIV_INDEX, 'div_index_h30269', TF_DIV_INDEX), 'div_index_h30269',
     '中证红利低波动指数(H30269)历史:点位/涨跌幅/成交/滚动PE', '0 5 16 ? * 2-6 *',
     '红利低波指数全历史(2013至今):open/high/low/close/change_pct/volume/amount/pe(滚动市盈率),中证官方。点位与 PE 全历史,可算估值分位/相关性。'),
    ('div_valuation', '红利低波指数股息率',
     code(AK, C_DIV_VAL, 'div_valuation', TF_DIV_VAL), 'div_valuation',
     '中证红利低波动指数(H30269)股息率(中证官方)', '0 8 16 ? * 2-6 *',
     '红利低波股息率 dividend_yield(%)+ pe(当前口径),中证官方仅回近~20交易日,按日累积成史。'),
    ('div_bond10y', '中国10年期国债收益率',
     code(AK, C_DIV_BOND, 'div_bond10y', TF_DIV_BOND), 'div_bond10y',
     '中国10年期国债收益率(股债利差用)', '0 11 16 ? * 2-6 *',
     '中国10年期国债到期收益率 bond_10y(%),用于股债利差=国债−股息率。'),
]

# 红利低波看板(指数点位/PE全历史 + 股息率 + 国债 + 估值明细)
DIV_DASH_ID = 'demo_board_dividend'


def _divline(cid, model, idx, y, title, unit, x, ypos, w, h, start_var=False):
    # start_var=True:native 用 date>= {{start}} 的 range,随看板筛选栏「起始日期」联动重刷;
    # 否则 match_all(不受筛选影响)——借此演示「作用范围」:只有引用了 {{start}} 的图才联动。
    query = {'range': {'date': {'gte': '{{start}}'}}} if start_var else {'match_all': {}}
    return {
        'id': cid, 'type': 'chart',
        'inline': {'modelId': model,
                   'native': {'index': idx, 'body': {'query': query, 'size': 5000}},
                   'chartSpec': {'type': 'line', 'x': 'date', 'ys': [{'field': y, 'agg': 'sum'}],
                                 'sort': {'by': '__x__', 'dir': 'asc'},
                                 'style': {'title': title, 'smooth': True, **({'unit': unit} if unit else {})}}},
        'pos': {'x': x, 'y': ypos, 'w': w, 'h': h}, 'props': {'title': title}, 'subscribe': True,
    }


DIV_DASH_COMPONENTS = [
    _divline('c1', 'dm_div_index_h30269', 'div_index_h30269', 'close', '红利低波指数(H30269)点位走势·全历史', '', 0, 0, 24, 7, start_var=True),
    _divline('c2', 'dm_div_index_h30269', 'div_index_h30269', 'pe', '红利低波 滚动市盈率PE·全历史(可算分位)', '', 0, 7, 12, 7, start_var=True),
    _divline('c3', 'dm_div_valuation', 'div_valuation', 'dividend_yield', '红利低波 股息率历史(%,累积中)', '%', 12, 7, 12, 7),
    _divline('c4', 'dm_div_bond10y', 'div_bond10y', 'bond_10y', '中国10年期国债收益率(%)', '%', 0, 14, 12, 7),
    {'id': 'c5', 'type': 'chart',
     'inline': {'modelId': 'dm_div_valuation',
                'native': {'index': 'div_valuation', 'body': {'query': {'match_all': {}}, 'size': 60}},
                'chartSpec': {'type': 'table', 'x': 'date',
                              'ys': [{'field': 'dividend_yield', 'agg': 'none'}, {'field': 'pe', 'agg': 'none'}],
                              'style': {'title': '红利低波估值明细(股息率/PE)'}}},
     'pos': {'x': 12, 'y': 14, 'w': 12, 'h': 7}, 'props': {'title': '红利低波估值明细'}, 'subscribe': True},
]
DIV_DASH_CANVAS = {'mode': 'matrix', 'cols': 24}
# 看板变量(联动):顶部筛选栏「起始日期」→ 图表 native 里的 {{start}} 占位;改值即重刷 c1/c2
DIV_DASH_FILTERS = [{'name': 'start', 'label': '起始日期', 'type': 'date', 'default': '2020-01-01'}]

# 红利低波数据分析助手(内置「三重黄金坑」择时框架为领域知识)
DIV_APP_ID = 9002
DIV_APP_PROMPT = """# 角色
你是「红利低波数据分析助手」,围绕中证红利低波动指数(H30269),用平台沉淀的数据做**估值/性价比/择时**分析并产出图表。定位:估值与性价比监控,不构成投资建议。

## 数据(数据源 `demo_es`,可用 `akshare_cn` 取最新)
- `div_index_h30269`:红利低波指数全历史(2013至今)date/open/high/low/close/change_pct/volume/amount/**pe(滚动市盈率)**
- `div_valuation`:红利低波股息率 date/dividend_yield(%)/pe(当前口径),中证官方按日累积
- `div_bond10y`:中国10年期国债收益率 date/bond_10y(%)

## 领域框架:红利低波「三重黄金坑」择时(经验规则,须用历史分位校准,勿盲信)
- 信号①股息率:>5.5% 黄金坑(越高越买)、<5% 谨慎、<4.5% 危险(越高=越便宜)
- 信号②市盈率PE:<8 好、>9 管住手、>9.5 危险
- 信号③股债利差=10年国债−股息率:<−3.5% 很值、<−3% 可布局(负得越多越划算)
- 满足≥2 信号→可分批;满足3→加到目标仓位。PE>9.5 且 股息率<4.5% 别重仓。12月/1月红利胜率偏高(样本少,仅参考)。

## 工作流程
1. get_table_schema 查上面三个索引字段(文本字段聚合用 .keyword;取时序写足 size)。
2. run_datasource_query 对 demo_es 取数;需要最新值用 akshare_cn(stock_zh_index_value_csindex 'H30269' 取当前股息率、bond_zh_us_rate 取国债)。
3. 沙箱 pandas 计算 + pyecharts 绘图(内联展示)。
4. 关系分析:PE 历史分位(div_index_h30269.pe 全历史,可靠)、点位↔PE、股债利差、股息率分位(样本较短需说明)。
5. 给出:当前三信号状态(满足几个)+ 结论 + 图/表。

## 注意
- **PE、点位是全历史(2013起)**,分位/相关性可靠;**股息率**由 csindex 每日累积、样本较短,做分位/相关性要说明区间。
- 阈值是自媒体经验值,鼓励用平台历史分位重新校准。免责:数据分析/估值监控,非投资建议。
"""
DIV_APP_CONFIG = {
    'prompt': DIV_APP_PROMPT,
    'prologue': '你好!我是红利低波数据分析助手。围绕中证红利低波动指数(H30269),分析点位/PE/股息率/股债利差与估值分位,评估「三重黄金坑」信号并画图。试试下面的预设问题。',
    'presetQuestions': [
        '现在红利低波满足几个「黄金坑」信号?给出股息率/PE/股债利差当前值与判断',
        '红利低波指数滚动PE现在处于 2013 年以来什么分位?画历史PE折线并标注分位',
        '把红利低波指数点位与滚动PE画成双轴,看估值与价格关系',
        '股债利差(10年国债−股息率)现在多少?画历史走势并标注 -3%/-3.5%',
        '红利低波指数近三年点位走势,并计算年化收益与最大回撤',
        '红利低波股息率现在多少、处于已累积样本的什么分位?',
    ],
    'quickCommands': [
        {'name': '黄金坑信号', 'content': '汇总当前股息率、PE、股债利差,判断满足几个「三重黄金坑」信号并给结论'},
        {'name': 'PE分位', 'content': '红利低波滚动PE当前值与 2013 年以来历史分位,折线图+分位标注'},
        {'name': '股债利差', 'content': '10年国债−红利低波股息率的历史走势,折线图,标注 -3%/-3.5%'},
        {'name': '指数走势', 'content': '红利低波指数近三年点位走势,折线图并点评'},
    ],
    'toolIds': [], 'datasetIds': [], 'datasourceCodes': [ES, AK],
    'enableMemory': False, 'model': {'modelId': 0, 'temperature': None, 'maxTokens': None},
}

# 数据源(自包含:不依赖 ezdata.sql 的 demo 段)。(id, name, code, source_type, family, config_dict)
DATASOURCES = [
    ('seed-akshare-cn', 'AKShare 财经数据', AK, 'akshare', 'api', {}),
    (
        'seed-demo-es',
        '演示-Elasticsearch',
        ES,
        'elasticsearch',
        'search',
        {'hosts': 'http://ezdata-es:9200', 'user': 'elastic', 'password': 'ezdata123456'},
    ),
]

# 演示看板:A股市场总览(多图看板 dash_type=board)。组件全部用真实种子模型出图,矩阵 24 列布局。
DASH_ID = 'demo_board_market'


def _dcomp(cid, model, idx, size, chartspec, x, y, w, h):
    return {
        'id': cid, 'type': 'chart',
        'inline': {
            'modelId': model,
            'native': {'index': idx, 'body': {'query': {'match_all': {}}, 'size': size}},
            'chartSpec': chartspec,
        },
        'pos': {'x': x, 'y': y, 'w': w, 'h': h},
        'props': {'title': chartspec['style']['title']},
        'subscribe': True,
    }


DASH_COMPONENTS = [
    _dcomp('c1', 'dm_fin_index_daily', 'fin_index_daily', 4000,
           {'type': 'line', 'x': 'date', 'ys': [{'field': 'close', 'agg': 'sum'}], 'series': 'name',
            'style': {'title': '主要指数日线走势', 'legend': True, 'smooth': True}}, 0, 0, 24, 7),
    _dcomp('c2', 'dm_fin_industry_summary', 'fin_industry_summary', 200,
           {'type': 'bar', 'x': 'board_name', 'ys': [{'field': 'change_pct', 'agg': 'sum'}],
            'sort': {'by': 'change_pct', 'dir': 'desc'}, 'topN': 12,
            'style': {'title': '行业涨跌幅 Top12(%)', 'label': True}}, 0, 7, 12, 7),
    _dcomp('c3', 'dm_fin_concept_board', 'fin_concept_board', 400,
           {'type': 'bar', 'x': 'board_name', 'ys': [{'field': 'change_pct', 'agg': 'sum'}],
            'sort': {'by': 'change_pct', 'dir': 'desc'}, 'topN': 12,
            'style': {'title': '概念板块涨幅 Top12(%)'}}, 12, 7, 12, 7),
    _dcomp('c4', 'dm_fin_market_fund_flow', 'fin_market_fund_flow', 200,
           {'type': 'line', 'x': 'date', 'ys': [{'field': 'main_net', 'agg': 'sum'}],
            'style': {'title': '大盘主力净流入趋势(亿元)', 'unit': '元', 'scale': 'yi'}}, 0, 14, 12, 7),
    _dcomp('c5', 'dm_fin_industry_pe', 'fin_industry_pe', 300,
           {'type': 'bar', 'x': 'industry_name', 'ys': [{'field': 'pe_weighted', 'agg': 'sum'}],
            'sort': {'by': 'pe_weighted', 'dir': 'desc'}, 'topN': 12,
            'style': {'title': '行业加权市盈率 Top12'}}, 12, 14, 12, 7),
]
DASH_CANVAS = {'mode': 'matrix', 'cols': 24}


APP_ID = 9001
APP_PROMPT = """# 角色
你是「财经数据分析助手」,擅长用平台已沉淀的财经数据回答行情、板块、情绪、宏观问题,并产出图表。

## 数据
所有数据在数据源 `demo_es`(Elasticsearch)的 fin_* 索引里:
- 行情:fin_stock_spot(A股全市场快照)、fin_stock_daily(龙头股日线)、fin_index_daily(主要指数日线)、fin_etf(ETF快照)
- 情绪/资金:fin_zt_pool(当日涨停池)、fin_market_activity(市场活跃度)、fin_market_fund_flow(大盘资金流时序)、fin_lhb(龙虎榜近30日)、fin_margin(两融余额时序)
- 板块/选股:fin_concept_board(概念板块)、fin_concept_summary(概念解析)、fin_industry_summary(行业)、fin_index_cons(主要指数成分股)、fin_cxg/fin_lxsz(技术选股)
- 基本面/估值:fin_yjbb(业绩报表)、fin_industry_pe(行业市盈率)
- 一级/宏观:fin_ipo(新股)、fin_cb(可转债)、fin_macro(CPI/PPI/PMI/货币)、fin_gdp(GDP季度)、fin_lpr(LPR利率)、fin_news(个股新闻)
也可用 `akshare_cn` 实时取最新数据。

## 工作流程
1. 先用 get_table_schema 查相关索引的字段(字段均为英文/缩写,如 code/name/price/change_pct/volume/amount/turnover_rate/industry/board_name;日线 date/open/close/high/low/volume)。
2. 用 run_datasource_query 对 demo_es 写 ES DSL 取数或聚合(query/aggs);需要实时数据再查 akshare_cn。
3. 在沙箱用 pandas 计算、用 pyecharts 绘图(图表会内联展示给用户)。
4. 给出简明结论 + 图/表。

## 取数要点(避免常见报错)
- 文本字段(name/industry/board_name/concept 等)做 terms 聚合/精确匹配/排序时,用带 .keyword 的子字段(schema 会列出,如 industry.keyword);不要对 text 主字段聚合。
- 取时间序列/明细(如个股日线)务必写足 size(如 size:300),ES 默认只回 10 条,否则 K 线/折线会残缺。
- 需要 Top-N 时在沙箱代码里 sorted(...)[:N] 排序切片后再产出,别靠预览目测。
- 数据为演示快照,涨停池/活跃度为当日,不要臆造不存在的历史。
"""
APP_CONFIG = {
    'prompt': APP_PROMPT,
    'prologue': '你好!我是财经数据分析助手。我可以分析 A股行情/涨停/资金流/龙虎榜/业绩/估值/宏观等数据并画图,试试下面的预设问题,或直接问我。',
    'presetQuestions': [
        '贵州茅台近一年日线走势,画K线图并简要点评',
        '今天涨停池里涨停家数最多的行业 Top5,用柱状图展示',
        '近120天大盘主力资金净流入趋势,折线图',
        '龙虎榜近30日净买额最高的个股 Top10',
        '最近报告期净利润同比增速最高的 20 只股票',
        '各证监会行业的静态市盈率对比,找出估值最低的5个行业',
    ],
    # 快捷指令是 {name, content} 对象(点按钮即发送 content);写成纯字符串前端会因缺 name/content 被过滤成空。
    'quickCommands': [
        {'name': '查行情', 'content': 'A股全市场今日涨幅榜前20,用表格展示'},
        {'name': '看涨停', 'content': '今日涨停池按行业分布的涨停家数 Top5,用柱状图展示'},
        {'name': '资金流', 'content': '近120天大盘主力与超大单资金净流入趋势,折线图'},
        {'name': '龙虎榜', 'content': '龙虎榜近30日净买额最高的个股 Top10,并统计上榜原因分布'},
        {'name': '看业绩', 'content': '最近报告期各行业平均净资产收益率ROE对比,柱状图'},
        {'name': '估值对比', 'content': '各证监会行业静态市盈率(加权平均)对比,找出最高和最低的5个行业'},
        {'name': '宏观数据', 'content': '最新 CPI/PPI/PMI 与 LPR 利率概览'},
    ],
    'toolIds': [],
    'datasetIds': [],
    'datasourceCodes': [ES, AK],
    'enableMemory': False,
    'model': {'modelId': 0, 'temperature': None, 'maxTokens': None},
}

# ============================ 每日多市场股票分析 demo(对标 daily_stock_analysis)============================
# A股/港股/美股各 6 只观察池 → akshare 日线 + pandas 技术指标(MA/RSI/MACD/KDJ)→ fin_watch_daily;
# 决策报告任务读指标 + 大盘上下文 → 规则打分(+可选 LLM 叙述)→ fin_daily_report,末尾按 env 推送到群机器人。

# 自选股日线 + 技术指标(逐只按市场取 akshare 日线,pandas 算指标,取近120根 emit 流式装载)
C_WATCH_DAILY = """
import pandas as pd

WATCH = {
    'A': [('sh600519','贵州茅台'),('sz300750','宁德时代'),('sz000651','格力电器'),
          ('sh601318','中国平安'),('sz000858','五粮液'),('sz002594','比亚迪')],
    'HK': [('00700','腾讯控股'),('09988','阿里巴巴-W'),('03690','美团-W'),
           ('01810','小米集团-W'),('00939','建设银行'),('02318','中国平安')],
    'US': [('AAPL','苹果'),('MSFT','微软'),('NVDA','英伟达'),
           ('TSLA','特斯拉'),('GOOGL','谷歌-A'),('AMZN','亚马逊')],
}
FUNC = {'A': 'stock_zh_a_daily', 'HK': 'stock_hk_daily', 'US': 'stock_us_daily'}

def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def _col(df, *names):
    for n in names:
        if n in df.columns:
            return pd.to_numeric(df[n], errors='coerce')
    return pd.Series([float('nan')] * len(df))

def indicators(df):
    close = _col(df, 'close', '收盘', '收盘价')
    high = _col(df, 'high', '最高', '最高价')
    low = _col(df, 'low', '最低', '最低价')
    out = pd.DataFrame(index=df.index)
    for n in (5, 10, 20, 60):
        out['ma%d' % n] = close.rolling(n).mean()
    diff = close.diff()
    gain = diff.clip(lower=0)
    loss = (-diff).clip(lower=0)
    ag = gain.ewm(alpha=1/14, adjust=False).mean()
    al = loss.ewm(alpha=1/14, adjust=False).mean().replace(0, float('nan'))
    out['rsi14'] = 100 - 100 / (1 + ag / al)
    e12 = close.ewm(span=12, adjust=False).mean()
    e26 = close.ewm(span=26, adjust=False).mean()
    dif = e12 - e26
    dea = dif.ewm(span=9, adjust=False).mean()
    out['macd_dif'] = dif
    out['macd_dea'] = dea
    out['macd'] = (dif - dea) * 2
    lmin = low.rolling(9).min()
    hmax = high.rolling(9).max()
    rsv = (close - lmin) / (hmax - lmin).replace(0, float('nan')) * 100
    k = rsv.ewm(alpha=1/3, adjust=False).mean()
    d = k.ewm(alpha=1/3, adjust=False).mean()
    out['kdj_k'] = k
    out['kdj_d'] = d
    out['kdj_j'] = 3 * k - 2 * d
    out['change_pct'] = close.pct_change() * 100
    return out

IND_COLS = ('ma5','ma10','ma20','ma60','rsi14','macd_dif','macd_dea','macd','kdj_k','kdj_d','kdj_j','change_pct')
total = 0
for market, lst in WATCH.items():
    for sym, nm in lst:
        try:
            params = {'symbol': sym}
            if market == 'A':
                params['adjust'] = 'qfq'
            raw = handler.query(FUNC[market], params)
        except Exception as e:
            print('跳过 %s/%s: %s' % (market, sym, e))
            continue
        if not raw:
            continue
        df = pd.DataFrame(raw).reset_index(drop=True)
        ind = indicators(df)
        n = len(df)
        rows = []
        for i in range(max(0, n - 120), n):
            d = df.iloc[i]
            r = {'market': market, 'symbol': sym, 'name': nm,
                 'date': str(d.get('date') or d.get('日期') or '')[:10],
                 'open': _num(d.get('open', d.get('开盘'))),
                 'high': _num(d.get('high', d.get('最高'))),
                 'low': _num(d.get('low', d.get('最低'))),
                 'close': _num(d.get('close', d.get('收盘'))),
                 'volume': _num(d.get('volume', d.get('成交量'))),
                 'amount': _num(d.get('amount', d.get('成交额')))}
            for c in IND_COLS:
                v = ind.iloc[i][c]
                r[c] = None if v != v else round(float(v), 4)
            rows.append(r)
        if rows:
            emit(rows)
            total += len(rows)
        print('%s/%s(%s) %d 行' % (market, sym, nm, len(rows)))
print('自选股日线+指标完成,共 %d 行 → fin_watch_daily' % total)
result = []
"""

# 决策报告:读 fin_watch_daily 最新指标 → 规则打分 + 可选 LLM 叙述 → fin_daily_report,末尾按 env 推送
C_DAILY_REPORT = """
import datetime
import os

es = get_handler('demo_es')
today = datetime.date.today().isoformat()
MKT_NAME = {'A': 'A股', 'HK': '港股', 'US': '美股'}

def _q(idx, body):
    try:
        return es.query({'index': idx, 'body': body}) or []
    except Exception as e:
        print('查询 %s 失败(%s),按空处理' % (idx, e))
        return []

def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

# 1) 自选股最新技术指标
latest = {}
for r in _q('fin_watch_daily', {'query': {'match_all': {}}, 'size': 20000}):
    s = r.get('symbol')
    dt = r.get('date') or ''
    if not s:
        continue
    if s not in latest or dt > (latest[s].get('date') or ''):
        latest[s] = r
print('自选股最新指标 %d 只(来自 fin_watch_daily)' % len(latest))

# 2) 融合上下文:A股基本面(业绩报表)/个股新闻/大盘背景(平台已有 ES 索引)
def _code6(sym):
    s = str(sym or '')
    return s[2:] if s[:2] in ('sh', 'sz', 'bj') else s

yjbb = {}  # 6位代码 -> 业绩报表最新报告期
for r in _q('fin_yjbb', {'query': {'match_all': {}}, 'size': 6000}):
    c = str(r.get('code') or '')
    if c and (c not in yjbb or (r.get('report_period') or '') > (yjbb[c].get('report_period') or '')):
        yjbb[c] = r
news = {}  # 6位代码 -> 新闻列表
for r in _q('fin_news', {'query': {'match_all': {}}, 'size': 2000}):
    c = str(r.get('query_symbol') or '')
    if c:
        news.setdefault(c, []).append(r)

def _latest_row(idx, date_field='date'):
    rs = [x for x in _q(idx, {'query': {'match_all': {}}, 'size': 400}) if x.get(date_field)]
    return max(rs, key=lambda x: x.get(date_field) or '') if rs else {}

flow = _latest_row('fin_market_fund_flow')
activity = {r.get('item'): r.get('value') for r in _q('fin_market_activity', {'query': {'match_all': {}}, 'size': 50}) if r.get('item')}
zt_cnt = len(_q('fin_zt_pool', {'query': {'match_all': {}}, 'size': 2000}))
main_net = _f(flow.get('main_net'))
a_tilt = 2 if (main_net or 0) > 0 else -2 if (main_net or 0) < 0 else 0
backdrop = 'A股大盘背景:主力净流入%s;涨停%d家;活跃度%s' % (
    ('%.1f亿元' % (main_net / 1e8)) if main_net is not None else '—', zt_cnt, activity.get('活跃度', '—'))
print(backdrop)

def fund_of(sym, market):
    return yjbb.get(_code6(sym)) if market == 'A' else None

def news_of(sym, market):
    if market != 'A':
        return []
    lst = sorted(news.get(_code6(sym)) or [], key=lambda x: x.get('publish_time') or '', reverse=True)
    return lst[:3]

# 把各维度拆成 4 个因子增量,不同策略给不同权重 → 同一份数据、不同策略出不同结论
def factors(r, fund, news_cnt, market):
    close, ma20, ma60 = r.get('close'), r.get('ma20'), r.get('ma60')
    rsi, macd, j, chg = r.get('rsi14'), r.get('macd'), r.get('kdj_j'), r.get('change_pct')
    f = {'trend': 0.0, 'momentum': 0.0, 'growth': 0.0, 'event': 0.0}
    if close and ma20 and ma60:
        f['trend'] = 18.0 if close > ma20 > ma60 else 8.0 if close > ma20 else -18.0 if close < ma20 < ma60 else -6.0
    m = 0.0
    if macd is not None:
        m += 8 if macd > 0 else -8
    if rsi is not None:
        m += -6 if rsi >= 70 else 6 if rsi <= 30 else 4 if rsi >= 55 else 0
    if j is not None:
        m += -5 if j >= 100 else 5 if j <= 0 else 0
    f['momentum'] = m
    if fund:
        npy, roe = _f(fund.get('net_profit_yoy')), _f(fund.get('roe'))
        g = 0.0
        if npy is not None:
            g += 6 if npy > 0 else -8
        if roe is not None and roe >= 15:
            g += 6
        f['growth'] = g
    ev = min(news_cnt, 2) * 4.0
    if chg is not None:
        ev += 5 if chg > 3 else -5 if chg < -3 else 0
    if market == 'A':
        ev += a_tilt * 2 + (2 if zt_cnt > 50 else 0)
    f['event'] = ev
    return f

# 可切换策略(对标 daily_stock_analysis 的策略选择):名称 + 因子权重 + LLM 侧重提示词
STRATEGIES = [
    {'name': '趋势跟随', 'w': {'trend': 1.0, 'momentum': 1.0, 'growth': 0.3, 'event': 0.4},
     'sys': '你按"趋势跟随"策略研判:重点看均线多空排列与 MACD/动量,顺势而为、回避均线空头与破位,基本面/消息仅作辅助。'},
    {'name': '成长质量', 'w': {'trend': 0.4, 'momentum': 0.3, 'growth': 1.6, 'event': 0.2},
     'sys': '你按"成长质量"策略研判:重点看净利润同比增速、ROE、毛利率等基本面质量,优选高成长高盈利,技术面仅作择时;无基本面(港美股)时以技术面为准并说明。'},
    {'name': '热点事件', 'w': {'trend': 0.5, 'momentum': 0.7, 'growth': 0.2, 'event': 1.6},
     'sys': '你按"热点事件"策略研判:重点看近期新闻催化、涨停/资金情绪、短期涨跌幅等事件驱动信号,关注题材与资金并提示追高风险。'},
]
_DISC = '用不超过100字中文给出多空研判与关键理由,口吻中性专业,不承诺收益,结尾固定加"(仅供参考,不构成投资建议)"。'

def action_of(sc):
    return '买入' if sc >= 68 else '持有' if sc >= 55 else '观望' if sc >= 42 else '回避'

def combine(f, w):
    sc = 50 + w['trend'] * f['trend'] + w['momentum'] * f['momentum'] + w['growth'] * f['growth'] + w['event'] * f['event']
    return int(max(0, min(100, round(sc))))

def rule_reason(r, fund, news_cnt, strat, sc, act):
    p = ['[%s]' % strat['name']]
    close, ma20, ma60 = r.get('close'), r.get('ma20'), r.get('ma60')
    if close and ma20 and ma60:
        p.append('均线多头排列' if close > ma20 > ma60 else '均线空头排列' if close < ma20 < ma60 else '均线纠缠')
    if r.get('macd') is not None:
        p.append('MACD' + ('翻红' if r['macd'] > 0 else '翻绿'))
    if r.get('rsi14') is not None:
        p.append('RSI14=%.0f' % r['rsi14'])
    if fund:
        npy, roe = _f(fund.get('net_profit_yoy')), _f(fund.get('roe'))
        if npy is not None:
            p.append('净利同比%+.0f%%' % npy)
        if roe is not None:
            p.append('ROE=%.1f' % roe)
    if news_cnt:
        p.append('新闻%d条' % news_cnt)
    return '；'.join(p) + '。评分%d→%s' % (sc, act)

llm = None
try:
    from ezdata.interface.web.llm import LLMClient
    _c = LLMClient()
    if _c.ready:
        llm = _c
        print('LLM 已就绪,生成融合研判')
    else:
        print('LLM 未配置(缺 LLM_API_KEY/LLM_MODEL),使用规则理由')
except Exception as e:
    print('LLM 不可用(%s),使用规则理由' % e)

def llm_reason(r, fund, news_list, strat, sc, act):
    if llm is None:
        return None
    parts = ['市场=%s 代码=%s 名称=%s' % (r.get('market'), r.get('symbol'), r.get('name')),
             '技术面: 收盘=%s MA20=%s MA60=%s RSI14=%s MACD=%s KDJ_J=%s 涨跌幅=%s%%'
             % (r.get('close'), r.get('ma20'), r.get('ma60'), r.get('rsi14'), r.get('macd'), r.get('kdj_j'), r.get('change_pct'))]
    if fund:
        parts.append('基本面: 净利同比=%s%% ROE=%s 毛利率=%s%% 行业=%s'
                     % (fund.get('net_profit_yoy'), fund.get('roe'), fund.get('gross_margin'), fund.get('industry')))
    if news_list:
        parts.append('近期新闻: ' + ' / '.join((n.get('title') or '')[:30] for n in news_list))
    if r.get('market') == 'A':
        parts.append(backdrop)
    parts.append('规则结论=%s(评分%d)' % (act, sc))
    try:
        # 每套策略用各自 system 提示词(侧重不同);temperature=None 跳过 complete 默认 0.0(opus-4-8 弃用会 400)
        txt = (llm.complete('\\n'.join(parts), system=strat['sys'] + _DISC, temperature=None) or '').strip()
    except Exception as e:
        print('LLM 生成失败(%s),回退规则理由' % e)
        return None
    low = txt.lower()
    # agno 部分版本会吞掉 provider 报错、把错误串当 content 返回;识别到就回退规则理由
    if len(txt) < 4 or 'error code' in low or 'invalid_request' in low or 'error in agent' in low:
        print('LLM 返回异常内容,回退规则理由:%s' % txt[:80])
        return None
    return txt[:240]

result = []
stat = {}  # (market, strategy) -> 统计
for s, r in latest.items():
    mk = r.get('market')
    fund = fund_of(s, mk)
    news_list = news_of(s, mk)
    ncnt = len(news_list)
    f = factors(r, fund, ncnt, mk)  # 因子只算一次,各策略共享
    base = {'date': today, 'market': mk, 'symbol': s, 'name': r.get('name'),
            'close': r.get('close'), 'change_pct': r.get('change_pct'),
            'ma20': r.get('ma20'), 'ma60': r.get('ma60'), 'rsi14': r.get('rsi14'),
            'macd': r.get('macd'), 'kdj_j': r.get('kdj_j'),
            'net_profit_yoy': _f(fund.get('net_profit_yoy')) if fund else None,
            'roe': _f(fund.get('roe')) if fund else None, 'news_cnt': ncnt}
    for strat in STRATEGIES:
        sc = combine(f, strat['w'])
        act = action_of(sc)
        reason = llm_reason(r, fund, news_list, strat, sc, act) or rule_reason(r, fund, ncnt, strat, sc, act)
        row = dict(base)
        row.update({'strategy': strat['name'], 'action': act, 'score': sc, 'reason': reason})
        result.append(row)
        d = stat.setdefault((mk, strat['name']), {'n': 0, 'bull': 0, 'sum': 0})
        d['n'] += 1
        d['sum'] += sc
        if act in ('买入', '持有'):
            d['bull'] += 1

for (mk, sname), d in stat.items():
    n = d['n'] or 1
    breadth = round(100.0 * d['bull'] / n)
    avg = round(d['sum'] / n)
    tone = '偏多' if breadth >= 60 else '偏空' if breadth <= 35 else '中性'
    extra = ('  ' + backdrop) if mk == 'A' else ''
    result.append({'date': today, 'market': mk, 'symbol': '__MARKET__', 'strategy': sname,
                   'name': '%s·%s综述' % (MKT_NAME.get(mk, mk), sname), 'action': tone, 'score': breadth,
                   'reason': '[%s]%s自选池%d只,看多占比%d%%(均分%d),整体%s。%s(仅供参考,不构成投资建议)'
                             % (sname, MKT_NAME.get(mk, mk), d['n'], breadth, avg, tone, extra)})
print('生成多策略融合决策报告 %d 行(%d 策略×%d 市场;基本面命中 %d 行/新闻命中 %d 行)→ fin_daily_report'
      % (len(result), len(STRATEGIES), len({m for m, _ in stat}),
         sum(1 for x in result if x.get('roe') is not None),
         sum(1 for x in result if x.get('news_cnt'))))

# —— 推送(env 驱动:配了哪个渠道的 webhook 就推哪个,都没配则跳过,不报错)——
confs = []
for _env, _ctype in [('DEMO_PUSH_WECOM', 'wecom'), ('DEMO_PUSH_FEISHU', 'feishu'), ('DEMO_PUSH_DINGTALK', 'dingtalk')]:
    _url = os.environ.get(_env)
    if _url:
        confs.append({'type': _ctype, 'webhook_url': _url})
if not confs:
    print('未配置推送 webhook(DEMO_PUSH_WECOM/FEISHU/DINGTALK),跳过推送')
else:
    _strat = os.environ.get('DEMO_PUSH_STRATEGY') or STRATEGIES[0]['name']  # 推送用哪套策略(默认第一套)
    _lines = ['# 每日多市场股票分析 %s(策略:%s)' % (today, _strat)]
    for mk in ('A', 'HK', 'US'):
        _picks = sorted([x for x in result if x['market'] == mk and x['symbol'] != '__MARKET__' and x.get('strategy') == _strat],
                        key=lambda x: x['score'], reverse=True)
        _summ = [x for x in result if x['market'] == mk and x['symbol'] == '__MARKET__' and x.get('strategy') == _strat]
        _lines.append('\\n## %s  %s' % (MKT_NAME.get(mk, mk), _summ[0]['reason'] if _summ else ''))
        for x in _picks[:3]:
            _lines.append('- %s(%s) %s 评分%d' % (x['name'], x['symbol'], x['action'], x['score']))
    try:
        from module_alert.channels.base import dispatch_forward
        dispatch_forward({'title': '每日多市场股票分析 %s' % today, 'content': '\\n'.join(_lines)}, confs)
        print('已推送到 %d 个渠道(策略:%s)' % (len(confs), _strat))
    except Exception as e:
        print('推送失败(%s)' % e)
"""

# 观察池只 18 只,轮询 akshare 约 1-2 分钟。crons:美股盘后+A/H 上一交易日均已收 → 早晨统一出报告
CRON_WATCH = '0 40 6 * * ? *'  # 每天 06:40 抓三市场自选股日线+指标
CRON_REPORT = '0 10 7 * * ? *'  # 每天 07:10 生成决策报告并推送(紧随 watch)

TASKS += [
    (
        'demo_fin_watch_daily',
        '自选股日线+技术指标(A/H/US)→ fin_watch_daily',
        code(AK, C_WATCH_DAILY, 'fin_watch_daily', tf({}, ['market', 'symbol', 'date'])),
        'fin_watch_daily',
        '自选股日线+指标',
        CRON_WATCH,
        'A股/港股/美股各6只观察池(茅台/宁德/平安/腾讯/阿里/小米/苹果/英伟达/特斯拉等),逐只 akshare 日线(A股前复权)+ pandas 计算 '
        'MA5/10/20/60、RSI14、MACD(dif/dea/macd)、KDJ(k/d/j)、涨跌幅,取近120根 emit 流式装载。'
        'market 区分市场,md5(market+symbol+date) 幂等。每天06:40更新,是决策报告与K线/均线看板的数据底座。',
    ),
    (
        'demo_fin_daily_report',
        '每日多市场·多策略融合决策报告(技术+基本面+新闻+大盘)→ fin_daily_report',
        code(ES, C_DAILY_REPORT, 'fin_daily_report', tf({}, ['date', 'market', 'symbol', 'strategy'])),
        'fin_daily_report',
        '每日决策报告',
        CRON_REPORT,
        '读 fin_watch_daily 每只最新指标,融合平台已有数据:A股基本面(fin_yjbb 净利同比/ROE/毛利)、个股新闻(fin_news)、'
        '大盘背景(fin_market_fund_flow 主力净流入 + fin_market_activity 活跃度 + fin_zt_pool 涨停家数)。把指标拆成 趋势/动量/成长/事件 四因子,'
        '按 **3 套可切换策略(趋势跟随/成长质量/热点事件)** 各自权重打分 → 同一份数据不同策略出不同 action(买入/持有/观望/回避);'
        '配了 LLM(env LLM_*)再按各策略侧重提示词产出研判 reason(每股每策略一条),否则规则理由。strategy 字段区分策略,'
        '另产出每市场每策略"综述"(看多广度)。每天07:10生成,末尾按 env(DEMO_PUSH_*,DEMO_PUSH_STRATEGY 选推送策略)推送群机器人。'
        '基本面/新闻仅 A股有(平台无H/US对应索引),H/US 纯技术面。数据分析仅供参考,不构成投资建议。',
    ),
]

# 每日股票分析看板(dash_type=board,声明式):决策表 + 三市场代表股K线均线 + 市场多头广度
STOCK_DASH_ID = 'demo_board_stock'


def _scomp(cid, term_val, ys, title, x, y, w, h, ctype='line'):
    # 按 symbol 精确过滤(symbol.keyword)取单只时序,x=date 升序;ys 各字段一条线
    return {
        'id': cid, 'type': 'chart',
        'inline': {'modelId': 'dm_fin_watch_daily',
                   'native': {'index': 'fin_watch_daily',
                              'body': {'query': {'term': {'symbol.keyword': term_val}}, 'size': 400,
                                       'sort': [{'date': 'asc'}]}},
                   'chartSpec': {'type': ctype, 'x': 'date', 'ys': ys,
                                 'style': {'title': title, 'legend': True, 'smooth': True}}},
        'pos': {'x': x, 'y': y, 'w': w, 'h': h}, 'props': {'title': title}, 'subscribe': True,
    }


_MA_YS = [{'field': 'close', 'agg': 'sum'}, {'field': 'ma20', 'agg': 'sum'}, {'field': 'ma60', 'agg': 'sum'}]
# 顶部策略切换:select 筛选器 → 变量 {{strategy}} 注入决策表/综述图的 native term,改选即重刷(联动)
_STRATEGY_OPTIONS = ['趋势跟随', '成长质量', '热点事件']
STOCK_DASH_FILTERS = [{'name': 'strategy', 'label': '策略', 'type': 'select',
                       'options': _STRATEGY_OPTIONS, 'default': _STRATEGY_OPTIONS[0]}]
STOCK_DASH_COMPONENTS = [
    {'id': 'f1', 'type': 'filter', 'props': {'varName': 'strategy', 'title': '策略切换'},
     'pos': {'x': 0, 'y': 0, 'w': 24, 'h': 1}},
    {'id': 'c1', 'type': 'chart',
     'inline': {'modelId': 'dm_fin_daily_report',
                'native': {'index': 'fin_daily_report',
                           'body': {'query': {'bool': {'must': [{'term': {'strategy.keyword': '{{strategy}}'}}],
                                                       'must_not': [{'term': {'symbol.keyword': '__MARKET__'}}]}},
                                    'size': 200, 'sort': [{'score': 'desc'}]}},
                'chartSpec': {'type': 'table', 'x': 'name',
                              'ys': [{'field': 'market', 'agg': 'none'}, {'field': 'close', 'agg': 'none'},
                                     {'field': 'change_pct', 'agg': 'none'}, {'field': 'action', 'agg': 'none'},
                                     {'field': 'score', 'agg': 'none'}, {'field': 'reason', 'agg': 'none'}],
                              'style': {'title': '决策报告(按所选策略)'}}},
     'pos': {'x': 0, 'y': 1, 'w': 24, 'h': 8}, 'props': {'title': '每日决策报告'}, 'subscribe': True},
    _scomp('c2', 'sh600519', _MA_YS, '贵州茅台 收盘/MA20/MA60(A股)', 0, 9, 12, 7),
    _scomp('c3', '00700', _MA_YS, '腾讯控股 收盘/MA20/MA60(港股)', 12, 9, 12, 7),
    _scomp('c4', 'AAPL', _MA_YS, '苹果 收盘/MA20/MA60(美股)', 0, 15, 12, 7),
    {'id': 'c5', 'type': 'chart',
     'inline': {'modelId': 'dm_fin_daily_report',
                'native': {'index': 'fin_daily_report',
                           'body': {'query': {'bool': {'must': [{'term': {'symbol.keyword': '__MARKET__'}},
                                                                {'term': {'strategy.keyword': '{{strategy}}'}}]}},
                                    'size': 50}},
                'chartSpec': {'type': 'bar', 'x': 'name', 'ys': [{'field': 'score', 'agg': 'sum'}],
                              'style': {'title': '各市场多头广度(%,按所选策略)', 'label': True}}},
     'pos': {'x': 12, 'y': 15, 'w': 12, 'h': 7}, 'props': {'title': '各市场多头广度'}, 'subscribe': True},
]
STOCK_DASH_CANVAS = {'mode': 'matrix', 'cols': 24}

# 每日多市场股票分析助手(AI 应用 9003):对话追问决策报告/指标(对标 DSA 的对话能力)
STOCK_APP_ID = 9003
STOCK_APP_PROMPT = """# 角色
你是「每日多市场股票分析助手」,基于平台每天沉淀的 A股/港股/美股自选股技术指标与决策报告,回答择时/多空/对比问题并出图。定位:技术面数据分析,不构成投资建议。

## 数据(数据源 `demo_es`)
- `fin_watch_daily`:自选股日线+指标 market(A/HK/US)/symbol/name/date/open/high/low/close/volume/amount/ma5/ma10/ma20/ma60/rsi14/macd_dif/macd_dea/macd/kdj_k/kdj_d/kdj_j/change_pct
- `fin_daily_report`:每日**多策略融合**决策报告(技术+基本面+新闻+大盘)date/market/**strategy(趋势跟随/成长质量/热点事件)**/symbol/name/close/change_pct/ma20/ma60/rsi14/macd/kdj_j/**net_profit_yoy(净利同比%,A股)/roe(A股)/news_cnt(新闻条数,A股)**/action(买入/持有/观望/回避)/score(0-100)/reason;symbol='__MARKET__' 为该市场该策略综述(score=看多广度%,A股 reason 附大盘背景)。**同一只股在 3 套策略下各有一行**;基本面/新闻仅 A股有,H/US 为纯技术面
也可用 `akshare_cn` 取最新日线(stock_zh_a_daily 前缀 sh/sz、stock_hk_daily 纯数字、stock_us_daily 代码)。

## 可切换策略(用户问"用X策略"时按 strategy 字段过滤)
- **趋势跟随**:重均线排列+MACD/动量,顺势;**成长质量**:重净利同比/ROE/毛利等基本面;**热点事件**:重新闻催化/涨停资金情绪/短期涨幅。
- 同一份数据不同策略权重 → 不同 action;可对比"同一只股在三套策略下的评分差异"。
- 综合 score≥68 买入、≥55 持有、≥42 观望、否则回避。

## 工作流程
1. get_table_schema 查两个索引字段(文本字段聚合/精确匹配用 .keyword,如 strategy.keyword/market.keyword/symbol.keyword;取时序写足 size)。
2. run_datasource_query 对 demo_es 取数(按 strategy/market/symbol 过滤,date 排序);问到某策略务必加 strategy.keyword 过滤。
3. 沙箱 pandas 计算 + pyecharts 绘图(内联展示);K线叠加均线时 close 与 ma20/ma60 同图。
4. 给出结论 + 图/表。免责:数据分析,非投资建议。
"""
STOCK_APP_CONFIG = {
    'prompt': STOCK_APP_PROMPT,
    'prologue': '你好!我是每日多市场股票分析助手。基于 A股/港股/美股自选股的技术指标与每日决策报告,帮你看多空、比强弱、画K线均线。试试下面的预设问题。',
    'presetQuestions': [
        '用「趋势跟随」策略,今天三大市场哪个多头广度最高?给出各市场综述',
        '同一只贵州茅台,在「趋势跟随/成长质量/热点事件」三套策略下的评分与结论有何差异?',
        '用「成长质量」策略,A股自选股评分 Top5,列出净利同比/ROE 与结论',
        '用「热点事件」策略,近期有新闻催化、评分靠前的个股',
        '贵州茅台最近120日收盘价叠加 MA20/MA60,画K线均线图并点评趋势',
        '腾讯控股 MACD 与 KDJ 当前状态如何?结合评分给出研判',
    ],
    'quickCommands': [
        {'name': '策略对比', 'content': '贵州茅台在趋势跟随/成长质量/热点事件三套策略下的评分与action对比,并说明为何不同'},
        {'name': '趋势选股', 'content': '用「趋势跟随」策略,三大市场评分 Top5 个股,表格展示 market/name/action/score'},
        {'name': '成长选股', 'content': '用「成长质量」策略,A股自选股评分 Top5,附净利同比/ROE'},
        {'name': '事件选股', 'content': '用「热点事件」策略,评分靠前且有新闻催化的个股'},
        {'name': 'K线均线', 'content': '贵州茅台近120日收盘价叠加 MA20/MA60 折线图'},
    ],
    'toolIds': [], 'datasetIds': [], 'datasourceCodes': [ES, AK],
    'enableMemory': False, 'model': {'modelId': 0, 'temperature': None, 'maxTokens': None},
}

# 定时任务联动:APScheduler 从 sys_job 表加载调度(invoke_target=dispatch.run_task, job_args=task_id),
# task.trigger_type=2 + crontab,task.job_id 指向 sys_job。仅插 task 不建 sys_job 不会真触发。
_INVOKE = 'module_task_schedule.dispatch.run_task'

_DS_SQL = text("""INSERT INTO data_source (id,name,code,source_type,family,config,secrets,status,remark,create_by,create_time,tenant_id)
VALUES (:id,:name,:code,:stype,:family,:config,NULL,'ok',:remark,'admin',:now,:tenant)""")
_TASK_SQL = text("""INSERT INTO task (id,template_code,task_type,run_type,name,params,status,built_in,trigger_type,crontab,priority,retry,countdown,run_queue,create_by,create_time,remark,tenant_id)
VALUES (:id,'DataIntegrationTask',1,1,:name,:params,1,0,:trigger,:crontab,1,0,60,'default','admin',:now,:remark,:tenant)""")
_JOB_SQL = text("""INSERT INTO sys_job (job_name,job_group,job_executor,invoke_target,job_args,cron_expression,misfire_policy,concurrent,status,create_by,create_time,tenant_id)
VALUES (:jn,'default','default',:inv,:args,:cron,'2','1','0','admin',:now,:tenant)""")
_MODEL_SQL = text("""INSERT INTO data_model (id,name,code,datasource_code,kind,object_name,auth,status,remark,create_by,create_time,tenant_id)
VALUES (:id,:name,:code,:ds,'index',:obj,'query,extract,api',1,:remark,'admin',:now,:tenant)""")
_APP_SQL = text("""INSERT INTO ai_app (app_id,name,description,app_type,status,config,user_id,create_by,create_time,tenant_id)
VALUES (:id,:name,:desc,:atype,'0',:config,1,'admin',:now,:tenant)""")
# 看板两表法:基础信息 data_dashboard + 画布 data_dashboard_canvas(content={canvas,components,filters})
_DASH_SQL = text("""INSERT INTO data_dashboard (id,name,dash_type,refresh_interval,remark,create_by,create_time,tenant_id)
VALUES (:id,:name,'board',0,:remark,'admin',:now,:tenant)""")
_DASHC_SQL = text("""INSERT INTO data_dashboard_canvas (id,dashboard_id,version,content,create_by,create_time,tenant_id)
VALUES (:id,:did,'current',:content,'admin',:now,:tenant)""")

# 演示指标(语义层):绑定 demo 模型,agent 命中即用 query_metric 取权威一致的数(避开 ES 声明式聚合不可靠)。
# (code, name, caliber, model_id, measure, dimensions, time_field, unit)
_METRICS = [
    ('industry_pe_avg', '行业加权市盈率', '巨潮资讯·证监会行业分类的加权静态市盈率,按行业汇总(pe_weighted 均值)。',
     'dm_fin_industry_pe', '{"agg":"avg","field":"pe_weighted"}', '[{"field":"industry_name","name":"行业"}]', None, '倍'),
    ('market_main_net', '大盘主力净流入', '沪深两市主力资金每日净流入额(元,正=净流入/负=净流出),按日期。',
     'dm_fin_market_fund_flow', '{"agg":"sum","field":"main_net"}', '[{"field":"date","name":"日期"}]', 'date', '元'),
    ('index_close', '指数收盘价', '主要指数(上证/深证/沪深300/创业板)每日收盘价,按指数与日期。',
     'dm_fin_index_daily', '{"agg":"avg","field":"close"}', '[{"field":"name","name":"指数"},{"field":"date","name":"日期"}]', 'date', '点'),
]
_METRIC_SQL = text("""INSERT INTO data_metric (name,code,caliber,model_id,measure,dimensions,time_field,unit,status,built_in,create_by,create_time,tenant_id)
VALUES (:name,:code,:caliber,:model_id,:measure,:dims,:tf,:unit,'0','1','admin',:now,:tenant)""")


def seed_metadata() -> int:
    """幂等写入数据源/任务/数据模型/AI应用。返回任务数。"""
    now = datetime.datetime.now()
    db = get_sync_session_local()()
    try:
        for sid, name, dcode, stype, family, cfg in DATASOURCES:
            db.execute(text('DELETE FROM data_source WHERE id=:id'), {'id': sid})
            db.execute(
                _DS_SQL,
                {
                    'id': sid,
                    'name': name,
                    'code': dcode,
                    'stype': stype,
                    'family': family,
                    'config': json.dumps(cfg),
                    'remark': '演示数据源',
                    'now': now,
                    'tenant': TENANT,
                },
            )
        for tid, name, params, idx, label, cron, desc in TASKS:
            jn = 'TASK_' + tid
            db.execute(text('DELETE FROM task WHERE id=:id'), {'id': tid})
            db.execute(text('DELETE FROM sys_job WHERE job_name=:jn'), {'jn': jn})  # 清旧调度(幂等)
            trigger = 2 if cron else 1  # 1单次 2定时
            db.execute(
                _TASK_SQL,
                {
                    'id': tid,
                    'name': name,
                    'params': params,
                    'trigger': trigger,
                    'crontab': cron,
                    'remark': desc,
                    'now': now,
                    'tenant': TENANT,
                },
            )  # 详细描述入 task.remark
            if cron:  # 建 sys_job 并回填 task.job_id,APScheduler 才会真正按 cron 触发
                r = db.execute(
                    _JOB_SQL, {'jn': jn, 'inv': _INVOKE, 'args': tid, 'cron': cron, 'now': now, 'tenant': TENANT}
                )
                db.execute(text('UPDATE task SET job_id=:jid WHERE id=:tid'), {'jid': r.lastrowid, 'tid': tid})
            dm = 'dm_' + idx
            db.execute(text('DELETE FROM data_model WHERE id=:id'), {'id': dm})
            db.execute(
                _MODEL_SQL,
                {
                    'id': dm,
                    'name': label,
                    'code': idx,
                    'ds': ES,
                    'obj': idx,
                    'remark': desc,
                    'now': now,
                    'tenant': TENANT,
                },
            )  # 数据模型名=label,备注=详细描述
        db.execute(text('DELETE FROM ai_app WHERE app_id=:id'), {'id': APP_ID})
        db.execute(
            _APP_SQL,
            {
                'id': APP_ID,
                'name': '财经数据分析助手',
                'desc': '基于 akshare 沉淀到 ES 的财经数据,对话取数+绘图分析',
                'atype': '数据分析',
                'config': json.dumps(APP_CONFIG, ensure_ascii=False),
                'now': now,
                'tenant': TENANT,
            },
        )
        # 演示多图看板:A股市场总览(先删后插,幂等)
        db.execute(text('DELETE FROM data_dashboard_canvas WHERE dashboard_id=:id'), {'id': DASH_ID})
        db.execute(text('DELETE FROM data_dashboard WHERE id=:id'), {'id': DASH_ID})
        db.execute(_DASH_SQL, {'id': DASH_ID, 'name': 'A股市场总览(Demo)',
                               'remark': '指数日线/行业涨跌幅/概念涨幅/大盘资金流/行业市盈率 多图总览(全部基于 demo 真实数据)',
                               'now': now, 'tenant': TENANT})
        db.execute(_DASHC_SQL, {'id': DASH_ID + '_canvas', 'did': DASH_ID,
                                'content': json.dumps({'canvas': DASH_CANVAS, 'components': DASH_COMPONENTS, 'filters': []}, ensure_ascii=False),
                                'now': now, 'tenant': TENANT})
        # 红利低波专题:AI 应用 + 看板(先删后插,幂等)
        db.execute(text('DELETE FROM ai_app WHERE app_id=:id'), {'id': DIV_APP_ID})
        db.execute(_APP_SQL, {'id': DIV_APP_ID, 'name': '红利低波数据分析助手',
                              'desc': '中证红利低波动指数(H30269)估值/性价比/择时分析,对话取数+绘图',
                              'atype': '数据分析', 'config': json.dumps(DIV_APP_CONFIG, ensure_ascii=False),
                              'now': now, 'tenant': TENANT})
        db.execute(text('DELETE FROM data_dashboard_canvas WHERE dashboard_id=:id'), {'id': DIV_DASH_ID})
        db.execute(text('DELETE FROM data_dashboard WHERE id=:id'), {'id': DIV_DASH_ID})
        db.execute(_DASH_SQL, {'id': DIV_DASH_ID, 'name': '红利低波指数估值/性价比(Demo)',
                               'remark': '指数点位/PE全历史 + 股息率 + 10年国债 + 估值明细,红利低波三重黄金坑监控',
                               'now': now, 'tenant': TENANT})
        db.execute(_DASHC_SQL, {'id': DIV_DASH_ID + '_canvas', 'did': DIV_DASH_ID,
                                'content': json.dumps({'canvas': DIV_DASH_CANVAS, 'components': DIV_DASH_COMPONENTS, 'filters': DIV_DASH_FILTERS}, ensure_ascii=False),
                                'now': now, 'tenant': TENANT})
        # 每日多市场股票分析:AI 应用 9003 + 决策看板(先删后插,幂等)
        db.execute(text('DELETE FROM ai_app WHERE app_id=:id'), {'id': STOCK_APP_ID})
        db.execute(_APP_SQL, {'id': STOCK_APP_ID, 'name': '每日多市场股票分析助手',
                              'desc': 'A股/港股/美股自选股技术指标与每日决策报告,对话取数+绘图',
                              'atype': '数据分析', 'config': json.dumps(STOCK_APP_CONFIG, ensure_ascii=False),
                              'now': now, 'tenant': TENANT})
        db.execute(text('DELETE FROM data_dashboard_canvas WHERE dashboard_id=:id'), {'id': STOCK_DASH_ID})
        db.execute(text('DELETE FROM data_dashboard WHERE id=:id'), {'id': STOCK_DASH_ID})
        db.execute(_DASH_SQL, {'id': STOCK_DASH_ID, 'name': '每日多市场股票分析(Demo)',
                               'remark': '决策报告表 + A股/港股/美股代表股K线均线 + 各市场多头广度(对标 daily_stock_analysis)',
                               'now': now, 'tenant': TENANT})
        db.execute(_DASHC_SQL, {'id': STOCK_DASH_ID + '_canvas', 'did': STOCK_DASH_ID,
                                'content': json.dumps({'canvas': STOCK_DASH_CANVAS, 'components': STOCK_DASH_COMPONENTS, 'filters': STOCK_DASH_FILTERS}, ensure_ascii=False),
                                'now': now, 'tenant': TENANT})
        # 演示指标(语义层,先删后插,幂等)
        for code_, name_, cal_, mid_, meas_, dims_, tf_, unit_ in _METRICS:
            db.execute(text('DELETE FROM data_metric WHERE code=:c'), {'c': code_})
            db.execute(_METRIC_SQL, {'name': name_, 'code': code_, 'caliber': cal_, 'model_id': mid_,
                                     'measure': meas_, 'dims': dims_, 'tf': tf_, 'unit': unit_, 'now': now, 'tenant': TENANT})
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


def _trigger_scheduler_reload() -> bool:
    """通知运行中的后端调度器立即从库重载(无需重启):向 Redis 同步频道 PUBLISH。

    后端 leader 的 _listen_sync_channel 收到后触发 _sync_jobs_from_database(增/删/改差量同步)。
    返回收到消息的订阅者数是否 >0(>0 说明有在监听的调度器)。best-effort,失败不影响播种。
    """
    try:
        import redis

        from config.env import RedisConfig

        r = redis.Redis(
            host=RedisConfig.redis_host,
            port=RedisConfig.redis_port,
            username=RedisConfig.redis_username or None,
            password=RedisConfig.redis_password or None,
            db=RedisConfig.redis_database,
            socket_timeout=5,
        )
        received = r.publish('scheduler:sync:request', 'demo_seed')
        r.close()
        return received > 0
    except Exception as e:
        print(f'触发调度重载失败({e}),可重启后端激活')
        return False


def seed_demo() -> None:
    """整体初始化:播种元数据 + 派发 ETL 到 Celery 填充 ES。幂等(按固定 demo id 先删后插),可重复执行。"""
    n = seed_metadata()
    scheduled = sum(1 for t in TASKS if t[5])
    print(
        f'OK: 数据源 {len(DATASOURCES)} + 任务 {n}(其中定时 {scheduled} 个/单次 {n - scheduled} 个) + 数据模型 {len({t[3] for t in TASKS})} + AI应用 3(财经 {APP_ID}/红利低波 {DIV_APP_ID}/多市场股票 {STOCK_APP_ID}) + 看板 3(市场 {DASH_ID}/红利低波 {DIV_DASH_ID}/多市场股票 {STOCK_DASH_ID}) 已写入'
    )
    m = dispatch_demo_tasks()
    print(f'已派发 {m} 个 ETL 任务到 Celery 立即灌一次 ES(约 2-3 分钟)')
    # 播种改的是 sys_job 表,运行中的调度器需重载才生效。优先 PUBLISH 让其即时重载,兜底提示重启。
    if _trigger_scheduler_reload():
        print('✅ 已通知运行中的后端即时重载定时调度(无需重启)')
    else:
        print('⚠️ 未检测到在监听的调度器,请重启后端激活:docker restart ezdata-backend-my')


if __name__ == '__main__':
    seed_demo()
