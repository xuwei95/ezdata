"""给 AI agent 的代码执行工具:在隔离沙箱里跑 Python(计算 / 数据源取数)。

基于 ezdata 沙箱(无持久凭据、子进程隔离、可超时 kill),替代 agno 自带 PythonTools 的本地 exec。
两个工具:
- run_python_code:跑普通 Python 做计算/数据处理
- run_datasource_query:对指定数据源跑取数代码(沙箱注入 handler)

数据源连接由本工具在 agent 进程内同步查库+解密后,以明文随请求注入沙箱(沙箱本身 env 为空)。
"""

from __future__ import annotations

import json
from typing import Any

from agno.tools import Toolkit

_ROW_CAP = 500  # 表格/图表产物最多回传行数(避免大表撑爆传输;LLM 文本摘要已含总数)
_CHART_ROW_CAP = 5000  # plot_chart 查询取数上限(引导聚合查询,结果通常很小)
# 与 EchartsBuilder / 后端 _normalize_chart_cfg 对齐(此处轻量构造,存看板时后端再规整)
_CHART_TYPES = frozenset({
    'bar', 'bar_stack', 'bar_percent', 'hbar', 'line', 'area', 'line_stack',
    'pie', 'donut', 'rose', 'scatter', 'radar', 'funnel', 'gauge', 'kline',
    'combo', 'waterfall', 'heatmap', 'boxplot', 'treemap', 'sankey', 'kpi', 'table',
})
_CHART_AGGS = frozenset({'sum', 'avg', 'count', 'max', 'min', 'none'})


def _coerce_ys(ys: Any) -> list[dict]:
    """把 LLM 可能传的多种 ys 形态归一为 [{'field','agg'}]:list[dict] / list[str] /
    单个 str / 单个 dict 都兼容(LLM 常直接传列名字符串,旧实现会崩或丢度量)。取不到则占位。"""
    items = ys if isinstance(ys, list) else ([ys] if ys not in (None, '') else [])
    norm = []
    for m in items:
        if isinstance(m, dict) and m.get('field'):
            agg = m.get('agg')
            d = {'field': str(m['field']), 'agg': agg if agg in _CHART_AGGS else 'none'}
            if m.get('mark') in ('bar', 'line'):  # 双轴组合:柱/线
                d['mark'] = m['mark']
            if m.get('axis') in ('left', 'right'):  # 双轴组合:左/右轴
                d['axis'] = m['axis']
            norm.append(d)
        elif isinstance(m, str) and m.strip():
            norm.append({'field': m.strip(), 'agg': 'none'})
    return norm or [{'field': '', 'agg': 'none'}]


def _chart_cfg(chart_type: str, x: str, ys: list | None, series: str, sort: dict | None,
               top_n: int, title: str, ohlc: dict | None = None, link: dict | None = None) -> dict:
    """把 plot_chart 入参组成 EchartsBuilder cfg(schema 与前端一致)。"""
    norm_ys = _coerce_ys(ys)
    s = sort if isinstance(sort, dict) else {}
    ctype = chart_type if chart_type in _CHART_TYPES else 'bar'
    cfg = {
        'type': ctype,
        'x': str(x or ''),
        'ys': norm_ys,
        'series': str(series or ''),
        'sort': {'by': str(s.get('by') or ''), 'dir': 'asc' if s.get('dir') == 'asc' else 'desc'},
        'topN': max(0, int(top_n or 0)),
        'style': {'title': str(title or '')},
    }
    if ctype == 'kline':  # K 线附带 OHLC 四列映射
        o = ohlc if isinstance(ohlc, dict) else {}
        cfg['ohlc'] = {k: str(o.get(k) or '') for k in ('o', 'h', 'l', 'c')}
    if ctype == 'sankey':  # 桑基附带 源/目标/值 三列映射
        lk = link if isinstance(link, dict) else {}
        cfg['link'] = {k: str(lk.get(k) or '') for k in ('source', 'target', 'value')}
    return cfg


