"""CCXT handler:加密货币交易所统一接口(ccxt 包)。

只读 API 型源:公开行情(ticker/K线/订单簿)免 key。与 akshare 同构——
  - "表"= 交易所方法名(fetch_ticker / fetch_ohlcv / ...);
  - statement = 方法名(str)或 {'method': 名, 'params': {...}}(dict);
  - params = 方法参数(symbol 如 'BTC/USDT'、timeframe 如 '1d');返回归一为 list[dict]。

交易所交易对实时,数据为真·实时(不同于已冻结的 akshare crypto_*)。能力:READ | EXTRACT | SCHEMA。
"""

from datetime import datetime, timezone
from typing import Any

from ezdata.handlers.base import Capability, Column, Connector, ConnectResult
from ezdata.handlers.ccxt_handler.connection_args import connection_args, connection_args_example

# 方法白名单 → 中文说明(给 AI 选方法 + 提示参数)
_METHODS: dict[str, str] = {
    'fetch_ticker': '指定交易对实时行情(symbol 如 BTC/USDT;返回 last/bid/ask/high/low/涨跌/成交量)',
    'fetch_ohlcv': '历史 K 线(symbol, timeframe 如 1m/5m/1h/1d, limit 条数;返回 时间/开/高/低/收/量)',
    'fetch_order_book': '订单簿盘口(symbol, limit 档数;bids/asks)',
    'fetch_trades': '最近成交记录(symbol, limit)',
    'load_markets': '全部交易对/市场详情(无参;按 symbol 过滤)',
    'fetch_status': '交易所运行状态(无参)',
}


