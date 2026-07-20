"""指标层执行:把指标定义编译成对模型的取数 + 服务端 pandas 聚合,返回权威一致的数。

为什么服务端 pandas 聚合而非下推 ES 声明式聚合:ES 声明式聚合(Top-N 不下推/KPI 取不到)实测不可靠
(见 chart-tool-routing);demo/中等数据量下,取行 + pandas 聚合确定、简单。大表下推留 P1b。

- run_sync():给 agent 工具(agno 同步)用,全同步(get_sync_session_local + 同步 handler)。
- run():给控制器测试用(async)。
- 两者共用 _aggregate();catalog 供指标目录注入 / list_metrics。
"""

from __future__ import annotations

import json
from typing import Any

_FETCH_CAP = 10000
_AGG = {'sum': 'sum', 'avg': 'mean', 'mean': 'mean', 'max': 'max', 'min': 'min', 'count': 'count', 'count_distinct': 'nunique'}


def _loads(s: str | None, default: Any) -> Any:
    if not s:
        return default
    try:
        return json.loads(s)
    except (ValueError, TypeError):
        return default


def _aggregate(code: str, md: dict, rows: list, group_by, filters, time_range, top_n) -> dict:
    """纯聚合:md=指标字段快照(measure/dimensions/default_filters/time_field/unit/caliber)。"""
    import pandas as pd

    df = pd.DataFrame(rows or [])
    if df.empty:
        return {'code': code, 'unit': md.get('unit') or '', 'caliber': md.get('caliber') or '', 'rows': []}

    for f, v in {**_loads(md.get('default_filters'), {}), **(filters or {})}.items():
        if f in df.columns:
            vals = v if isinstance(v, list) else [v]
            df = df[df[f].astype(str).isin([str(x) for x in vals])]
    tf = md.get('time_field')
    if time_range and tf and tf in df.columns:
        if time_range.get('start'):
            df = df[df[tf].astype(str) >= str(time_range['start'])]
        if time_range.get('end'):
            df = df[df[tf].astype(str) <= str(time_range['end'])]

    measure = _loads(md.get('measure'), {}) or {}
    agg = _AGG.get((measure.get('agg') or 'sum').lower(), 'sum')
    field = measure.get('field')
    if field and field in df.columns and agg not in ('count', 'nunique'):
        df[field] = pd.to_numeric(df[field], errors='coerce')

    dims = group_by or [d.get('field') for d in _loads(md.get('dimensions'), []) if isinstance(d, dict) and d.get('field')]
    dims = [d for d in dims if d in df.columns]

    if dims:
        grp = df.groupby(dims, dropna=False)
        ser = grp.size() if (agg == 'count' or not field) else getattr(grp[field], agg)()
        res = ser.reset_index()
        res.columns = list(dims) + ['value']
        res = res.sort_values('value', ascending=False)
        if top_n:
            res = res.head(int(top_n))
        out_rows = res.to_dict('records')
    else:
        if agg == 'count' or not field:
            val: Any = int(len(df))
        elif agg == 'nunique':
            val = int(df[field].nunique())
        else:
            val = getattr(pd.to_numeric(df[field], errors='coerce'), agg)()
        out_rows = [{'value': (round(float(val), 4) if val is not None and val == val else None)}]

    for row in out_rows:
        for k, v in list(row.items()):
            if isinstance(v, float):
                row[k] = None if v != v else round(v, 4)
    return {'code': code, 'unit': md.get('unit') or '', 'caliber': md.get('caliber') or '', 'rows': out_rows}


def _md(metric) -> dict:
    return {
        'measure': metric.measure,
        'dimensions': metric.dimensions,
        'default_filters': metric.default_filters,
        'time_field': metric.time_field,
        'unit': metric.unit,
        'caliber': metric.caliber,
    }