class SandboxCodeTools(Toolkit):
    """沙箱代码执行工具集(供 agent 调用)。"""

    def __init__(
        self,
        artifacts: list | None = None,
        allowed_codes: list | None = None,
        enable_datasource: bool = True,
        **kwargs: Any,
    ) -> None:
        # 结构化产物收集器(图表/表格):工具产出时 append,_stream_agent 排空发给前端渲染。
        # 给 LLM 的返回值仍是文本摘要,不污染上下文。
        self.artifacts: list = artifacts if artifacts is not None else []
        # allowed_codes 非空时,取数仅限这些数据源(应用「数据分析」选定的源);None=不限。
        self.allowed_codes = set(allowed_codes) if allowed_codes else None
        # run_python_code 是纯沙箱计算/绘图(不碰数据源),始终可用;
        # run_datasource_query 才是取数能力,enable_datasource=False 时不挂(应用未选数据源)。
        tools = [self.run_python_code]
        if enable_datasource:
            tools.append(self.run_datasource_query)
            tools.append(self.plot_chart)
        super().__init__(name='sandbox_code', tools=tools, **kwargs)

    def _collect(self, res: dict, saveable: dict | None = None) -> None:
        """把沙箱结果里的 html/dataframe 归一成前端可渲染的产物,append 到收集器。

        saveable:数据源取数的图可带上 {mode:'code', datasourceCode, code},供前端「存为看板」时经 LLM 转看板。
        """
        if not (res and res.get('success')):
            return
        result = res.get('result')
        if not (isinstance(result, dict) and 'type' in result and 'value' in result):
            return
        t, val = result['type'], result['value']
        if t == 'html':
            art = {'kind': 'chart', 'html': str(val)}
            if saveable:  # 代码取数产出的图 → 可存看板(存时 convert_code_to_board 转)
                art['saveable'] = saveable
            self.artifacts.append(art)
        elif t == 'dataframe':
            rows = val if isinstance(val, list) else []
            self.artifacts.append({'kind': 'table', 'rows': rows[:_ROW_CAP], 'total': len(rows)})

    def run_python_code(self, code: str, variable_to_return: str | None = None) -> str:
        """运行 Python 代码做计算或数据处理,返回结果。

        可用库:math、json、datetime、re、statistics、pandas、numpy、pyecharts 等;禁止文件/网络/系统访问。
        把结果赋值给变量并用 variable_to_return 指定返回,或直接 print。结果可加工成结构化格式——
        把变量赋为 {type, value} 字典:
          - {'type':'string','value':'结论文本'}              文本结论
          - {'type':'dataframe','value': df}                   表格(df 为 pandas DataFrame,自动转换)
          - {'type':'html','value': chart.render_embed()}      图表(用 pyecharts 绘图)
        也可直接返回数字/字符串/列表。

        :param code: 要执行的 Python 代码
        :param variable_to_return: 要返回其值的变量名(可选)
        :return: 执行结果摘要(结论 / 表格预览 / 图表提示 / 标准输出)
        """
        from module_data import sandbox_client

        try:
            res = sandbox_client.run_python(code, variable_to_return)
        except Exception as e:
            return f'调用沙箱失败: {e}'
        self._collect(res)
        return _format_result(res)

    def run_datasource_query(self, datasource_code: str, code: str, variable_to_return: str = 'result') -> str:
        """对指定数据源运行取数代码,可对数据加工后返回结论 / 表格 / 图表。

        code 中可直接使用预置的 `handler` 对象访问数据源:
            - SQL 源(mysql/pg…):rows = handler.query("SELECT * FROM users LIMIT 10")
            - 非 SQL 源:statement 形态随源而定,**不是 SQL**。如 akshare 财经接口:
              rows = handler.query("stock_hk_spot_em", {})   # 函数名 + 参数 dict,返回 list[dict](带重试)
              先用 get_table_schema 查该源的函数名/参数,再调;勿对 akshare 写 SQL。
        把结果赋值给 result(或用 variable_to_return 指定),可加工成 {type, value}:
          - {'type':'string','value':'共 100 个用户'}                 文本结论
          - {'type':'dataframe','value': pd.DataFrame(rows)}          表格(自动转换)
          - {'type':'html','value': chart.render_embed()}             图表(用 pyecharts 绘图)
        也可直接返回 list/数字/字符串。可用 pandas、numpy、pyecharts 等做加工。

        :param datasource_code: 数据源编码(平台已配置的数据源)
        :param code: 取数 Python 代码,内部可用 handler 对象
        :param variable_to_return: 要返回其值的变量名(默认 result)
        :return: 结果摘要(结论 / 表格预览 / 图表提示)
        """
        from module_data import sandbox_client

        if self.allowed_codes is not None and datasource_code not in self.allowed_codes:
            return f'该应用未授权访问数据源: {datasource_code}(仅可用: {", ".join(self.allowed_codes)})'
        try:
            datasource = _resolve_datasource(datasource_code)
        except Exception as e:
            return f'数据源解析失败: {e}'
        try:
            res = sandbox_client.run_python_data(code, datasource, variable_to_return)
        except Exception as e:
            return f'调用沙箱失败: {e}'
        # 代码取数产出的图带上 code,前端「存为看板」时经 convert_code_to_board 转成可复用看板
        self._collect(res, saveable={'mode': 'code', 'datasourceCode': datasource_code, 'code': code})
        return _format_result(res)

    def plot_chart(
        self,
        datasource_code: str,
        native: Any,
        chart_type: str = 'bar',
        x: str = '',
        ys: list | None = None,
        series: str = '',
        sort: dict | None = None,
        top_n: int = 0,
        title: str = '',
        ohlc: dict | None = None,
        link: dict | None = None,
    ) -> str:
        """按一条只读查询出图,产出可「存为看板」的图表(EchartsBuilder 配置 + 数据)。

        与 run_datasource_query 不同:本工具只跑**单条只读查询** + 声明式图表配置,产出的图用户可一键存为
        可复用看板。**能聚合就在查询里做**(SQL 用 GROUP BY、ES 用 aggs、Mongo 用 $group),对应度量 agg 用 'none'
        直接画;需要复杂多步 pandas 加工时才改用 run_datasource_query(那类图仅展示、不可存)。

        :param datasource_code: 数据源编码(平台已配置)
        :param native: 该源的查询语句——SQL 字符串,或 ES DSL / Mongo pipeline 的 dict(也可传 JSON 字符串)
        :param chart_type: 图表类型 bar/hbar/bar_stack/line/area/pie/donut/rose/scatter/radar/funnel/gauge/kline(K线)/
            combo(双轴组合)/waterfall(瀑布)/heatmap(热力)/boxplot(箱线)/treemap(矩形树图)/sankey(桑基)/kpi
        :param x: 类别/维度列名(kline 填时间列;heatmap 填 X 轴类别列;sankey 不用)
        :param ys: 度量数组,每项 {"field":"列名","agg":"sum|avg|count|max|min|none"};查询已聚合则用 none;
            combo 每项可加 "mark":"bar|line" 与 "axis":"left|right";heatmap/boxplot/treemap/waterfall 只用第一个
        :param series: 分组/拆分列名(可选;heatmap 时它是 Y 轴类别列)
        :param sort: {"by":"" 或 "__x__" 或某度量field,"dir":"desc|asc"}(可选)
        :param top_n: 只取前 N(0=不限)
        :param title: 图表标题
        :param ohlc: 仅 kline 需要,四列映射 {"o":"开盘列","h":"最高列","l":"最低列","c":"收盘列"}
        :param link: 仅 sankey 需要,三列映射 {"source":"源列","target":"目标列","value":"流量值列"}
        :return: 结果摘要(图表展示给用户;LLM 只见此文本)
        """
        from ezdata.utils.etl_util import assert_readonly_sql
        from module_data import sandbox_client

        if self.allowed_codes is not None and datasource_code not in self.allowed_codes:
            return f'该应用未授权访问数据源: {datasource_code}(仅可用: {", ".join(self.allowed_codes)})'
        stmt = native
        if isinstance(stmt, str):
            s = stmt.strip()
            stmt = json.loads(s) if s[:1] in '{[' and _try_json(s) else s  # dict 语句可能以 JSON 串传入
        if isinstance(stmt, str):
            try:
                assert_readonly_sql(stmt, 'rdbms')  # SQL 文本只读护栏;ES/Mongo(dict)天然只读免检
            except Exception as e:
                return f'查询被拦截(仅允许只读查询): {e}'
        try:
            datasource = _resolve_datasource(datasource_code)
        except Exception as e:
            return f'数据源解析失败: {e}'
        code = f'result = handler.query({stmt!r}, None, {_CHART_ROW_CAP})'
        try:
            res = sandbox_client.run_python_data(code, datasource, 'result')
        except Exception as e:
            return f'调用沙箱失败: {e}'
        if not res.get('success'):
            return f'查询失败: {res.get("error") or "未知错误"}'
        rows = res.get('result')
        if isinstance(rows, dict) and 'value' in rows:  # 若被规整成 {type,value}
            rows = rows['value']
        if not isinstance(rows, list):
            rows = []
        cfg = _chart_cfg(chart_type, x, ys, series, sort, top_n, title, ohlc, link)
        self.artifacts.append({
            'kind': 'echart',
            'cfg': cfg,
            'rows': rows[:_ROW_CAP],
            'total': len(rows),
            'saveable': {'datasourceCode': datasource_code, 'native': stmt, 'chartSpec': cfg, 'title': title},
        })
        dims = ', '.join([x] + ([series] if series else [])) or '(无)'
        if cfg['type'] == 'kline':
            o = cfg.get('ohlc') or {}
            ms = f'OHLC({o.get("o", "")}/{o.get("h", "")}/{o.get("l", "")}/{o.get("c", "")})'
        elif cfg['type'] == 'sankey':
            lk = cfg.get('link') or {}
            ms = f'{lk.get("source", "")}→{lk.get("target", "")} (值 {lk.get("value", "")})'
        else:  # 用已归一的 cfg['ys'](dict),别用原始入参 ys(可能是字符串列表,会 .get 崩)
            ms = ', '.join(f'{m.get("agg", "")}({m.get("field", "")})' for m in cfg['ys']) or '(无)'
        return (
            f'已生成图表({chart_type}):维度 {dims},度量 {ms},{len(rows)} 行数据,'
            f'已展示给用户(用户可点「存为看板」保存复用)。'
        )