class CCXTHandler(Connector):
    name = 'ccxt'
    title = 'CCXT 加密货币交易所'
    family = 'api'
    capabilities = Capability.READ | Capability.EXTRACT | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._ex = None

    # ---------- 交易所实例 ----------
    def _exchange(self) -> Any:
        def _make():
            import ccxt

            ex_id = self.arg('exchange', default='okx')
            cls = getattr(ccxt, str(ex_id), None)
            if cls is None:
                raise ValueError(f'未知交易所: {ex_id}(参考 ccxt.exchanges)')
            cfg: dict[str, Any] = {'timeout': 15000, 'enableRateLimit': True}
            for k in ('apiKey', 'secret', 'password'):
                v = self.arg(k)
                if v:
                    cfg[k] = v
            opts = self.arg('options', default={})
            if isinstance(opts, dict):
                cfg.update(opts)
            ex = cls(cfg)
            # ccxt 不读 HTTP_PROXY 环境变量;沙箱只能经 egress 代理出网,显式注入(backend 无此 env 则直连)
            import os

            proxy = (
                os.environ.get('HTTPS_PROXY')
                or os.environ.get('https_proxy')
                or os.environ.get('HTTP_PROXY')
                or os.environ.get('http_proxy')
            )
            if proxy:
                ex.proxies = {'http': proxy, 'https': proxy}  # requests 风格;勿用 httpProxy/httpsProxy(4.x 互斥报错)
            return ex

        return self._lazy('_ex', _make)

    # ---------- 元信息 ----------
    def test_connection(self) -> ConnectResult:
        try:
            import ccxt

            ex = self._exchange()
            return ConnectResult(True, f'ccxt {ccxt.__version__} / {ex.id} 可用')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        return list(_METHODS)

    def table_labels(self) -> dict[str, str]:
        return dict(_METHODS)

    def get_columns(self, table: str) -> list[Column]:
        """返回该方法的【调用参数】(symbol/timeframe/limit 等),据此 handler.query('方法', {参数})。"""
        import inspect

        try:
            fn = getattr(self._exchange(), table, None)
            if fn is None:
                return [Column(name='(未知方法)', type='', comment='不在该交易所')]
            cols: list[Column] = []
            for pname, p in inspect.signature(fn).parameters.items():
                if pname in ('params', 'kwargs', 'args'):
                    continue
                required = p.default is inspect.Parameter.empty
                default = '' if required else repr(p.default)
                cols.append(Column(name=pname, type='参数', comment='必填' if required else f'默认 {default}'))
            return cols or [Column(name='(无参)', type='', comment='')]
        except Exception as e:
            return [Column(name='(签名不可用)', type='', comment=str(e)[:80])]

    def describe(self, table: str) -> str:
        """方法用法说明(symbol 格式 / timeframe 取值)。"""
        base = _METHODS.get(table, '')
        tips = {
            'fetch_ticker': "symbol 形如 'BTC/USDT'、'ETH/USDT';返回字段含 last(最新价)、bid/ask、high/low、percentage(涨跌%)、baseVolume。",
            'fetch_ohlcv': "symbol 如 'BTC/USDT';timeframe ∈ 1m/3m/5m/15m/30m/1h/4h/1d/1w/1M;limit 为返回根数(如 30)。",
            'fetch_order_book': "symbol 如 'BTC/USDT';limit 为盘口档数。",
            'fetch_trades': "symbol 如 'BTC/USDT';limit 为成交条数。",
            'load_markets': '无参;返回所有可交易对(键为 symbol)。',
            'fetch_status': '无参;返回交易所状态。',
        }
        return (base + ('\n' + tips[table] if table in tips else '')).strip()

    # ---------- 读路径 ----------
    @staticmethod
    def _call_with_retry(fn: Any, params: dict, attempts: int = 3) -> Any:
        import time

        last = None
        for i in range(attempts):
            try:
                return fn(**params)
            except Exception as e:
                msg = str(e).lower()
                if any(k in msg for k in ('timeout', 'network', 'connection', 'temporarily', 'rate', 'ddos')):
                    last = e
                    time.sleep(1.0 * (i + 1))
                    continue
                raise
        raise last if last is not None else RuntimeError('ccxt 调用失败')

    def query(self, statement: Any, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """statement = 方法名(str)或 {'method'|'func': 名, 'params': {...}}。symbol 如 'BTC/USDT'。"""
        if isinstance(statement, dict):
            method = statement.get('method') or statement.get('func')
            call_params = statement.get('params') or params or {}
        else:
            method = statement
            call_params = params or {}
        if not method:
            raise ValueError("ccxt 查询需指定方法名(如 'fetch_ticker')")
        ex = self._exchange()
        fn = getattr(ex, str(method), None)
        if not callable(fn):
            raise ValueError(f'交易所 {ex.id} 无此方法: {method}')
        res = self._call_with_retry(fn, dict(call_params or {}))
        return self._normalize(str(method), res, limit)

    @staticmethod
    def _normalize(method: str, res: Any, limit: int | None) -> list[dict]:
        rows: list[dict]
        if method == 'fetch_ohlcv' and isinstance(res, list):
            rows = [
                {
                    'timestamp': r[0],
                    'datetime': datetime.fromtimestamp(r[0] / 1000, tz=timezone.utc).isoformat(),
                    'open': r[1],
                    'high': r[2],
                    'low': r[3],
                    'close': r[4],
                    'volume': r[5],
                }
                for r in res
                if isinstance(r, (list, tuple)) and len(r) >= 6
            ]
        elif method == 'load_markets' and isinstance(res, dict):
            rows = [{'symbol': k, **(v if isinstance(v, dict) else {'value': v})} for k, v in res.items()]
        elif isinstance(res, dict):
            rows = [res]
        elif isinstance(res, list):
            rows = [r if isinstance(r, dict) else {'value': r} for r in res]
        else:
            rows = [{'value': res}]
        return rows[: int(limit)] if limit is not None else rows

    # ---------- 抽取(dlt 写路径)----------
    def extract(self, table: str, **kwargs: Any) -> Any:
        import dlt

        handler, method, call_params = self, table, kwargs.get('params') or {}

        @dlt.resource(name=method, write_disposition='append')
        def _rows() -> Any:
            yield from handler.query(method, call_params)

        return _rows
