"""
数据集成(ETL)任务执行器

把 module_data 的连接器层接入任务调度:抽取 -> (可选)转换 -> 装载。

两种抽取形态(同一个任务,按源能力自动判定):
- 批量源(READ,如 mysql):执行 extract.native 原生查询取数,一次性装载。
- 流式源(STREAM,如 binlog/kafka):
    - extract.max_events 有值 → 有界读取这一批后装载(可跑通、可调度);
    - extract.max_events 为空/0 → 长驻阻塞消费,微批(batch_size)持续装载(任务 hang 住,直到被终止)。

params(由前端内置组件 DataIntegrationTask 生成):
{
  "extract": {
    "datasource_code": "demo_mysql",
    "native": "SELECT * FROM orders WHERE ...",  # 批量源
    "object": "orders",                          # 批量:参考;流式:表/主题过滤
    "max_events": 100,                           # 流式:有界条数(空=持续消费)
    "batch_size": 100                            # 流式持续消费时的微批大小
  },
  "transform": { "enabled": false, "code": "def transform(row):\n    return row" },
  "load": { "datasource_code": "dwh_mysql", "table": "orders_copy", "mode": "append", "dataset": "public" }
}
源须具 READ 或 STREAM;目标须具 WRITE。
"""

import os
import re
from typing import Any

from sqlalchemy import select

from module_task_schedule.runners.base import BaseRunner, register_runner

# dlt 默认对 normalize/load 开进程池;Celery prefork 的 worker 是 daemon 进程,
# 不允许再 fork 子进程,会导致 pipeline.run 卡死。强制单 worker → 全程在本进程内同步执行。
os.environ.setdefault('EXTRACT__WORKERS', '1')
os.environ.setdefault('NORMALIZE__WORKERS', '1')
os.environ.setdefault('LOAD__WORKERS', '1')
# dlt 默认 snake_case 命名会 strip 掉非 ASCII(中文)列名 → 多列塌缩冲突、数据丢失。
# 用 direct 命名保留原始列名(中文源/akshare 等),MySQL/PG 的 utf8 标识符可承载。
os.environ.setdefault('SCHEMA__NAMING', 'direct')


def _load_datasource(code: str) -> Any:
    """同步会话按编码加载数据源记录(worker 无请求上下文)。"""
    from module_data.entity.do.data_do import DataSource
    from module_task_schedule.sync_db import get_sync_session_local

    db = get_sync_session_local()()
    try:
        ds = db.execute(select(DataSource).where(DataSource.code == code)).scalars().first()
        if ds is None:
            raise ValueError(f'数据源不存在: code={code}')
        # 在会话内取出需要的字段,避免会话关闭后惰性加载
        return {'source_type': ds.source_type, 'config': ds.config or {}, 'secrets': ds.secrets}
    finally:
        db.close()


def _build_handler(rec: dict) -> Any:
    from ezdata.handlers import create_handler

    # 经 create_handler 走进程内实例缓存(worker 跨任务复用连接池);
    # secrets 为密文串(查库)→ from_record 内部解密;为明文 dict(沙箱注入)→ 直接合并不解密
    return create_handler(rec['source_type'], rec['config'], rec['secrets'])


# 平凡整表查询:仅 `SELECT * FROM <表>`(可带反引号/分号),无 WHERE/JOIN/LIMIT/ORDER/聚合等。
# 严格锚定整串,任何附加子句都不匹配 → 回退普通 query 路径(安全优先,绝不误判)。
_WHOLE_TABLE_RE = re.compile(r'^\s*select\s+\*\s+from\s+`?([A-Za-z_][\w$]*)`?\s*;?\s*$', re.IGNORECASE)


def _whole_table_native(native: Any) -> str | None:
    """`SELECT * FROM <表>` → 返回表名(可走 dlt 原生 pyarrow 流式快路);否则 None。

    仅对单一未限定标识符整表查询生效;含 schema 点号/WHERE/LIMIT/JOIN 等一律返回 None。
    """
    if not isinstance(native, str):
        return None
    m = _WHOLE_TABLE_RE.match(native)
    return m.group(1) if m else None


def _compile_transform(code: str):
    """编译逐行转换函数:用户代码须定义 transform(row)->row。"""
    ns: dict[str, Any] = {}
    exec(compile(code, '<etl-transform>', 'exec'), ns)
    fn = ns.get('transform')
    if not callable(fn):
        raise ValueError('转换代码必须定义 transform(row) 函数')
    return fn


# 代码取数(爬虫/任意取数)单次最多产出行数,防 OOM/撑爆装载;超出截断
_EXTRACT_ROW_CAP = 200000