def _try_json(s: str) -> bool:
    try:
        json.loads(s)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def _resolve_datasource(code: str) -> dict:
    """同步查数据源 + 解密 secrets 为明文 dict(沙箱无凭据,连接随请求注入)。"""
    from module_task_schedule.runners.data_integration_runner import _load_datasource
    from utils.crypto_util import CryptoUtil

    rec = _load_datasource(code)  # {source_type, config, secrets(AES 密文)}
    secrets: dict = {}
    if rec.get('secrets'):
        try:
            secrets = json.loads(CryptoUtil.decrypt(rec['secrets']))
        except Exception:
            secrets = {}
    return {'source_type': rec['source_type'], 'config': rec.get('config') or {}, 'secrets': secrets}


def _preview(v: Any, limit: int = 500) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
    return s[:limit] + '…' if len(s) > limit else s


def _summarize(result: Any) -> str:
    """把结果摘要成给 LLM 的文本:html/大表不全量回传,避免污染上下文。"""
    if result is None:
        return ''
    if isinstance(result, dict) and 'type' in result and 'value' in result:
        t, val = result['type'], result['value']
        if t == 'html':
            return f'已生成图表(html,{len(str(val))} 字符),将展示给用户。'
        if t == 'dataframe':
            rows = val if isinstance(val, list) else []
            cols = ', '.join(map(str, rows[0].keys())) if rows and isinstance(rows[0], dict) else ''
            head = f'数据表格 {len(rows)} 行' + (f',字段: {cols}' if cols else '')
            return f'{head}。前 8 行预览:\n{_preview(rows[:8], 1200)}'
        if t == 'string':
            return f'结论: {val}'
        return f'结果({t}): {_preview(val)}'
    return f'结果: {_preview(result)}'


def _format_result(res: dict) -> str:
    """把沙箱响应拼成给 LLM 的文本(按结果类型摘要)。"""
    if not res.get('success'):
        return f'执行失败: {res.get("error") or "未知错误"}'
    parts: list[str] = [_summarize(res.get('result'))]
    if (res.get('stdout') or '').strip():
        parts.append(f'输出:\n{res["stdout"].rstrip()}')
    return '\n'.join(p for p in parts if p) or '执行成功(无返回值/输出)'
