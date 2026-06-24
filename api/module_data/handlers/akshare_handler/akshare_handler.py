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
# 白名单之外的函数仍可经 query 直接调用。
# 常用接口白名单(实测可用)。标注数据源:新浪/金十 较稳,东财(em)实时/全市场快照在高频时易限流,
# 故能用单标的(新浪)就别用全市场(东财)快照。value 是给 AI 选函数的中文说明。
_COMMON_FUNCS: dict[str, str] = {
    # —— A股 ——
    'stock_zh_a_hist': 'A股历史行情(东财;symbol 如 600519,period daily/weekly/monthly,adjust qfq/hfq/"")',
    'stock_zh_a_daily': 'A股历史行情(新浪·更稳;symbol 带前缀如 sh600519,adjust qfq/hfq)',
    'stock_zh_a_spot_em': 'A股实时行情快照(全市场·东财·较重;按名称/代码过滤目标股)',
    'stock_bid_ask_em': '个股实时五档/最新价(东财;单标的 symbol 如 600519)',
    'stock_individual_info_em': '个股基本信息(东财;symbol 如 600519)',
    'stock_financial_abstract': '财务摘要关键指标(symbol 如 600519)',
    'stock_financial_analysis_indicator': '财务分析指标(symbol,start_year)',
    'stock_individual_fund_flow': '个股资金流向(stock 如 600519,market sh/sz)',
    'stock_news_em': '个股新闻(symbol 如 600519)',
    'stock_lhb_detail_em': '龙虎榜明细(start_date,end_date)',
    'stock_board_industry_name_em': '行业板块列表(无参)',
    'stock_board_concept_name_em': '概念板块列表(无参)',
    'stock_board_industry_cons_em': '行业板块成分股(symbol=板块名)',
    # —— 指数 ——
    'stock_zh_index_daily': '指数历史行情(新浪·更稳;symbol 如 sh000001)',
    'stock_zh_index_spot_em': '指数实时行情(东财;symbol 如 上证系列指数)',
    # —— 港股 ——
    'stock_hk_daily': '港股历史行情(新浪·更稳;symbol 如 00700腾讯/01810小米,adjust qfq/hfq/"")',
    'stock_hk_hist': '港股历史行情(东财;symbol 如 00700,period,adjust)',
    'stock_hk_spot_em': '港股实时行情快照(全市场·东财·较重;按名称/代码过滤,如小米=代码 01810)',
    # —— 美股 ——
    'stock_us_daily': '美股历史行情(新浪·更稳;symbol 如 AAPL/TSLA)',
    'stock_us_hist': '美股历史行情(东财;symbol 如 105.AAPL)',
    'stock_us_spot_em': '美股实时行情快照(全市场·东财·较重)',
    # —— 币圈:akshare 的 crypto_* 接口数据已冻结(2020/2023 旧值),不收录;实时币价用 CCXT 交易所连接器 ——
    # —— 基金 ——
    'fund_open_fund_info_em': '开放式基金净值(symbol 基金代码,indicator 如 单位净值走势)',
    'fund_etf_spot_em': 'ETF 实时行情(全市场·东财)',
    'fund_etf_hist_em': 'ETF 历史行情(symbol,period,adjust)',
    # —— 债券 / 外汇 / 宏观 ——
    'bond_zh_hs_daily': '沪深债券历史行情(新浪·稳;symbol 如 sh010107)',
    'currency_boc_sina': '中行人民币汇率(新浪·稳;symbol 如 美元,start_date,end_date)',
    'macro_china_gdp': '中国 GDP(无参)',
    'macro_china_cpi': '中国 CPI(无参)',
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

    @staticmethod
    def _call_with_retry(fn: Any, call_params: dict, attempts: int = 5) -> Any:
        """akshare 后端源站(东财/新浪等)常瞬时断连,对连接类错误做退避重试。"""
        import time

        last = None
        for i in range(attempts):
            try:
                return fn(**call_params)
            except (ConnectionError, TimeoutError) as e:  # requests.ConnectionError 继承自内置 ConnectionError
                last = e
                time.sleep(1.5 * (i + 1))
            except Exception as e:  # noqa: BLE001  其余(含解析异常)看是否连接类
                msg = str(e).lower()
                if any(k in msg for k in ('connection', 'timeout', 'remotedisconnected', 'aborted', 'reset')):
                    last = e
                    time.sleep(1.5 * (i + 1))
                    continue
                raise
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