def _is_dataframe(v: Any) -> bool:
    try:
        import pandas as pd

        return isinstance(v, pd.DataFrame)
    except Exception:
        return False


def _coerce_records(data: Any) -> list[dict]:
    """把用户代码产出的 result 归一为 list[dict]:支持 list[dict]/DataFrame/单 dict/可迭代。"""
    if data is None:
        raise ValueError('代码取数未产出结果:请把结果(list[dict])赋值给变量 result')
    try:
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            return data.to_dict('records')
    except ImportError:
        pass
    if isinstance(data, dict):
        return [data]
    if not isinstance(data, list):
        try:
            data = list(data)  # 生成器 / 其它可迭代
        except TypeError:
            raise ValueError(f'result 必须是 list[dict](或 DataFrame),实际为 {type(data).__name__}') from None
    if data and not isinstance(data[0], dict):
        raise ValueError('result 的元素必须是 dict(每行一条记录)')
    return data


@register_runner('DataIntegrationTask')
class DataIntegrationRunner(BaseRunner):
    """抽取 -> 转换 -> 装载。"""

    def _resolve_datasource(self, code: str) -> dict:
        """解析数据源记录 {source_type, config, secrets}。

        沙箱(无凭据)场景:context['resolved_datasources'] 由调用方预解密注入,secrets 为明文 dict;
        worker 正式场景:无注入,查库取记录,secrets 为 AES 密文串(由 from_record 内部解密)。
        """
        injected = (self.context.get('resolved_datasources') or {}).get(code)
        return injected or _load_datasource(code)

    def run(self) -> Any:
        from ezdata.handlers import Capability

        extract = self.params.get('extract') or {}
        transform = self.params.get('transform') or {}
        load = self.params.get('load') or {}

        fn = None
        if transform.get('enabled') and (transform.get('code') or '').strip():
            fn = _compile_transform(transform['code'])

        # 代码取数:用户写 Python 产出 result(list[dict]),worker 进程内执行(可访问任意外网,写爬虫)
        if (extract.get('mode') or '') == 'code':
            return self._run_code_extract(extract, load, fn)

        src_code = extract.get('datasource_code')
        native = extract.get('native')
        obj = (extract.get('object') or '').strip() or None
        dst_code = load.get('datasource_code')
        table = load.get('table') or obj
        if not (src_code and dst_code and table):
            raise ValueError('ETL 参数不完整:需 extract.datasource_code 与 load.datasource_code/table')

        self.logger.info(f'加载源数据源 {src_code} / 目标数据源 {dst_code}')
        src = _build_handler(self._resolve_datasource(src_code))
        dst = _build_handler(self._resolve_datasource(dst_code))
        if not dst.has(Capability.WRITE):
            raise ValueError(f'目标数据源 {dst.name} 不支持写入(WRITE)')

        # 流式源(无 READ):有界一批 / 长驻消费
        if not src.has(Capability.READ) and src.has(Capability.STREAM):
            return self._run_stream(src, dst, src_code, dst_code, table, obj, extract, load, fn)

        # 批量源:原生查询取数 -> 装载
        if not native:
            raise ValueError('批量源需提供 extract.native 原生查询')

        # 列式快路(无 transform + DB 目标):避开 query→list[dict] 行模式,直接喂 dlt 列式装载。
        # 任一条件不满足(转换/文件目标/不支持)都回退下方普通 query→list→write。
        from ezdata.utils.etl_util import assert_readonly_sql, is_file_target

        dst_is_file = is_file_target(getattr(dst, 'family', None))

        # 快路①:文件源(DuckDB)→ DuckDB→Arrow→dlt(实测约 3x)。任意只读查询都适用
        # (整条 SQL 交 DuckDB 跑,结果取 Arrow 而非 list;WHERE/列裁剪均可)。
        if not fn and not dst_is_file and isinstance(native, str) and hasattr(src, 'query_arrow'):
            assert_readonly_sql(native)
            self.logger.info(f'文件源 → DuckDB→Arrow→dlt 列式快路:{str(native)[:120]}')
            tbl = src.query_arrow(native)
            info = self._load(dst, src_code, table, tbl, load)
            self.logger.info(str(info)[:500])
            return f'ETL 完成(Arrow 列式): {src_code} -> {dst_code}.{table}'

        # 快路②:SQL 源整表查询(SELECT * FROM 表)→ dlt 原生 pyarrow 流式 extract→load(实测约 2x)。
        fast_table = None if fn else _whole_table_native(native)
        if fast_table and src.has(Capability.EXTRACT) and not dst_is_file:
            self.logger.info(f'整表无转换 → dlt 原生流式快路(pyarrow):extract {fast_table} -> {dst_code}.{table}')
            resource = src.extract(fast_table, backend='pyarrow')
            info = self._load(dst, src_code, table, resource, load)
            self.logger.info(str(info)[:500])
            return f'ETL 完成(pyarrow 流式): {src_code} -> {dst_code}.{table}'

        assert_readonly_sql(native)  # 抽取只读护栏:只允许 SELECT 类
        self.logger.info(f'执行原生查询抽取:{str(native)[:200]}')
        data = src.query(native, None, None)
        if fn:
            self.logger.info('应用逐行转换 transform(row)')
            data = [fn(dict(r)) for r in data]
        self.logger.info(f'抽取 {len(data)} 条')
        info = self._load(dst, src_code, table, data, load)
        self.logger.info(str(info)[:500])
        return f'ETL 完成: {src_code} -> {dst_code}.{table} ({len(data)} 行)'

    def _run_code_extract(self, extract: dict, load: dict, fn: Any) -> Any:
        """代码取数:在 worker 进程内执行用户 Python,取变量 result(list[dict])→ 可选转换 → 装载。

        - 不强制源数据源;可用 get_handler(code) 按需取某数据源 handler(.query()/.extract());
          仅选 1 个授权源时另注入 handler 别名。print() 即日志。
        - 与 transform 同为 worker 进程内 exec(同一信任模型);调试预览走沙箱(见 EtlService.preview)。
        """
        from ezdata.handlers import Capability

        code = (extract.get('code') or '').strip()
        if not code:
            raise ValueError('代码取数需提供 extract.code')
        dst_code = load.get('datasource_code')
        table = load.get('table')
        if not (dst_code and table):
            raise ValueError('代码取数需 load.datasource_code 与 load.table')
        allowed = list(extract.get('datasource_codes') or [])

        dst = _build_handler(self._resolve_datasource(dst_code))
        if not dst.has(Capability.WRITE):
            raise ValueError(f'目标数据源 {dst.name} 不支持写入(WRITE)')

        def get_handler(ds_code: str) -> Any:
            if allowed and ds_code not in allowed:
                raise ValueError(f'数据源未在「可用数据源」中授权: {ds_code}')
            return _build_handler(self._resolve_datasource(ds_code))

        # 流式分批装载:三种产出方式都支持,由平台边取边装(首批按配置 mode——如 replace 先清空目标,
        # 后续批次一律 append),适合分页/大表——单批失败不拖垮已装批次,也不必把全量堆进内存。
        #   ① emit(rows):反复调用,回调式;
        #   ② result 赋成生成器(生成器函数产出,可 yield 单行 dict 或整批 list[dict])→ 原生 yield 流式;
        #   ③ result 赋成 list/DataFrame/dict → 一次性装载(向后兼容)。
        stream_state = {'total': 0, 'first': True}
        _CHUNK = 500  # 生成器逐行 yield 时的攒批大小

        def _load_batch(batch: list) -> int:
            if fn:
                batch = [fn(dict(r)) for r in batch]
            remain = _EXTRACT_ROW_CAP - stream_state['total']
            if remain <= 0 or not batch:
                return 0
            batch = batch[:remain]
            m = (load.get('mode') or 'append') if stream_state['first'] else 'append'
            self._load(dst, 'code', table, batch, {**load, 'mode': m})
            stream_state['first'] = False
            stream_state['total'] += len(batch)
            self.logger.info(f'流式分批已装载 {stream_state["total"]} 条')
            return len(batch)

        emit_used = {'v': False}

        def emit(rows: Any) -> int:
            emit_used['v'] = True
            return _load_batch(_coerce_records(rows if rows is not None else []))

        ns: dict[str, Any] = {
            'get_handler': get_handler,
            'logger': self.logger,
            'log': self.logger.info,
            'emit': emit,
            'result': None,
        }
        if len(allowed) == 1:
            ns['handler'] = get_handler(allowed[0])
        self.logger.info('执行代码取数(worker 进程内)…')
        exec(compile(code, '<etl-extract>', 'exec'), ns)
        res = ns.get('result')

        def _empty_replace_guard() -> None:
            if stream_state['total'] == 0 and (load.get('mode') or 'append') == 'replace':
                self._load(dst, 'code', table, [], load)  # replace 但零产出 → 清空目标(建空表/索引)

        # ① emit 已边取边装
        if emit_used['v']:
            _empty_replace_guard()
            return f'ETL 完成(代码取数·流式分批): -> {dst_code}.{table} ({stream_state["total"]} 行)'
        # ② result 是生成器/迭代器(排除 list/tuple/dict/str/bytes/DataFrame)→ 原生 yield 流式
        if (
            res is not None
            and not isinstance(res, (list, tuple, dict, str, bytes))
            and not _is_dataframe(res)
            and hasattr(res, '__iter__')
        ):
            buf: list[dict] = []
            for item in res:
                if item is None:
                    continue
                buf.extend(_coerce_records(item))  # yield 单行 dict → [dict];yield 整批 list → 原样
                while len(buf) >= _CHUNK:
                    _load_batch(buf[:_CHUNK])
                    buf = buf[_CHUNK:]
                if stream_state['total'] >= _EXTRACT_ROW_CAP:
                    self.logger.info(f'生成器流式已达上限 {_EXTRACT_ROW_CAP},停止')
                    buf = []
                    break
            if buf:
                _load_batch(buf)
            _empty_replace_guard()
            return f'ETL 完成(代码取数·生成器流式): -> {dst_code}.{table} ({stream_state["total"]} 行)'
        # ③ 一次性 result(list/DataFrame/dict)
        data = _coerce_records(res)
        if len(data) > _EXTRACT_ROW_CAP:
            self.logger.info(f'代码取数 {len(data)} 行,超上限 {_EXTRACT_ROW_CAP},已截断')
            data = data[:_EXTRACT_ROW_CAP]
        if fn:
            self.logger.info('应用逐行转换 transform(row)')
            data = [fn(dict(r)) for r in data]
        self.logger.info(f'代码取数 {len(data)} 条')
        info = self._load(dst, 'code', table, data, load)
        self.logger.info(str(info)[:500])
        return f'ETL 完成(代码取数): -> {dst_code}.{table} ({len(data)} 行)'

    def _run_stream(
        self,
        src: Any,
        dst: Any,
        src_code: str,
        dst_code: str,
        table: str,
        obj: str | None,
        extract: dict,
        load: dict,
        fn: Any,
    ) -> Any:
        """流式源:max_events 有值→有界读取一批;否则长驻阻塞消费,微批持续装载。"""
        from ezdata.utils.etl_util import stream_kwargs, stream_statement

        max_events = int(extract.get('max_events') or 0)
        if max_events > 0:  # 有界:读这一批后一次性装载
            self.logger.info(f'流式有界读取最多 {max_events} 条(table/topic={obj or "全部"})')
            data = src.query(stream_statement(obj), None, max_events)
            if fn:
                data = [fn(dict(r)) for r in data]
            self.logger.info(f'读取 {len(data)} 条')
            info = self._load(dst, src_code, table, data, load)
            self.logger.info(str(info)[:500])
            return f'流式有界摄取完成: {src_code} -> {dst_code}.{table} ({len(data)} 条)'

        # 无界:长驻阻塞消费,微批写入(任务 hang 住直到被终止)
        batch_size = int(extract.get('batch_size') or 100)
        self.logger.info(f'流式长驻消费(微批 {batch_size},阻塞直到任务终止)…')
        buf: list[dict] = []
        total = 0
        for ev in src.stream(**stream_kwargs(obj)):
            buf.append(fn(dict(ev)) if fn else ev)
            if len(buf) >= batch_size:
                self._load(dst, src_code, table, buf, load)
                total += len(buf)
                self.logger.info(f'已装载 {total} 条')
                buf = []
        if buf:  # 正常不会到这(stream 阻塞),保险
            self._load(dst, src_code, table, buf, load)
            total += len(buf)
        return f'流式消费结束: {src_code} -> {dst_code}.{table} ({total} 条)'

    def _load(self, dst: Any, src_code: str, table: str, data: list[dict], load: dict) -> Any:
        """装载一批记录:对象存储序列化整写,其余走 dlt pipeline。

        pipeline_name 以 task_id 为唯一键:不同任务即使写同一目标表也用各自的 dlt pipeline 状态,
        避免并发/多任务共用 pipeline 状态相互串扰;同一任务重跑沿用同名 pipeline(保留增量状态)。
        """
        from ezdata.utils.etl_util import is_file_target, serialize_records

        mode = load.get('mode') or 'append'
        dataset = load.get('dataset') or 'public'
        if is_file_target(getattr(dst, 'family', None)):
            return dst.write(serialize_records(data, load.get('format') or 'csv'), table, mode=mode)
        pname = f'etl_{self.context.get("task_id") or src_code}_{table}'
        return dst.write(data, table, mode=mode, dataset=dataset, pipeline_name=pname)
