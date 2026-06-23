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
_COMMON_FUNCS: dict[str, str] = {
    # —— A股行情 ——
    'stock_zh_a_spot_em': 'A股实时行情(东财)',
    'stock_zh_a_hist': 'A股历史行情(日/周/月,可复权)',
    'stock_zh_a_hist_min_em': 'A股分钟历史行情',
    'stock_bid_ask_em': '个股实时买卖五档',
    'stock_zh_index_spot_em': '指数实时行情',
    'stock_zh_index_daily': '指数历史行情',
    # —— 个股资料/财务 ——
    'stock_individual_info_em': '个股基本信息',
    'stock_financial_abstract': '财务摘要(关键指标)',
    'stock_financial_analysis_indicator': '财务分析指标',
    'stock_zygc_em': '主营构成',
    'stock_news_em': '个股新闻',
    # —— 资金/榜单 ——
    'stock_individual_fund_flow': '个股资金流向',
    'stock_lhb_detail_em': '龙虎榜明细',
    'stock_hsgt_fund_flow_summary_em': '沪深港通资金流',
    # —— 板块/概念 ——
    'stock_board_industry_name_em': '行业板块列表',
    'stock_board_concept_name_em': '概念板块列表',
    'stock_board_industry_cons_em': '行业板块成分股',
    # —— 基金 ——
    'fund_open_fund_info_em': '开放式基金净值',
    'fund_etf_fund_daily_em': 'ETF基金实时行情',
    'fund_etf_hist_em': 'ETF基金历史行情',
    # —— 宏观/其他 ——
    'macro_china_gdp': '中国GDP',
    'macro_china_cpi': '中国CPI',
    'currency_boc_sina': '人民币汇率中间价',
    'bond_zh_hs_daily': '债券历史行情',
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

    def get_columns(self, table: str) -> list[Column]:
        """按默认参数试调一行推断列名;多数函数需必填参数,失败则返回空(容忍)。"""
        try:
            rows = self.query(table, None, limit=1)
        except Exception:  # noqa: BLE001
            return []
        if not rows:
            return []
        return [Column(name=str(k), type=type(v).__name__) for k, v in rows[0].items()]

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
