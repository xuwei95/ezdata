"""任务级数据血缘:从**已声明**的任务参数 + 模型/指标绑定关系拼血缘图(零 SQL 解析)。

节点:datasource / task / model / metric;边:源→任务→模型(load)、模型→指标。
按需在内存计算(自托管规模足够,始终新鲜);列级/运行时血缘留 P3。
"""

from __future__ import annotations

import json
from collections import deque
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def _nid(t: str, i: str) -> str:
    return f'{t}:{i}'


class LineageService:
    @classmethod
    async def build_graph(cls, db: AsyncSession) -> dict:
        """全量血缘图 {nodes:[{id,type,name,meta}], edges:[{source,target,label}]}。"""
        from module_data.entity.do.data_do import DataModel, DataSource
        from module_data.entity.do.data_metric_do import DataMetric
        from module_task_schedule.entity.do.task_do import Task

        nodes: dict[str, dict] = {}
        edges: list[dict] = []

        def add_node(t: str, i: str, name: str, **meta):
            nid = _nid(t, i)
            if nid not in nodes:
                nodes[nid] = {'id': nid, 'type': t, 'name': name, **({'meta': meta} if meta else {})}
            return nid

        # 数据源
        for code, name, stype in (await db.execute(select(DataSource.code, DataSource.name, DataSource.source_type))).all():
            add_node('datasource', code, name or code, source_type=stype)
        # 模型(建 (datasource_code, object_name) → model 查找)
        model_by_obj: dict[tuple, str] = {}
        for mid, name, dc, obj in (
            await db.execute(select(DataModel.id, DataModel.name, DataModel.datasource_code, DataModel.object_name).where(DataModel.status == 1))
        ).all():
            if not obj:
                continue
            add_node('model', mid, name or obj, datasource_code=dc, object_name=obj)
            model_by_obj[(dc, obj)] = mid
            if dc:
                edges.append({'source': _nid('datasource', dc), 'target': _nid('model', mid), 'label': '属于'})
        # 任务:extract 源 → task → load 模型
        for tid, tname, params in (await db.execute(select(Task.id, Task.name, Task.params))).all():
            try:
                p = json.loads(params) if isinstance(params, str) else (params or {})
            except (ValueError, TypeError):
                continue
            ex, ld = p.get('extract') or {}, p.get('load') or {}
            if not ld.get('table'):
                continue  # 非数据集成任务(python/shell)无 load,跳过
            add_node('task', tid, tname or tid)
            tgt = model_by_obj.get((ld.get('datasource_code'), ld.get('table')))
            if tgt:
                edges.append({'source': _nid('task', tid), 'target': _nid('model', tgt), 'label': '产出'})
            src_codes = [c for c in ([ex.get('datasource_code')] + (ex.get('datasource_codes') or [])) if c]
            for sc in dict.fromkeys(src_codes):
                edges.append({'source': _nid('datasource', sc), 'target': _nid('task', tid), 'label': '抽取'})
        # 指标:模型 → 指标
        for code, name, mid in (
            await db.execute(select(DataMetric.code, DataMetric.name, DataMetric.model_id).where(DataMetric.status == '0'))
        ).all():
            add_node('metric', code, name or code, model_id=mid)
            if mid and _nid('model', mid) in nodes:
                edges.append({'source': _nid('model', mid), 'target': _nid('metric', code), 'label': '定义指标'})

        return {'nodes': list(nodes.values()), 'edges': edges}

    @classmethod
    def provenance_sync(cls, datasource_code: str, object_name: str) -> str:
        """(同步)某表的来源一句话:由哪个任务从哪个上游源抽取、定时/单次。供 get_table_schema 注入 agent。

        无产出任务(如直接建模的表)返回空串。
        """
        if not datasource_code or not object_name:
            return ''
        try:
            from module_task_schedule.entity.do.task_do import Task
            from module_task_schedule.sync_db import get_sync_session_local

            db = get_sync_session_local()()
            try:
                rows = db.execute(select(Task.name, Task.params, Task.trigger_type)).all()
            finally:
                db.close()
        except Exception:
            return ''
        parts: list[str] = []
        for name, params, trig in rows:
            try:
                p = json.loads(params) if isinstance(params, str) else (params or {})
            except (ValueError, TypeError):
                continue
            ld = p.get('load') or {}
            if ld.get('datasource_code') == datasource_code and ld.get('table') == object_name:
                ex = p.get('extract') or {}
                srcs = [c for c in ([ex.get('datasource_code')] + (ex.get('datasource_codes') or [])) if c]
                s = '/'.join(dict.fromkeys(srcs)) or '(代码取数)'
                parts.append(f'任务「{name}」从 {s} 抽取({"定时" if trig == 2 else "单次"})')
        return ('【来源/血缘】本表由 ' + ';'.join(parts) + '。') if parts else ''

    # datasource 是"星型 hub"(一个源挂着几十张表/任务):BFS 经它会瞬间炸成全图。
    # 除起点外,到达 datasource 即作终端(纳入节点、连边,但不再向外扩展),使模型血缘聚焦为
    # 它自身的来龙去脉(属于的源 + 产出它的任务 + 这些任务的抽取源 + 它上面的指标),不牵出兄弟表。
    _HUB_TYPES = {'datasource'}

    @classmethod
    async def subgraph(cls, db: AsyncSession, node_type: str, node_id: str, depth: int = 3) -> dict:
        """以某节点为中心,取 depth 跳内的上下游子图(datasource 作终端 hub,不外扩)。"""
        g = await cls.build_graph(db)
        start = _nid(node_type, node_id)
        idx = {n['id']: n for n in g['nodes']}
        if start not in idx:
            return {'nodes': [], 'edges': []}
        adj: dict[str, list[tuple]] = {}
        for e in g['edges']:
            adj.setdefault(e['source'], []).append((e['target'], e))
            adj.setdefault(e['target'], []).append((e['source'], e))
        seen = {start}
        keep_edges: list[dict] = []
        q: deque = deque([(start, 0)])
        while q:
            cur, d = q.popleft()
            # 到达 hub 型节点(非起点)不再外扩,避免经共享数据源炸成全图
            if d >= depth or (cur != start and idx[cur]['type'] in cls._HUB_TYPES):
                continue
            for nxt, e in adj.get(cur, []):
                if e not in keep_edges:
                    keep_edges.append(e)
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, d + 1))
        return {'nodes': [idx[n] for n in seen], 'edges': keep_edges}
