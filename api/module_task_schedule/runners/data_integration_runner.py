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
    from module_data.entity.do.data_do import DataSource  # noqa: PLC0415
    from module_task_schedule.sync_db import get_sync_session_local  # noqa: PLC0415

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
    from module_data.handlers import create_handler  # noqa: PLC0415

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
    exec(compile(code, '<etl-transform>', 'exec'), ns)  # noqa: S102 受限内部调试用途
    fn = ns.get('transform')
    if not callable(fn):
        raise ValueError('转换代码必须定义 transform(row) 函数')
    return fn


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
        from module_data.handlers import Capability  # noqa: PLC0415

        extract = self.params.get('extract') or {}
        transform = self.params.get('transform') or {}
        load = self.params.get('load') or {}

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

        fn = None
        if transform.get('enabled') and (transform.get('code') or '').strip():
            fn = _compile_transform(transform['code'])

        # 流式源(无 READ):有界一批 / 长驻消费
        if not src.has(Capability.READ) and src.has(Capability.STREAM):
            return self._run_stream(src, dst, src_code, dst_code, table, obj, extract, load, fn)

        # 批量源:原生查询取数 -> 装载
        if not native:
            raise ValueError('批量源需提供 extract.native 原生查询')

        # 列式快路(无 transform + DB 目标):避开 query→list[dict] 行模式,直接喂 dlt 列式装载。
        # 任一条件不满足(转换/文件目标/不支持)都回退下方普通 query→list→write。
        from module_data.etl_util import assert_readonly_sql, is_file_target  # noqa: PLC0415
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

    def _run_stream(self, src: Any, dst: Any, src_code: str, dst_code: str, table: str,
                    obj: str | None, extract: dict, load: dict, fn: Any) -> Any:
        """流式源:max_events 有值→有界读取一批;否则长驻阻塞消费,微批持续装载。"""
        from module_data.etl_util import stream_kwargs, stream_statement  # noqa: PLC0415

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

    @staticmethod
    def _load(dst: Any, src_code: str, table: str, data: list[dict], load: dict) -> Any:
        """装载一批记录:对象存储序列化整写,其余走 dlt pipeline。"""
        from module_data.etl_util import is_file_target, serialize_records  # noqa: PLC0415

        mode = load.get('mode') or 'append'
        dataset = load.get('dataset') or 'public'
        if is_file_target(getattr(dst, 'family', None)):
            return dst.write(serialize_records(data, load.get('format') or 'csv'), table, mode=mode)
        return dst.write(data, table, mode=mode, dataset=dataset, pipeline_name=f'etl_{src_code}_{table}')