class MetricService:
    # ---------- 同步(给 agent 工具) ----------
    @classmethod
    def catalog_sync(cls) -> list[dict]:
        from sqlalchemy import select

        from module_data.entity.do.data_metric_do import DataMetric
        from module_task_schedule.sync_db import get_sync_session_local

        db = get_sync_session_local()()
        try:
            rows = db.execute(select(DataMetric).where(DataMetric.status == '0').order_by(DataMetric.metric_id)).scalars().all()
            return [
                {
                    'code': r.code,
                    'name': r.name,
                    'caliber': (r.caliber or '').strip(),
                    'dimensions': [d.get('field') for d in _loads(r.dimensions, []) if isinstance(d, dict) and d.get('field')],
                    'unit': r.unit or '',
                }
                for r in rows
            ]
        finally:
            db.close()

    @classmethod
    def run_sync(cls, metric_code: str, group_by=None, filters=None, time_range=None, top_n=None) -> dict:
        from sqlalchemy import select

        from module_data.entity.do.data_do import DataModel, DataSource
        from module_data.entity.do.data_metric_do import DataMetric
        from module_data.service.data_service import _handler_from_ds
        from module_task_schedule.sync_db import get_sync_session_local

        db = get_sync_session_local()()
        try:
            metric = db.execute(select(DataMetric).where(DataMetric.code == metric_code, DataMetric.status == '0')).scalars().first()
            if not metric:
                avail = ', '.join(m['code'] for m in cls.catalog_sync()) or '(无)'
                return {'error': f'指标不存在或已停用: {metric_code}。可用指标: {avail}'}
            if not metric.model_id:
                return {'error': f'指标 {metric_code} 未绑定数据模型'}
            model = db.execute(select(DataModel).where(DataModel.id == metric.model_id)).scalars().first()
            ds = model and db.execute(select(DataSource).where(DataSource.code == model.datasource_code)).scalars().first()
            if not model or not ds:
                return {'error': f'指标 {metric_code} 的模型/数据源缺失'}
            md = _md(metric)
            handler = _handler_from_ds(ds)
            native = handler.sample_query(model.object_name or '', _FETCH_CAP)
            rows = handler.query(native, None, _FETCH_CAP)
        finally:
            db.close()
        return _aggregate(metric_code, md, rows, group_by, filters, time_range, top_n)

    # ---------- 异步 CRUD(指标管理页) ----------
    @classmethod
    async def get_list(cls, db, query, is_page: bool = False):
        from module_data.dao.data_metric_dao import DataMetricDao

        return await DataMetricDao.get_list(db, query, True, is_page)

    @classmethod
    async def detail(cls, db, metric_id: int):
        from utils.common_util import CamelCaseUtil

        from module_data.dao.data_metric_dao import DataMetricDao
        from module_data.entity.vo.data_metric_vo import DataMetricModel

        obj = await DataMetricDao.get_by_id(db, metric_id)
        return DataMetricModel(**CamelCaseUtil.transform_result(obj)) if obj else DataMetricModel()

    @classmethod
    async def add(cls, db, vo, operator: str):
        import datetime as _dt

        from common.vo import CrudResponseModel
        from exceptions.exception import ServiceException
        from module_data.dao.data_metric_dao import DataMetricDao

        if await DataMetricDao.get_by_code(db, vo.code):
            raise ServiceException(message=f'指标代码已存在: {vo.code}')
        try:
            data = vo.model_dump(exclude_unset=True, exclude={'metric_id', 'create_time', 'update_time'})
            data.update(create_by=operator, create_time=_dt.datetime.now(), built_in='0', review_state='ok')
            await DataMetricDao.add(db, data)
            await db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def edit(cls, db, vo, operator: str):
        import datetime as _dt

        from common.vo import CrudResponseModel
        from exceptions.exception import ServiceException
        from module_data.dao.data_metric_dao import DataMetricDao

        existing = await DataMetricDao.get_by_id(db, vo.metric_id)
        if not existing:
            raise ServiceException(message='指标不存在')
        try:
            data = vo.model_dump(exclude_unset=True, exclude={'create_time', 'create_by'})
            data.update(update_by=operator, update_time=_dt.datetime.now(), review_state='ok')  # 人工确认即消除 stale
            data['metric_id'] = vo.metric_id
            await DataMetricDao.edit(db, data)
            await db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def delete(cls, db, ids: str):
        from common.vo import CrudResponseModel
        from module_data.dao.data_metric_dao import DataMetricDao

        try:
            for i in [x for x in ids.split(',') if x]:
                await DataMetricDao.remove(db, int(i))
            await db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def preview(cls, db, metric_code: str, top_n: int = 10) -> dict:
        """管理页试跑:同步执行(threadpool 包裹避免阻塞事件循环)。"""
        from fastapi.concurrency import run_in_threadpool

        return await run_in_threadpool(cls.run_sync, metric_code, None, None, None, top_n)

    # ---------- 异步(agent 目录) ----------
    @classmethod
    async def resolve_agent_metrics(cls, db) -> list[dict]:
        from module_data.dao.data_metric_dao import DataMetricDao

        rows = await DataMetricDao.list_enabled(db)
        return [
            {
                'code': r.code,
                'name': r.name,
                'caliber': (r.caliber or '').strip(),
                'dimensions': [d.get('field') for d in _loads(r.dimensions, []) if isinstance(d, dict) and d.get('field')],
                'unit': r.unit or '',
            }
            for r in rows
        ]
