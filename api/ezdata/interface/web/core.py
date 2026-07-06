"""核心门面:把 连接目录(store) + ezdata.services + LLM 组装成三件事。

  数据管理:list_source_types / connection_schema / test / list_tables / get_columns
  取数    :query(只读护栏由 services 负责)
  AI 取数 :ask —— NL → (prompts 构造) → LLM → 查询语句 → services.query 执行
  ETL     :run_etl —— 同步 抽取→(转换)→写入,小数据直查直写 / 大数据走 dlt

所有对 ezdata 的调用都经 services 门面,不碰 db/web/celery。
"""

from typing import Any

from ezdata import services
from ezdata.services import prompts
from ezdata.utils.etl_util import json_safe_rows

from .llm import LLMClient, strip_code_fence
from .sources import ConnectionStore


class Core:
    def __init__(self, store: ConnectionStore, llm: LLMClient | None = None):
        self.store = store
        self.llm = llm or LLMClient()

    # ---------- 数据管理:元信息 ----------
    def list_source_types(self) -> list[dict]:
        return services.list_source_types()

    def connection_schema(self, source_type: str) -> dict:
        return services.connection_schema(source_type)

    # ---------- 数据管理:依赖诊断 / 安装 ----------
    def dependency_status(self, source_type: str) -> dict:
        """只读诊断:{source_type, requirements, missing, ready}。"""
        return services.dependency_status(source_type)

    def install_dependencies(self, source_type: str, upgrade: bool = False) -> dict:
        """在当前进程 pip 装该源缺失依赖(带副作用)。"""
        return services.install_dependencies(source_type, upgrade=upgrade)

    # ---------- 数据管理:连接目录 CRUD(委托 store) ----------
    def list_connections(self) -> list[dict]:
        return self.store.list()

    def add_connection(self, name, source_type, config=None, secrets=None) -> dict:
        return self.store.add(name, source_type, config, secrets)

    def update_connection(self, name, **fields) -> dict:
        return self.store.update(name, **fields)

    def remove_connection(self, name) -> bool:
        return self.store.remove(name)

    # ---------- 数据管理:访问 ----------
    def test_connection(self, name: str | None = None, *, source_type=None,
                        config=None, secrets=None) -> dict:
        if name:
            source_type, config, secrets = self.store.resolve(name)
        return services.test_connection(source_type, config, secrets)

    def list_tables(self, name: str) -> list[str]:
        st, cfg, sec = self.store.resolve(name)
        return services.list_tables(st, cfg, sec)

    def get_columns(self, name: str, table: str) -> list[dict]:
        st, cfg, sec = self.store.resolve(name)
        return services.get_columns(st, cfg, sec, table=table)

    def sample_query(self, name: str, table: str) -> dict:
        """该表的原生查询默认示例(前端预填,limit=100)。

        走 handler.sample_query 给出该源合适的原生语法(SQL 出 SELECT,ES/Mongo 等出各自 DSL);
        handler 未实现或抛错则回退到通用 SELECT(SQL 族适用)。对齐平台 DataQueryService.sample_query。
        """
        st, cfg, sec = self.store.resolve(name)
        try:
            native = services.get_handler(st, cfg, sec).sample_query(table, 100)
        except Exception:  # noqa: BLE001  未实现/取样失败:回退通用 SELECT
            native = f'SELECT * FROM {table} LIMIT 100'
        return {'native': native}

    # ---------- 取数 ----------
    def query(self, name: str, statement: Any, limit: int | None = 200) -> list[dict]:
        st, cfg, sec = self.store.resolve(name)
        rows = services.query(st, cfg, sec, statement=statement, limit=limit)
        return json_safe_rows(rows)

    # ---------- 导出 ----------
    @staticmethod
    def export_excel(rows: list[dict]) -> bytes:
        """把查询结果行导出为 xlsx 字节流(pandas + openpyxl)。空结果也产出仅表头/空表。

        清洗孤立代理字符(\\udcxx):某些库/编码会带出无法编码为 UTF-8 的孤立代理,
        pandas(pyarrow 字符串)会报 UnicodeEncodeError,先替换掉再落表。
        """
        import io  # noqa: PLC0415

        import pandas as pd  # noqa: PLC0415

        def _clean(v: Any) -> Any:
            if isinstance(v, str):
                return v.encode('utf-8', 'replace').decode('utf-8')
            return v

        cleaned = [{k: _clean(v) for k, v in r.items()} for r in (rows or [])]
        buf = io.BytesIO()
        pd.DataFrame(cleaned).to_excel(buf, index=False, engine='openpyxl')
        return buf.getvalue()

    # ---------- AI 取数 ----------
    def ask(self, name: str, question: str, tables: list[str] | None = None,
            limit: int | None = 200) -> dict:
        """NL → 查询语句 → 执行。返回 {source_type, family, statement, rows, row_count}。"""
        st, cfg, sec = self.store.resolve(name)
        h = services.get_handler(st, cfg, sec)
        prompt = prompts.build_query_prompt(h, tables, question)
        raw = self.llm.complete(prompt)
        statement = self._parse_statement(strip_code_fence(raw), getattr(h, 'family', ''))
        rows = services.query(st, cfg, sec, statement=statement, limit=limit)
        rows = json_safe_rows(rows)
        return {
            'source_type': st,
            'family': getattr(h, 'family', ''),
            'statement': statement,
            'rows': rows,
            'row_count': len(rows),
        }

    def ask_stream(self, name: str, question: str, tables: list[str] | None = None,
                   limit: int | None = 200):
        """流式 AI 取数:先逐 token 吐生成的查询,再执行并给出结果。

        yield 事件 dict:{event, data}
          meta      -> {source_type, family}
          token     -> 文本增量(生成中的查询语句)
          statement -> 最终解析出的查询(str 或 {func,params})
          result    -> {statement, rows, row_count}
        """
        st, cfg, sec = self.store.resolve(name)
        h = services.get_handler(st, cfg, sec)
        family = getattr(h, 'family', '')
        yield {'event': 'meta', 'data': {'source_type': st, 'family': family}}
        prompt = prompts.build_query_prompt(h, tables, question)
        full = ''
        for delta in self.llm.stream(prompt):
            full += delta
            yield {'event': 'token', 'data': delta}
        statement = self._parse_statement(strip_code_fence(full), family)
        yield {'event': 'statement', 'data': statement}
        rows = json_safe_rows(services.query(st, cfg, sec, statement=statement, limit=limit))
        yield {'event': 'result', 'data': {'statement': statement, 'rows': rows, 'row_count': len(rows)}}

    def gen_query_stream(self, name: str, question: str, tables: list[str] | None = None):
        """流式**仅生成**查询语句(不执行):由用户在前端确认后手动点查询。

        yield 事件 dict:{event, data}
          meta      -> {source_type, family}
          token     -> 文本增量(生成中的查询语句)
          statement -> 最终解析出的查询(str 或 {func,params})
        """
        st, cfg, sec = self.store.resolve(name)
        h = services.get_handler(st, cfg, sec)
        family = getattr(h, 'family', '')
        yield {'event': 'meta', 'data': {'source_type': st, 'family': family}}
        prompt = prompts.build_query_prompt(h, tables, question)
        full = ''
        for delta in self.llm.stream(prompt):
            full += delta
            yield {'event': 'token', 'data': delta}
        yield {'event': 'statement', 'data': self._parse_statement(strip_code_fence(full), family)}

    def install_dependencies_stream(self, source_type: str, upgrade: bool = False):
        """流式安装依赖:逐行吐 pip 输出,最后给出诊断结果。

        yield 事件 dict:{event, data}
          log  -> 一行 pip 输出
          done -> {ok, ready, returncode, missing_after, message}
        """
        import importlib
        import subprocess
        import sys

        before = services.dependency_status(source_type)
        reqs = before.get('requirements') or []
        if not reqs:
            yield {'event': 'done', 'data': {'ok': True, 'ready': True, 'missing_after': [],
                                             'message': '该数据源无 requirements,无需安装'}}
            return
        targets = reqs if upgrade else (before.get('missing') or [])
        if not targets:
            yield {'event': 'done', 'data': {'ok': True, 'ready': True, 'missing_after': [],
                                             'message': '依赖已就绪,无需安装'}}
            return
        cmd = [sys.executable, '-m', 'pip', 'install', *(['-U'] if upgrade else []), *targets]
        yield {'event': 'log', 'data': '$ ' + ' '.join(cmd)}
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,  # noqa: S603
                                text=True, bufsize=1)
        for line in proc.stdout:
            yield {'event': 'log', 'data': line.rstrip('\n')}
        proc.wait()
        importlib.invalidate_caches()   # 让本进程发现刚装进 site-packages 的新驱动
        after = services.dependency_status(source_type)
        ok = proc.returncode == 0 and after.get('ready')
        yield {'event': 'done', 'data': {
            'ok': ok, 'ready': after.get('ready'), 'returncode': proc.returncode,
            'missing_after': after.get('missing') or [],
            'message': '安装完成,依赖已就绪(当前进程已动态生效)' if ok else '安装未完全成功,请看上方日志',
        }}

    @staticmethod
    def _parse_statement(text: str, family: str) -> Any:
        """api 族输出 {func,params} JSON;其余源(SQL/DSL)按文本执行,DSL 也尝试解析为对象。"""
        import json
        t = text.strip()
        if family == 'api' or (t.startswith('{') and t.endswith('}')):
            try:
                return json.loads(t)
            except json.JSONDecodeError:
                return t
        # SQL/文本:去掉模型常带出的结尾分号(否则被 facade 包成子查询时语法错)
        return t.rstrip().rstrip(';').rstrip()

    # ---------- ETL ----------
    # 写入模式 -> pandas.to_sql if_exists
    _SQL_FAMILIES = {'rdbms', 'timeseries'}

    def run_etl(self, source: str, target: str, *, statement: Any, table: str,
                mode: str = 'append', limit: int | None = None, use_dlt: bool = False) -> dict:
        """同步 ETL:源上取数 → 写入目标。

        use_dlt=True:大数据/增量走 dlt(抽取 dlt source → handler.write,数据入 dlt dataset)。
        否则(默认):小数据直查直写。SQL 目标用 pandas.to_sql 直接落顶层表(直观,便于回查);
        非 SQL 目标回退到 handler.write(该源原生写)。
        """
        s_t, s_c, s_s = self.store.resolve(source)
        t_t, t_c, t_s = self.store.resolve(target)
        if use_dlt:
            src = services.get_handler(s_t, s_c, s_s).extract(statement)
            info = services.get_handler(t_t, t_c, t_s).write(src, table, mode=mode)
            return {'mode': 'dlt', 'table': table, 'info': str(info)}

        rows = json_safe_rows(services.query(s_t, s_c, s_s, statement=statement, limit=limit))
        target_h = services.get_handler(t_t, t_c, t_s)
        if getattr(target_h, 'family', '') in self._SQL_FAMILIES and hasattr(target_h, 'engine'):
            import pandas as pd
            if_exists = 'replace' if mode == 'replace' else 'append'
            pd.DataFrame(rows).to_sql(table, target_h.engine, if_exists=if_exists, index=False)
            return {'mode': 'sync', 'target': t_t, 'table': table, 'row_count': len(rows)}
        # 非 SQL 目标:走该源原生写路径
        services.write(t_t, t_c, t_s, records=rows, table=table, mode=mode)
        return {'mode': 'native', 'target': t_t, 'table': table, 'row_count': len(rows)}
