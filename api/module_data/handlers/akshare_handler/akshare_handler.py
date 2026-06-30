"""AKShare handler:中国财经数据接口(akshare 包)。

只读 API 型数据源,免 key、无连接参数。与 SQL/文档库不同,这里:
  - "表"= akshare 的一个数据接口函数名(如 stock_zh_a_hist);
  - 查询的 statement = 函数名(str)或 {'func': 函数名, 'params': {函数参数}}(dict);
  - params = 函数关键字参数;返回 DataFrame → list[dict]。

akshare 函数本身没有 limit 参数,limit 仅对结果行做切片。能力:READ | EXTRACT | SCHEMA。
"""

from typing import Any

from module_data.handlers.akshare_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.base import Capability, Column, Connector, ConnectResult

# 常用接口白名单(给 list_tables / agent 用,避免全量 ~1400 个函数撑爆上下文)。
# 常用接口白名单 —— **全部实测稳定**(2026-06 探测):东财(em)实时/全市场 push2 快照高频必限流
# (RemoteDisconnected),已全部剔除;全市场实时快照用新浪 stock_zh_a_spot,个股/指数历史用新浪日线(取最新一行即最新交易日价)。
# 仅保留 2 个非 push2、实测稳定的东财接口(基金净值/个股新闻,新浪无对应)。value 给 AI 选函数 + 参数。
# 例外:2026-06-29 实测补入 2 个"当日快照"接口(涨停池 stock_zt_pool_em·datacenter / 市场活跃度
# stock_market_activity_legu·乐咕),非 push2、低频抓当天稳定不限流,但均无历史(详见 value 标注)。
# 实时币价不在此(akshare crypto_* 已冻结)→ 用 CCXT 交易所连接器(source_type=ccxt)。
_COMMON_FUNCS: dict[str, str] = {
    # —— A股(新浪)——
    'stock_zh_a_spot': 'A股全市场实时快照(新浪·无参;返回全部A股 代码/名称/最新价/涨跌额/涨跌幅/买卖盘/昨收今开/最高最低/成交量额;比东财 push2(stock_zh_a_spot_em)稳定、不易限流,首选;注:无换手率/市盈率/市值)',
    'stock_zh_a_daily': 'A股历史日线(新浪;symbol 带前缀如 sh600519/sz000001,adjust qfq/hfq/"";取最新一行=最新交易日价)',
    'stock_zh_a_minute': 'A股分时K线(新浪;symbol 如 sh600519,period 1/5/15/30/60 分钟,adjust)',
    # —— 财务(新浪)——
    'stock_financial_analysis_indicator': '财务分析指标(新浪;symbol 如 600519,start_year 如 2020)',
    'stock_financial_report_sina': '三大财报(新浪;stock 如 sh600519,symbol 资产负债表/利润表/现金流量表)',
    # —— 指数(新浪)——
    'stock_zh_index_daily': '指数历史行情(新浪;symbol 如 sh000001 上证/sz399001 深成/sh000300 沪深300)',
    'index_us_stock_sina': '美股指数历史(新浪;symbol 如 .INX 标普500/.DJI 道指/.IXIC 纳指)',
    'index_stock_cons_sina': '指数成分股(新浪;symbol 指数代码如 000300 沪深300/000016 上证50;返回成分股清单+实时价)',
    # —— 港股 / 美股(新浪)——
    'stock_hk_daily': '港股历史行情(新浪;symbol 如 00700腾讯/01810小米,adjust qfq/hfq/"";取最新行=最新价)',
    'stock_us_daily': '美股历史行情(新浪;symbol 如 AAPL/TSLA/NVDA;取最新行=最新价)',
    # —— 基金 ——
    'fund_etf_hist_sina': 'ETF历史行情(新浪;symbol 如 sh510300 沪深300ETF)',
    'fund_etf_category_sina': 'ETF分类列表(新浪;symbol 如 ETF基金;返回全市场 ETF 代码/名称/最新价)',
    'fund_open_fund_info_em': '开放式基金净值(东财·稳;symbol 基金代码如 000001,indicator 单位净值走势/累计净值走势)',
    # —— 债券(新浪)——
    'bond_zh_hs_daily': '沪深债券历史行情(新浪;symbol 如 sh010107)',
    'bond_zh_hs_cov_daily': '可转债历史行情(新浪;symbol 如 sh113527)',
    'bond_cb_profile_sina': '可转债概况(新浪;symbol 如 sh113527;转股价/发行规模/到期日等条款,item-value 两列)',
    'bond_zh_us_rate': '中美国债收益率(datacenter;start_date 如 20240101;中/美各期限到期收益率)',
    'bond_china_yield': '中债国债收益率曲线(datacenter;start_date/end_date;各期限即期收益率)',
    # —— 外汇 / 期货(新浪)——
    'currency_boc_sina': '中行人民币汇率(新浪;symbol 如 美元/欧元/日元,start_date,end_date)',
    'futures_main_sina': '期货主力连续合约历史(新浪;symbol 如 V0聚氯乙烯/RB0螺纹钢,start_date,end_date)',
    'futures_zh_daily_sina': '期货指定合约日线(新浪;symbol 具体合约如 V2501/RB2510)',
    # —— 宏观 ——
    'macro_china_gdp': '中国 GDP(无参)',
    'macro_china_cpi': '中国 CPI(无参)',
    'macro_china_ppi': '中国 PPI(无参)',
    'macro_china_pmi': '中国 PMI(无参)',
    'macro_china_money_supply': '货币供应 M0/M1/M2(无参;数量+同比+环比)',
    'macro_china_new_house_price': '70城新建/二手住宅价格指数(无参;同比/环比/定基)',
    # —— 龙虎榜 / 解禁 / 交易所总貌 ——
    'stock_restricted_release_queue_sina': '个股限售解禁批次(新浪;symbol 如 600519;解禁日期/数量/流通市值)',
    'stock_sse_summary': '上交所市场总貌(无参;主板/科创板 股票数/市值/换手等)',
    # —— 涨停池 / 市场情绪(2026-06-29 实测稳定不限流;均为"当日快照",无历史)——
    'stock_zt_pool_em': '涨停板行情(东财;date 如 20260626,**只有最近一个交易日**有数据,更早日期返回空;不传 date 默认今天、收盘出数前为空;返回 代码/名称/涨跌幅/最新价/成交额/流通市值/封板资金/首末封板时间/炸板次数/连板数/行业)',
    'stock_market_activity_legu': '市场活跃度·涨跌家数(乐咕legu,无参;仅当下快照无历史,item-value 两列:上涨/下跌/涨停/跌停/活跃度等)',
    # —— 新闻 ——
    'stock_news_em': '个股新闻(东财·稳;symbol 如 600519)',
    'stock_info_global_sina': '新浪全球财经快讯(无参;最新 20 条 时间+内容)',
    # —— 工具 ——
    'tool_trade_date_hist_sina': 'A股历史交易日历(新浪,无参;判断某日是否开市/取最近交易日)',
    # ============ 同花顺(THS,实测稳定;注意股票 symbol 多为 6 位代码不带 sh/sz 前缀)============
    # —— 财务(同花顺,结构比新浪更全:按报告期/按单季度)——
    'stock_financial_abstract_ths': '财务主要指标(同花顺;symbol 如 000063,indicator 按报告期/按单季度/按年度)',
    'stock_financial_benefit_ths': '利润表(同花顺;symbol 如 000063,indicator 按报告期/按单季度/按年度)',
    'stock_financial_debt_ths': '资产负债表(同花顺;symbol 如 000063,indicator 按报告期/按单季度/按年度)',
    'stock_financial_cash_ths': '现金流量表(同花顺;symbol 如 000063,indicator 按报告期/按单季度/按年度)',
    # —— 板块(同花顺)——
    'stock_board_industry_name_ths': '行业板块列表(同花顺,无参;板块名称+代码)',
    'stock_board_industry_summary_ths': '行业板块实时一览(同花顺,无参;各板块涨跌幅/成交额/领涨股)',
    'stock_board_industry_index_ths': '行业板块指数历史(同花顺;symbol 行业名如 半导体/元件,start_date,end_date)',
    'stock_board_concept_index_ths': '概念板块指数历史(同花顺;symbol 概念名如 阿里巴巴概念,start_date,end_date)',
    'stock_board_concept_summary_ths': '概念板块时间表(同花顺,无参;概念/驱动事件/龙头股/成分股数)',
    # —— 新股 / 分红 / 盈利预测 / 主营(同花顺)——
    'stock_ipo_ths': '新股申购与中签(同花顺;symbol 全部A股/京市/沪市/深市)',
    'stock_fhps_detail_ths': 'A股分红派息明细(同花顺;symbol 如 603444)',
    'stock_hk_fhpx_detail_ths': '港股分红派息明细(同花顺;symbol 如 0700)',
    'stock_profit_forecast_ths': '机构盈利预测(同花顺;symbol 如 600519,indicator 预测年报每股收益/净利润等)',
    'stock_zyjs_ths': '主营业务介绍(同花顺;symbol 如 000066)',
    # —— 股东 / 高管异动(同花顺)——
    'stock_management_change_ths': '高管持股变动(同花顺;symbol 如 688981)',
    'stock_shareholder_change_ths': '股东持股变动(同花顺;symbol 如 688981)',
    # —— 技术选股(同花顺)——
    'stock_rank_cxg_ths': '技术选股·创新高(同花顺;symbol 创月新高/半年新高/一年新高/历史新高)',
    'stock_rank_lxsz_ths': '技术选股·连续上涨(同花顺,无参;连涨天数/累计涨幅)',
    # —— 基金 / 可转债(同花顺)——
    'fund_info_ths': '基金基本信息(同花顺;symbol 基金代码如 161130)',
    'bond_zh_cov_info_ths': '可转债数据中心(同花顺,无参;全市场可转债 申购/转股/规模)',
    # —— 新闻(同花顺)——
    'stock_info_global_ths': '同花顺全球财经直播(无参;最新 20 条 标题/内容/时间/链接)',
}


