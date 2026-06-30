"""财经 demo 种子(幂等,自包含):服务启动后手动跑一次即可,平台默认是空项目。

只影响 demo 命名空间(按固定 id 先删后插),不碰用户/权限/其他数据源任务等系统数据:
- seed_metadata():  建数据源(akshare_cn/demo_es) + 23 个 DataIntegrationTask
                    + 23 个 data_model + 1 个 AI 应用。参数化原生 SQL,multiline 代码零转义,可反复执行。
                    每个索引一份独立中英字段 map(MAP_*)+ tf() 编译 transform;任务带详细 remark;定时按数据节奏分档。
- dispatch_demo_tasks(): 把 23 个任务派发到 Celery(异步),由 worker 取数填充 demo_es 的 fin_* 索引。
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
# tf(MAP) 据此编译出 transform.code(未命中的列原样保留);新浪日线/指数本就是英文,无需 transform。
def tf(mapping: dict) -> str:
    return ('def transform(row):\n'
            '    M = ' + repr(mapping) + '\n'
            '    return {M.get(k, k): v for k, v in row.items()}')


# stock_zh_a_spot(新浪全市场快照,替代东财 push2 的 stock_zh_a_spot_em——新浪更稳;
# 注:新浪快照无 换手率/市盈率/市值 等字段,只有量价基础列)
MAP_SPOT = {
    '代码': 'code', '名称': 'name', '最新价': 'price', '涨跌额': 'change', '涨跌幅': 'change_pct',
    '买入': 'buy', '卖出': 'sell', '昨收': 'pre_close', '今开': 'open', '最高': 'high', '最低': 'low',
    '成交量': 'volume', '成交额': 'amount', '时间戳': 'timestamp',
}
# stock_zt_pool_em(涨停池)
MAP_ZT = {
    '序号': 'seq', '代码': 'code', '名称': 'name', '涨跌幅': 'change_pct', '最新价': 'price', '成交额': 'amount',
    '流通市值': 'float_market_cap', '总市值': 'market_cap', '换手率': 'turnover_rate', '封板资金': 'seal_amount',
    '首次封板时间': 'first_seal_time', '最后封板时间': 'last_seal_time', '炸板次数': 'break_count',
    '涨停统计': 'zt_stat', '连板数': 'boards', '所属行业': 'industry',
}
# stock_board_concept_name_em(概念板块快照)
MAP_CPTBOARD = {
    '排名': 'rank', '板块名称': 'board_name', '板块代码': 'board_code', '最新价': 'price', '涨跌额': 'change',
    '涨跌幅': 'change_pct', '总市值': 'market_cap', '换手率': 'turnover_rate', '上涨家数': 'up_count',
    '下跌家数': 'down_count', '领涨股票': 'lead_stock', '领涨股票-涨跌幅': 'lead_stock_change_pct',
}
# stock_board_industry_summary_ths(行业板块一览)
MAP_INDSUM = {
    '序号': 'seq', '板块': 'board_name', '涨跌幅': 'change_pct', '总成交量': 'total_volume', '总成交额': 'total_amount',
    '净流入': 'net_inflow', '上涨家数': 'up_count', '下跌家数': 'down_count', '均价': 'avg_price',
    '领涨股': 'lead_stock', '领涨股-最新价': 'lead_stock_price', '领涨股-涨跌幅': 'lead_stock_change_pct',
}
# stock_board_concept_summary_ths(概念解析)
MAP_CPTSUM = {
    '日期': 'date', '概念名称': 'concept_name', '驱动事件': 'driver_event', '龙头股': 'leader_stock', '成分股数量': 'cons_count',
}
# stock_rank_cxg_ths(技术选股·创新高)
MAP_CXG = {
    '序号': 'seq', '股票代码': 'code', '股票简称': 'name', '涨跌幅': 'change_pct', '换手率': 'turnover_rate',
    '最新价': 'price', '前期高点': 'prev_high', '前期高点日期': 'prev_high_date',
}
# stock_rank_lxsz_ths(技术选股·连续上涨)
MAP_LXSZ = {
    '序号': 'seq', '股票代码': 'code', '股票简称': 'name', '收盘价': 'close', '最高价': 'high', '最低价': 'low',
    '连涨天数': 'up_days', '连续涨跌幅': 'consec_change_pct', '累计换手率': 'cum_turnover_rate', '所属行业': 'industry',
}
# stock_ipo_ths(新股申购)
MAP_IPO = {
    '股票代码': 'code', '股票简称': 'name', '申购代码': 'subscribe_code', '发行总数（万股）': 'issue_total_wan',
    '网上发行（万股）': 'online_issue_wan', '申购上限（万股）': 'subscribe_limit_wan',
    '顶格申购需配市值（万元）': 'max_subscribe_mktcap_wan', '发行价格': 'issue_price', '发行市盈率': 'issue_pe',
    '行业市盈率': 'industry_pe', '申购日期': 'subscribe_date', '中签率（%）': 'winning_rate_pct', '中签号': 'lucky_number',
    '中签缴款日期': 'payment_date', '上市日期': 'list_date', '打新收益（元）': 'ipo_profit_yuan',
    '首日最高涨幅': 'first_day_max_gain', '连板天数': 'boards_days',
}
# bond_zh_cov_info_ths(可转债)
MAP_CB = {
    '债券代码': 'bond_code', '债券简称': 'bond_name', '申购日期': 'subscribe_date', '申购代码': 'subscribe_code',
    '原股东配售码': 'shareholder_code', '每股获配额': 'per_share_alloc', '计划发行量': 'planned_issue',
    '实际发行量': 'actual_issue', '中签公布日': 'winning_announce_date', '中签号': 'lucky_number',
    '上市日期': 'list_date', '正股代码': 'stock_code', '正股简称': 'stock_name', '转股价格': 'convert_price',
    '到期时间': 'maturity_date', '中签率': 'winning_rate',
}
# index_stock_cons_sina(主要指数成分股,替代东财 concept_cons_em——新浪更稳;列本就多为英文,仅统一少数命名)
# code 内补 index_code/index_name(已英文)。沪深300含 per/pb/mktcap/turnoverratio,上证50等子集可能缺,稀疏正常。
MAP_IDXCONS = {
    'trade': 'price', 'pricechange': 'change', 'changepercent': 'change_pct', 'settlement': 'pre_close',
    'per': 'pe', 'mktcap': 'market_cap', 'nmc': 'float_market_cap', 'turnoverratio': 'turnover_rate',
    'ticktime': 'tick_time',
}
# 宏观:cpi/ppi/pmi/money_supply 四接口列名的并集(本就是多接口汇到一个索引)+ code 内补的 indicator
MAP_MACRO = {
    '月份': 'month', '当月': 'month_val', '当月同比增长': 'month_yoy', '累计': 'cum',
    '全国-当月': 'national_month', '全国-同比增长': 'national_yoy', '全国-环比增长': 'national_mom', '全国-累计': 'national_cum',
    '城市-当月': 'urban_month', '城市-同比增长': 'urban_yoy', '城市-环比增长': 'urban_mom', '城市-累计': 'urban_cum',
    '农村-当月': 'rural_month', '农村-同比增长': 'rural_yoy', '农村-环比增长': 'rural_mom', '农村-累计': 'rural_cum',
    '制造业-指数': 'mfg_index', '制造业-同比增长': 'mfg_yoy', '非制造业-指数': 'nonmfg_index', '非制造业-同比增长': 'nonmfg_yoy',
    '流通中的现金(M0)-数量(亿元)': 'm0_amount_yi', '流通中的现金(M0)-同比增长': 'm0_yoy', '流通中的现金(M0)-环比增长': 'm0_mom',
    '货币(M1)-数量(亿元)': 'm1_amount_yi', '货币(M1)-同比增长': 'm1_yoy', '货币(M1)-环比增长': 'm1_mom',
    '货币和准货币(M2)-数量(亿元)': 'm2_amount_yi', '货币和准货币(M2)-同比增长': 'm2_yoy', '货币和准货币(M2)-环比增长': 'm2_mom',
}
# stock_news_em(个股新闻):code 内补的 query_symbol(已英文)
MAP_NEWS = {
    '关键词': 'keyword', '新闻标题': 'title', '新闻内容': 'content', '发布时间': 'publish_time',
    '文章来源': 'source', '新闻链接': 'url',
}
# stock_market_fund_flow(大盘资金流·时序)
MAP_MKTFLOW = {
    '日期': 'date', '上证-收盘价': 'sh_close', '上证-涨跌幅': 'sh_change_pct',
    '深证-收盘价': 'sz_close', '深证-涨跌幅': 'sz_change_pct',
    '主力净流入-净额': 'main_net', '主力净流入-净占比': 'main_net_pct',
    '超大单净流入-净额': 'xlarge_net', '超大单净流入-净占比': 'xlarge_net_pct',
    '大单净流入-净额': 'large_net', '大单净流入-净占比': 'large_net_pct',
    '中单净流入-净额': 'mid_net', '中单净流入-净占比': 'mid_net_pct',
    '小单净流入-净额': 'small_net', '小单净流入-净占比': 'small_net_pct',
}
# stock_lhb_detail_em(龙虎榜明细)
MAP_LHB = {
    '序号': 'seq', '代码': 'code', '名称': 'name', '上榜日': 'list_date', '解读': 'interpret',
    '收盘价': 'close', '涨跌幅': 'change_pct', '龙虎榜净买额': 'lhb_net_buy', '龙虎榜买入额': 'lhb_buy',
    '龙虎榜卖出额': 'lhb_sell', '龙虎榜成交额': 'lhb_amount', '市场总成交额': 'market_amount',
    '净买额占总成交比': 'net_buy_pct', '成交额占总成交比': 'amount_pct', '换手率': 'turnover_rate',
    '流通市值': 'float_market_cap', '上榜原因': 'reason',
    '上榜后1日': 'after_1d', '上榜后2日': 'after_2d', '上榜后5日': 'after_5d', '上榜后10日': 'after_10d',
}
# stock_yjbb_em(业绩报表):code 内补的 report_period(已英文)
MAP_YJBB = {
    '序号': 'seq', '股票代码': 'code', '股票简称': 'name', '每股收益': 'eps',
    '营业总收入-营业总收入': 'revenue', '营业总收入-同比增长': 'revenue_yoy', '营业总收入-季度环比增长': 'revenue_qoq',
    '净利润-净利润': 'net_profit', '净利润-同比增长': 'net_profit_yoy', '净利润-季度环比增长': 'net_profit_qoq',
    '每股净资产': 'bps', '净资产收益率': 'roe', '每股经营现金流量': 'ocfps', '销售毛利率': 'gross_margin',
    '所处行业': 'industry', '最新公告日期': 'announce_date',
}
# stock_industry_pe_ratio_cninfo(行业市盈率·证监会分类)
MAP_INDPE = {
    '变动日期': 'date', '行业分类': 'industry_class', '行业层级': 'industry_level', '行业编码': 'industry_code',
    '行业名称': 'industry_name', '公司数量': 'company_count', '纳入计算公司数量': 'calc_company_count',
    '总市值-静态': 'market_cap_static', '净利润-静态': 'net_profit_static',
    '静态市盈率-加权平均': 'pe_weighted', '静态市盈率-中位数': 'pe_median', '静态市盈率-算术平均': 'pe_mean',
}
# stock_margin_sse(上交所融资融券·时序)
MAP_MARGIN = {
    '信用交易日期': 'date', '融资余额': 'margin_balance', '融资买入额': 'margin_buy',
    '融券余量': 'short_volume', '融券余量金额': 'short_amount', '融券卖出量': 'short_sell',
    '融资融券余额': 'total_balance',
}
# fund_etf_spot_em(ETF 实时快照)
MAP_ETF = {
    '代码': 'code', '名称': 'name', '最新价': 'price', 'IOPV实时估值': 'iopv', '基金折价率': 'discount_rate',
    '涨跌额': 'change', '涨跌幅': 'change_pct', '成交量': 'volume', '成交额': 'amount', '开盘价': 'open',
    '最高价': 'high', '最低价': 'low', '昨收': 'pre_close', '振幅': 'amplitude', '换手率': 'turnover_rate',
    '量比': 'volume_ratio', '委比': 'commission_ratio', '外盘': 'outer_volume', '内盘': 'inner_volume',
    '主力净流入-净额': 'main_net', '主力净流入-净占比': 'main_net_pct',
    '超大单净流入-净额': 'xlarge_net', '超大单净流入-净占比': 'xlarge_net_pct',
    '大单净流入-净额': 'large_net', '大单净流入-净占比': 'large_net_pct',
    '中单净流入-净额': 'mid_net', '中单净流入-净占比': 'mid_net_pct',
    '小单净流入-净额': 'small_net', '小单净流入-净占比': 'small_net_pct',
    '现手': 'current_hand', '买一': 'bid1', '卖一': 'ask1', '最新份额': 'latest_shares',
    '流通市值': 'float_market_cap', '总市值': 'market_cap', '数据日期': 'data_date', '更新时间': 'update_time',
}
# macro_china_gdp(中国 GDP·季度)
MAP_GDP = {
    '季度': 'quarter', '国内生产总值-绝对值': 'gdp_abs', '国内生产总值-同比增长': 'gdp_yoy',
    '第一产业-绝对值': 'primary_abs', '第一产业-同比增长': 'primary_yoy',
    '第二产业-绝对值': 'secondary_abs', '第二产业-同比增长': 'secondary_yoy',
    '第三产业-绝对值': 'tertiary_abs', '第三产业-同比增长': 'tertiary_yoy',
}
# macro_china_lpr(LPR 利率·时序;原列名为英文大写,统一成小写下划线)
MAP_LPR = {
    'TRADE_DATE': 'trade_date', 'LPR1Y': 'lpr_1y', 'LPR5Y': 'lpr_5y', 'RATE_1': 'rate_1', 'RATE_2': 'rate_2',
}


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


def code(ds: str, src: str, idx: str, transform: str = '') -> str:
    return json.dumps({
        'extract': {'mode': 'code', 'datasource_codes': [ds], 'code': src},
        'transform': {'enabled': bool(transform), 'code': transform},
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
print('stock_daily rows=%d' % len(result))
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

# 定时策略:按各数据的真实更新节奏分档。cron 为 6 段 Quartz:秒 分 时 日 月 周;日/周用 ? 占位。
# 注意:该 cron 适配器对"星期范围"有坑(会被当成 week-of-year),故只用"每天/每月某日"形态,不用星期。
CRON_CLOSE = '0 0 16 * * ?'    # 收盘日更 16:00(全市场快照/涨停/板块/日线/资金流/ETF)
CRON_EVENING = '0 30 18 * * ?'  # 盘后晚间 18:30(龙虎榜、两融——交易所/东财收盘后才发布)
CRON_DAWN = '0 30 0 * * ?'     # 凌晨日更 00:30(概念成分/解析/技术选股/业绩/行业估值/新股/可转债)
CRON_HOUR = '0 0 * * * ?'      # 每小时(新闻,时效性强)
CRON_MONTH = '0 0 2 1 * ?'     # 每月1号 02:00(宏观月度/季度:CPI·PPI·PMI·货币/GDP/LPR)

# (task_id, 任务名, params_json, 索引, 数据模型名, cron, 详细描述)  cron='' 即单次手动(trigger_type=1)
# 任务名简明带"→索引";详细描述写清:数据源/字段/更新节奏/适合的分析。data_model 名用"数据模型名"。
TASKS = [
    ('demo_fin_spot', 'A股全市场实时快照 → fin_stock_spot',
     native('stock_zh_a_spot', None, 'fin_stock_spot', tf(MAP_SPOT)), 'fin_stock_spot', 'A股全市场快照', CRON_CLOSE,
     '新浪全A股截面行情(改用新浪,替代东财 push2 以提升稳定性):代码/名称/最新价/涨跌额/涨跌幅/买卖盘/昨收今开/最高最低/成交量额。每交易日收盘后(16:00)全量刷新,适合涨跌幅榜、量价分布分析。注:新浪快照不含换手率/市盈率/市值。'),
    ('demo_fin_zt', '涨停板池(当日)→ fin_zt_pool',
     native('stock_zt_pool_em', None, 'fin_zt_pool', tf(MAP_ZT)), 'fin_zt_pool', '当日涨停池', CRON_CLOSE,
     '东财当日涨停个股:封板资金/首次与最后封板时间/炸板次数/涨停统计/连板数/所属行业。收盘后(16:00)日更,适合按行业统计涨停家数、连板梯队、封板强度分析。'),
    ('demo_fin_act', '市场活跃度情绪 → fin_market_activity',
     native('stock_market_activity_legu', None, 'fin_market_activity', TF_STR_VALUE), 'fin_market_activity', '市场活跃度', CRON_CLOSE,
     '乐咕乐股市场情绪快照:上涨/下跌/平盘/涨停/跌停/真跌停/活跃度等家数统计,以 item(指标名)+value(值,统一转字符串避免ES类型冲突)键值对存储。收盘后日更,适合做多空力量、市场温度概览。'),
    ('demo_fin_cptboard', '概念板块行情快照 → fin_concept_board',
     native('stock_board_concept_name_em', None, 'fin_concept_board', tf(MAP_CPTBOARD)), 'fin_concept_board', '概念板块行情', CRON_CLOSE,
     '东财全部概念板块:排名/板块名称/板块代码/最新价/涨跌额/涨跌幅/总市值/换手率/上涨下跌家数/领涨股票及其涨跌幅。收盘后日更,适合概念热度排行、强势板块筛选。'),
    ('demo_fin_indsum', '行业板块一览 → fin_industry_summary',
     native('stock_board_industry_summary_ths', None, 'fin_industry_summary', tf(MAP_INDSUM)), 'fin_industry_summary', '行业板块一览', CRON_CLOSE,
     '同花顺行业板块汇总:涨跌幅/总成交量/总成交额/净流入/上涨下跌家数/均价/领涨股及其最新价与涨跌幅。收盘后日更,适合行业轮动、资金净流入排行。'),
    ('demo_fin_cptsum', '概念板块解析(驱动/龙头)→ fin_concept_summary',
     native('stock_board_concept_summary_ths', None, 'fin_concept_summary', tf(MAP_CPTSUM)), 'fin_concept_summary', '概念解析', CRON_DAWN,
     '同花顺概念解析:日期/概念名称/驱动事件/龙头股/成分股数量。概念定义变动不频繁,凌晨(00:30)日更,适合解读概念逻辑、定位龙头与成分股规模。'),
    ('demo_fin_cxg', '技术选股·创月新高 → fin_cxg',
     native('stock_rank_cxg_ths', {'symbol': '创月新高'}, 'fin_cxg', tf(MAP_CXG)), 'fin_cxg', '技术选股·创新高', CRON_DAWN,
     '同花顺技术形态选股(创月新高):股票代码/简称/涨跌幅/换手率/最新价/前期高点及其日期。凌晨日更,适合强势突破股票池。'),
    ('demo_fin_lxsz', '技术选股·连续上涨 → fin_lxsz',
     native('stock_rank_lxsz_ths', None, 'fin_lxsz', tf(MAP_LXSZ)), 'fin_lxsz', '技术选股·连续上涨', CRON_DAWN,
     '同花顺连续上涨个股:股票代码/简称/收盘价/最高价/最低价/连涨天数/连续涨跌幅/累计换手率/所属行业。凌晨日更,适合动量与连涨梯队分析。'),
    ('demo_fin_ipo', '新股申购与中签 → fin_ipo',
     native('stock_ipo_ths', {'symbol': '全部A股'}, 'fin_ipo', tf(MAP_IPO)), 'fin_ipo', '新股申购', CRON_DAWN,
     '同花顺新股申购:申购代码/发行总数与网上发行量/申购上限/顶格申购需配市值/发行价格/发行与行业市盈率/申购日/中签率/中签号/缴款日/上市日/打新收益/首日最高涨幅/连板天数。凌晨日更以跟进新发。'),
    ('demo_fin_cb', '可转债申购信息 → fin_cb',
     native('bond_zh_cov_info_ths', None, 'fin_cb', tf(MAP_CB)), 'fin_cb', '可转债申购', CRON_DAWN,
     '同花顺可转债信息中心:债券代码与简称/申购日与申购代码/原股东配售码/每股获配额/计划与实际发行量/中签公布日/中签号/上市日/正股代码与简称/转股价格/到期时间/中签率。凌晨日更。'),
    ('demo_fin_daily', '龙头股日线·前复权近250日 → fin_stock_daily',
     code(AK, C_STOCK_DAILY, 'fin_stock_daily'), 'fin_stock_daily', '个股日线', CRON_CLOSE,
     '新浪6只代表性个股(贵州茅台/宁德时代/比亚迪/中芯国际/中国平安/格力电器)前复权日线 OHLCV(字段本就是英文 date/open/high/low/close/volume/amount/turnover,无需中英转换),各取最近250个交易日。收盘后日更,适合K线、均线、个股走势对比。'),
    ('demo_fin_index', '主要指数日线·近250日 → fin_index_daily',
     code(AK, C_INDEX_DAILY, 'fin_index_daily'), 'fin_index_daily', '指数日线', CRON_CLOSE,
     '新浪四大指数(上证指数/深证成指/沪深300/创业板指)日线 OHLCV(英文字段,无需转换),各取最近250个交易日。收盘后日更,适合大盘走势、指数对比。'),
    ('demo_fin_idxcons', '主要指数成分股 → fin_index_cons',
     code(AK, C_INDEX_CONS, 'fin_index_cons', tf(MAP_IDXCONS)), 'fin_index_cons', '指数成分股', CRON_DAWN,
     '新浪主要指数成分股(沪深300/上证50/中证500;替代东财 concept_cons 以提升稳定性):个股代码/名称/最新价/涨跌幅/成交量额/市盈率/市净率/市值/换手率,附 index_code/index_name 归属。凌晨日更,适合"指数→成分股"下钻、成分股权重股分析。'),
    ('demo_fin_macro', '宏观经济·CPI/PPI/PMI/货币供应 → fin_macro',
     code(AK, C_MACRO, 'fin_macro', tf(MAP_MACRO)), 'fin_macro', '宏观经济', CRON_MONTH,
     '国家统计局/央行月度宏观:CPI(全国/城市/农村当月与同环比累计)、PPI、PMI(制造业/非制造业)、货币供应(M0/M1/M2 数量与同环比),按 indicator 字段区分来源。月度数据,每月1号(02:00)刷新。'),
    ('demo_fin_news', '个股新闻资讯 → fin_news',
     code(AK, C_NEWS, 'fin_news', tf(MAP_NEWS)), 'fin_news', '个股新闻', CRON_HOUR,
     '东财个股新闻(贵州茅台/宁德时代/格力电器):关键词/标题/内容/发布时间/来源/链接,附 query_symbol。时效性强,每小时刷新,适合舆情、事件跟踪。'),
    # —— 新增数据集(2026-06-30):资金面/基本面/估值/杠杆/宏观补充 ——
    ('demo_fin_mktflow', '大盘资金流向·近120日时序 → fin_market_fund_flow',
     native('stock_market_fund_flow', None, 'fin_market_fund_flow', tf(MAP_MKTFLOW)), 'fin_market_fund_flow', '大盘资金流', CRON_CLOSE,
     '东财沪深大盘资金流时序(约近120日):主力/超大单/大单/中单/小单净流入的净额与净占比,并含上证、深证收盘价与涨跌幅。收盘后日更,适合主力资金趋势折线、各级别资金对比堆叠图、资金与指数联动。'),
    ('demo_fin_lhb', '龙虎榜明细·近30日 → fin_lhb',
     code(AK, C_LHB, 'fin_lhb', tf(MAP_LHB)), 'fin_lhb', '龙虎榜', CRON_EVENING,
     '东财龙虎榜近30日明细:代码/名称/上榜日/解读/收盘价涨跌幅/龙虎榜净买入卖出与成交额/市场总成交额/净买额与成交额占比/换手率/流通市值/上榜原因/上榜后1·2·5·10日涨幅。龙虎榜收盘后发布,18:30 晚间日更,适合游资动向、上榜原因分布、上榜后表现统计。'),
    ('demo_fin_yjbb', '业绩报表·最近报告期 → fin_yjbb',
     code(AK, C_YJBB, 'fin_yjbb', tf(MAP_YJBB)), 'fin_yjbb', '业绩报表', CRON_DAWN,
     '东财全A股最近已披露报告期业绩(自动回溯季度末):EPS/营业总收入及同比环比/净利润及同比环比/每股净资产/净资产收益率ROE/每股经营现金流/销售毛利率/所处行业,附 report_period。财报季滚动更新,凌晨日更,适合成长性(净利同比)、盈利能力(ROE/毛利)、行业对比。'),
    ('demo_fin_indpe', '行业市盈率估值·证监会分类 → fin_industry_pe',
     code(AK, C_INDPE, 'fin_industry_pe', tf(MAP_INDPE)), 'fin_industry_pe', '行业市盈率', CRON_DAWN,
     '巨潮资讯证监会行业分类静态市盈率(自动回溯最近交易日):行业名称与编码/公司数量/纳入计算公司数/静态总市值与净利润/静态市盈率的加权平均·中位数·算术平均。凌晨日更,适合行业估值横向对比、高低估筛选。'),
    ('demo_fin_margin', '融资融券余额·上交所近180日 → fin_margin',
     code(AK, C_MARGIN, 'fin_margin', tf(MAP_MARGIN)), 'fin_margin', '融资融券', CRON_EVENING,
     '上交所两融时序(约近180日):信用交易日期/融资余额/融资买入额/融券余量及金额/融券卖出量/融资融券总余额。交易所收盘后发布,18:30 晚间日更,适合杠杆资金趋势、市场情绪与风险偏好分析。'),
    ('demo_fin_etf', 'ETF 基金实时快照 → fin_etf',
     native('fund_etf_spot_em', None, 'fin_etf', tf(MAP_ETF)), 'fin_etf', 'ETF快照', CRON_CLOSE,
     '东财全市场ETF行情:最新价/IOPV实时估值/基金折价率/涨跌幅/成交量额/开高低昨收/振幅/换手率/量比委比/内外盘/各级别资金净流入/最新份额/流通与总市值/数据日期。收盘后日更,适合ETF涨幅榜、折溢价、资金流分析。'),
    ('demo_fin_gdp', '中国GDP·季度 → fin_gdp',
     native('macro_china_gdp', None, 'fin_gdp', tf(MAP_GDP)), 'fin_gdp', '中国GDP', CRON_MONTH,
     '国家统计局季度GDP:国内生产总值绝对值与同比增长,以及第一/第二/第三产业的绝对值与同比。季度数据,每月1号刷新,适合经济增长趋势、产业结构分析。'),
    ('demo_fin_lpr', 'LPR贷款市场报价利率·时序 → fin_lpr',
     native('macro_china_lpr', None, 'fin_lpr', tf(MAP_LPR)), 'fin_lpr', 'LPR利率', CRON_MONTH,
     '央行LPR利率时序:1年期(lpr_1y)与5年期(lpr_5y)贷款市场报价利率及历史利率(原英文大写列已统一为小写下划线)。每月20号公布,每月1号刷新,适合利率走势、货币政策跟踪。'),
]

# 数据源(自包含:不依赖 ezdata.sql 的 demo 段)。(id, name, code, source_type, family, config_dict)
DATASOURCES = [
    ('seed-akshare-cn', 'AKShare 财经数据', AK, 'akshare', 'api', {}),
    ('seed-demo-es', '演示-Elasticsearch', ES, 'elasticsearch', 'search',
     {'hosts': 'http://ezdata-es:9200', 'user': 'elastic', 'password': 'ezdata123456'}),
]

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


def seed_metadata() -> int:
    """幂等写入数据源/任务/数据模型/AI应用。返回任务数。"""
    now = datetime.datetime.now()
    db = get_sync_session_local()()
    try:
        for sid, name, dcode, stype, family, cfg in DATASOURCES:
            db.execute(text('DELETE FROM data_source WHERE id=:id'), {'id': sid})
            db.execute(_DS_SQL, {'id': sid, 'name': name, 'code': dcode, 'stype': stype, 'family': family,
                                 'config': json.dumps(cfg), 'remark': '演示数据源', 'now': now, 'tenant': TENANT})
        for tid, name, params, idx, label, cron, desc in TASKS:
            jn = 'TASK_' + tid
            db.execute(text('DELETE FROM task WHERE id=:id'), {'id': tid})
            db.execute(text('DELETE FROM sys_job WHERE job_name=:jn'), {'jn': jn})  # 清旧调度(幂等)
            trigger = 2 if cron else 1  # 1单次 2定时
            db.execute(_TASK_SQL, {'id': tid, 'name': name, 'params': params, 'trigger': trigger,
                                   'crontab': cron, 'remark': desc, 'now': now, 'tenant': TENANT})  # 详细描述入 task.remark
            if cron:  # 建 sys_job 并回填 task.job_id,APScheduler 才会真正按 cron 触发
                r = db.execute(_JOB_SQL, {'jn': jn, 'inv': _INVOKE, 'args': tid, 'cron': cron, 'now': now, 'tenant': TENANT})
                db.execute(text('UPDATE task SET job_id=:jid WHERE id=:tid'), {'jid': r.lastrowid, 'tid': tid})
            dm = 'dm_' + idx
            db.execute(text('DELETE FROM data_model WHERE id=:id'), {'id': dm})
            db.execute(_MODEL_SQL, {'id': dm, 'name': label, 'code': idx, 'ds': ES, 'obj': idx,
                                    'remark': desc, 'now': now, 'tenant': TENANT})  # 数据模型名=label,备注=详细描述
        db.execute(text('DELETE FROM ai_app WHERE app_id=:id'), {'id': APP_ID})
        db.execute(_APP_SQL, {'id': APP_ID, 'name': '财经数据分析助手',
                              'desc': '基于 akshare 沉淀到 ES 的财经数据,对话取数+绘图分析', 'atype': '数据分析',
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
    scheduled = sum(1 for t in TASKS if t[5])
    print(f'OK: 数据源 {len(DATASOURCES)} + 任务 {n}(其中定时 {scheduled} 个/单次 {n - scheduled} 个) + 数据模型 {n} + AI应用 1(app_id={APP_ID}) 已写入')
    m = dispatch_demo_tasks()
    print(f'已派发 {m} 个 ETL 任务到 Celery 立即灌一次 ES(约 2-3 分钟)')
    print('定时调度需重启后端激活:docker restart ezdata-backend-my(启动时 init_system_scheduler 读 sys_job)')


if __name__ == '__main__':
    seed_demo()
