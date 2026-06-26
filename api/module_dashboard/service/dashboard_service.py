"""控制台概览:聚合各模块计数 + 分布 + 任务趋势(多租户由 TenantMixin 自动过滤)。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from module_ai.entity.do.ai_app_do import AiApp
from module_ai.entity.do.ai_model_do import AiModels
from module_ai.entity.do.ai_tool_do import AiTool
from module_ai.service.ai_metrics_service import AiMetricsService
from module_data.entity.do.data_do import DataModel, DataSource
from module_rag.entity.do.rag_do import RagChunk, RagDataset, RagDocument
from module_task_schedule.entity.do.task_do import Task, TaskInstance

_RAG_DOC = {1: '待训练', 2: '训练中', 3: '成功', 4: '失败'}


class DashboardService:
    @classmethod
    async def overview(cls, db: AsyncSession) -> dict[str, Any]:
        async def cnt(entity: Any, *where: Any) -> int:
            q = select(func.count()).select_from(entity)
            for w in where:
                q = q.where(w)
            return int((await db.execute(q)).scalar() or 0)

        async def dist(col: Any, mapper: dict | None = None) -> list[dict]:
            rows = (await db.execute(select(col, func.count()).group_by(col))).all()
            out = []
            for k, v in rows:
                name = mapper.get(int(k), '未知') if (mapper and k is not None) else (str(k) if k not in (None, '') else '未知')
                out.append({'name': name, 'value': int(v)})
            return out

        cards = {
            'dataSources': await cnt(DataSource),
            'dataModels': await cnt(DataModel),
            'tasks': await cnt(Task, Task.task_type == 1),
            'dags': await cnt(Task, Task.task_type == 2),
            'knowledgeBases': await cnt(RagDataset),
            'documents': await cnt(RagDocument),
            'chunks': await cnt(RagChunk),
            'aiModels': await cnt(AiModels),
            'aiApps': await cnt(AiApp),
            'aiTools': await cnt(AiTool),
        }

        # AI 用量(复用 LLMOps 聚合):近 7 天 token/会话 + 趋势序列
        ai_usage = await AiMetricsService.overview(db, 7)

        source_family = await dist(DataSource.family)
        source_type = await dist(DataSource.source_type)
        rag_doc_status = await dist(RagDocument.status, _RAG_DOC)

        # 任务实例:近 7 天(避免全表扫 20 万)
        cutoff = datetime.now() - timedelta(days=7)
        ts_rows = (await db.execute(
            select(TaskInstance.status, func.count()).where(TaskInstance.start_time >= cutoff)
            .group_by(TaskInstance.status))).all()
        task_status = [{'name': s or '未知', 'value': int(v)} for s, v in ts_rows]

        tr_rows = (await db.execute(
            select(func.date(TaskInstance.start_time), TaskInstance.status, func.count())
            .where(TaskInstance.start_time >= cutoff)
            .group_by(func.date(TaskInstance.start_time), TaskInstance.status))).all()
        trend_map: dict[str, dict] = {}
        for d, s, v in tr_rows:
            key = str(d)
            t = trend_map.setdefault(key, {'date': key, 'success': 0, 'failure': 0, 'total': 0})
            t['total'] += int(v)
            if s == 'SUCCESS':
                t['success'] += int(v)
            elif s == 'FAILURE':
                t['failure'] += int(v)
        task_trend = sorted(trend_map.values(), key=lambda x: x['date'])

        recent = (await db.execute(
            select(TaskInstance).order_by(desc(TaskInstance.start_time)).limit(8))).scalars().all()
        recent_runs = [{
            'name': r.name, 'status': r.status, 'startTime': r.start_time,
            'dur': cls._dur(r.start_time, r.end_time),
        } for r in recent]

        return {
            'cards': cards, 'sourceFamily': source_family, 'sourceType': source_type,
            'ragDocStatus': rag_doc_status, 'taskStatus': task_status,
            'taskTrend': task_trend, 'recentRuns': recent_runs,
            'aiUsage': {'totals': ai_usage.get('totals') or {}, 'series': ai_usage.get('series') or []},
        }

    @staticmethod
    def _dur(start: datetime | None, end: datetime | None) -> str:
        if not start or not end:
            return ''
        sec = int((end - start).total_seconds())
        if sec < 60:
            return f'{sec}s'
        if sec < 3600:
            return f'{sec // 60}m{sec % 60}s'
        return f'{sec // 3600}h{(sec % 3600) // 60}m'