class AKShareHandler(Connector):
    name = 'akshare'
    title = 'AKShare 财经数据'
    family = 'api'
    capabilities = Capability.READ | Capability.EXTRACT | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    # ---------- 元信息 ----------
    def test_connection(self) -> ConnectResult:
        """免 key:能 import akshare 即视为可用(不做重量级网络调用)。"""
        try:
            import akshare  # noqa: F401

            return ConnectResult(True, 'akshare 可用')
        except Exception as e:  # noqa: BLE001
            return ConnectResult(False, f'akshare 不可用: {e}')

    def list_tables(self) -> list[str]:
        """返回常用接口函数名(白名单)。"""
        return list(_COMMON_FUNCS.keys())

    def table_labels(self) -> dict[str, str]:
        """函数名 → 中文说明(供 agent 选对函数;data_agent_tools 在无数据模型时回退用)。"""
        return dict(_COMMON_FUNCS)

    def get_columns(self, table: str) -> list[Column]:
        """返回该函数的【调用参数签名】(而非试调取列——多数函数需必填参数且联网慢)。

        agent 据此知道怎么调:`handler.query('<函数名>', {参数})`(带重试),返回 DataFrame 行。
        """
        import inspect

        try:
            import akshare as ak

            fn = getattr(ak, table, None)
            if fn is None:
                return [Column(name='(未知函数)', type='', comment='不在 akshare 中')]
            cols: list[Column] = []
            for pname, p in inspect.signature(fn).parameters.items():
                if pname in ('kwargs', 'args'):
                    continue
                required = p.default is inspect.Parameter.empty
                default = '' if required else repr(p.default)
                cols.append(Column(name=pname, type='参数',
                                   comment=('必填' if required else f'默认 {default}')))
            return cols
        except Exception as e:  # noqa: BLE001
            return [Column(name='(签名不可用)', type='', comment=str(e)[:80])]

    def describe(self, table: str) -> str:
        """返回该 akshare 函数的完整文档(参数可选值 / 返回列 / 示例),给 AI 精准调用。"""
        import inspect

        try:
            import akshare as ak

            fn = getattr(ak, table, None)
            return (inspect.getdoc(fn) or '').strip()[:1800] if fn is not None else ''
        except Exception:  # noqa: BLE001
            return ''

    def sample_query(self, table: str, limit: int = 100) -> dict:
        """ETL/查询表单预填:{'func': 函数名, 'params': {签名默认值}}。"""
        params = {}
        try:
            import inspect

            import akshare as ak

            fn = getattr(ak, table, None)
            if fn is not None:
                for pname, p in inspect.signature(fn).parameters.items():
                    params[pname] = '' if p.default is inspect.Parameter.empty else p.default
        except Exception:  # noqa: BLE001
            pass
        return {'func': table, 'params': params}

    # ---------- 读路径 ----------
    def query(self, statement: Any, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """statement = 函数名(str) 或 {'func'|'method': 名, 'params': {...}}(dict)。

        akshare 函数无 limit 参数,limit 仅对结果行切片。
        """
        import akshare as ak

        if isinstance(statement, dict):
            func_name = statement.get('func') or statement.get('method')
            call_params = statement.get('params') or params or {}
        else:
            func_name = statement
            call_params = params or {}
        if not func_name:
            raise ValueError('akshare 查询需指定函数名(statement 或 statement.func)')

        fn = getattr(ak, str(func_name), None)
        if not callable(fn):
            raise ValueError(f'AKShare 无此接口: {func_name}')

        df = self._call_with_retry(fn, call_params or {})
        if df is None:
            return []
        df = df.fillna('')
        records = df.to_dict('records')
        if limit is not None:
            records = records[: int(limit)]
        return records

    # akshare 内部多数 requests 调用不带超时,源站(尤其东财)挂起时 socket 会永久阻塞,
    # 在 Celery worker 里会卡死整个 fork 槽、阻塞队列。用进程级 socket 默认超时给每次读/连兜底:
    # 单次 socket 操作超过此秒数即抛 timeout(非整体下载上限,大响应仍可分多次读),由下方重试接住。
    _SOCKET_TIMEOUT = 30

    @classmethod
    def _call_with_retry(cls, fn: Any, call_params: dict, attempts: int = 5) -> Any:
        """akshare 后端源站(东财/新浪等)常瞬时断连/挂起,对连接类错误做退避重试,并加 socket 超时防永久 hang。"""
        import socket
        import time

        last = None
        for i in range(attempts):
            prev_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(cls._SOCKET_TIMEOUT)  # 仅影响本次调用内新建的 socket
            try:
                return fn(**call_params)
            except (ConnectionError, TimeoutError) as e:  # requests.ConnectionError / socket.timeout(py3.10=TimeoutError)
                last = e
                time.sleep(1.5 * (i + 1))
            except Exception as e:  # noqa: BLE001  其余(含解析异常)看是否连接/超时类
                msg = str(e).lower()
                if any(k in msg for k in ('connection', 'timeout', 'timed out', 'remotedisconnected', 'aborted', 'reset')):
                    last = e
                    time.sleep(1.5 * (i + 1))
                    continue
                raise
            finally:
                socket.setdefaulttimeout(prev_timeout)  # 还原,避免影响后续 ES 装载等其它 socket
        raise last if last is not None else RuntimeError('akshare 调用失败')

    # ---------- 抽取(dlt 写路径)----------
    def extract(self, table: str, **kwargs: Any) -> Any:
        """返回 dlt resource:table=函数名,kwargs['params']=函数参数。

        当前 ETL 批量路径走 query(extract.native),此方法为完整性/未来长任务保留。
        """
        import dlt

        handler = self
        func_name = table
        call_params = kwargs.get('params') or {}

        @dlt.resource(name=func_name, write_disposition='append')
        def _rows() -> Any:
            yield from handler.query(func_name, call_params)

        return _rows
