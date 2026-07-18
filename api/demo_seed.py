"""财经 demo 种子(幂等,自包含):服务启动后手动跑一次即可,平台默认是空项目。

只影响 demo 命名空间(按固定 id 先删后插),不碰用户/权限/其他数据源任务等系统数据:
- seed_metadata():  建数据源(akshare_cn/demo_es) + 28 个 DataIntegrationTask
                    + 28 个 data_model + 1 个 AI 应用 + 1 个多图看板(A股市场总览)。参数化原生 SQL,multiline 代码零转义,可反复执行。
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

C_STOCK_DAILY = """
symbols = {'sh600519':'贵州茅台','sz300750':'宁德时代','sz002594':'比亚迪',
           'sh688981':'中芯国际','sh601318':'中国平安','sz000651':'格力电器'}
result = []
for c, nm in symbols.items():
    rows = handler.query('stock_zh_a_daily', {'symbol': c, 'adjust': 'qfq'})
    for r in rows[-250:]:
        r['symbol'] = c; r['name'] = nm
        result.append(r)
print('stock_daily rows=%d' % len(result))
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
print('完成:%d 只 / %d 行 → fin_stock_daily_all' % (done, total))
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
        'demo_fin_daily',
        '龙头股日线·前复权近250日 → fin_stock_daily',
        code(AK, C_STOCK_DAILY, 'fin_stock_daily', tf({}, ['symbol', 'date'])),
        'fin_stock_daily',
        '个股日线',
        CRON_CLOSE,
        '新浪6只代表性个股(贵州茅台/宁德时代/比亚迪/中芯国际/中国平安/格力电器)前复权日线 OHLCV(字段本就是英文 date/open/high/low/close/volume/amount/turnover,无需中英转换),各取最近250个交易日。收盘后日更,适合K线、均线、个股走势对比。',
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
        '全A股历史日线 → fin_stock_daily_all',
        code_multi([ES, AK], C_ALL_STOCK_DAILY, 'fin_stock_daily_all', tf({}, ['symbol', 'date'])),
        'fin_stock_daily_all',
        '全A股日线',
        '',  # cron 空 → trigger_type=1 单次(手动触发一次,全量沪深约5000只、耗时较长)
        '复用「A股全市场快照」产物 fin_stock_spot(demo_es)作全市场代码源,不重复抓全市场;仅用 akshare(stock_zh_a_daily 前复权)逐只补历史日线,emit 流式装载、md5(symbol+date) 幂等 → ES 索引 fin_stock_daily_all。单次触发,沪深约5000只、耗时较长。',
    ),
]

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
        f'OK: 数据源 {len(DATASOURCES)} + 任务 {n}(其中定时 {scheduled} 个/单次 {n - scheduled} 个) + 数据模型 {n} + AI应用 1(app_id={APP_ID}) 已写入'
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
