"""AI 可观测(LLMOps)聚合服务。

数据源:agno 落库的 ai_sessions.runs(每轮含 model / metrics(tokens,duration) / status / user_id /
created_at)。在应用层聚合出用量总览、按天趋势、按模型/用户排行。会话量大时可后续物化成汇总表。
"""

import json
import time
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


def _empty_overview() -> dict[str, Any]:
    """ai_sessions 尚未由 agno 建表(全新环境/未对话过)时的空结果。"""
    return {
        'totals': {
            'sessions': 0, 'runs': 0, 'inputTokens': 0, 'outputTokens': 0,
            'totalTokens': 0, 'avgDuration': 0, 'successRate': 0,
        },
        'series': [], 'byModel': [], 'byUser': [],
    }


class AiMetricsService:
    """对话/agent 用量与可观测聚合。"""

    @classmethod
    async def overview(cls, db: AsyncSession, days: int = 7) -> dict[str, Any]:
        since = int(time.time()) - max(int(days or 7), 1) * 86400
        # ai_sessions 由 agno 在首次对话时惰性建表;全新环境尚未对话则表不存在,返回空总览
        try:
            res = (await db.execute(text('SELECT user_id, runs FROM ai_sessions WHERE runs IS NOT NULL'))).all()
        except SQLAlchemyError:
            await db.rollback()
            return _empty_overview()

        sessions = 0
        total_runs = 0
        tin = tout = ttot = 0
        dur_sum = 0.0
        ok = 0
        by_model: dict[str, dict] = {}
        by_user: dict[str, dict] = {}
        by_day: dict[str, dict] = {}

        for user_id, runs_json in res:
            try:
                runs = json.loads(runs_json) if isinstance(runs_json, str) else (runs_json or [])
            except (ValueError, TypeError):
                continue
            counted = False
            for run in runs:
                ca = int(run.get('created_at') or 0)
                if ca and ca < since:
                    continue
                m = run.get('metrics') or {}
                it = int(m.get('input_tokens') or 0)
                ot = int(m.get('output_tokens') or 0)
                tt = int(m.get('total_tokens') or (it + ot))
                total_runs += 1
                tin += it
                tout += ot
                ttot += tt
                dur_sum += float(m.get('duration') or 0)
                status = str(run.get('status') or '').upper()
                if not any(k in status for k in ('ERROR', 'FAIL', 'CANCEL')):
                    ok += 1
                model = run.get('model') or 'unknown'
                bm = by_model.setdefault(model, {'model': model, 'runs': 0, 'tokens': 0})
                bm['runs'] += 1
                bm['tokens'] += tt
                uid = str(run.get('user_id') or user_id or '')
                bu = by_user.setdefault(uid, {'userId': uid, 'runs': 0, 'tokens': 0})
                bu['runs'] += 1
                bu['tokens'] += tt
                day = datetime.fromtimestamp(ca).strftime('%Y-%m-%d') if ca else '未知'
                bd = by_day.setdefault(day, {'date': day, 'tokens': 0, 'runs': 0})
                bd['tokens'] += tt
                bd['runs'] += 1
                counted = True
            if counted:
                sessions += 1

        names = await cls._user_names(db, list(by_user))
        for uid, v in by_user.items():
            v['userName'] = names.get(uid, uid)

        return {
            'totals': {
                'sessions': sessions, 'runs': total_runs,
                'inputTokens': tin, 'outputTokens': tout, 'totalTokens': ttot,
                'avgDuration': round(dur_sum / total_runs, 2) if total_runs else 0,
                'successRate': round(ok / total_runs * 100, 1) if total_runs else 0,
            },
            'series': sorted(by_day.values(), key=lambda x: x['date']),
            'byModel': sorted(by_model.values(), key=lambda x: -x['tokens'])[:10],
            'byUser': sorted(by_user.values(), key=lambda x: -x['tokens'])[:10],
        }

    @classmethod
    async def _user_names(cls, db: AsyncSession, uids: list[str]) -> dict[str, str]:
        ids = [int(u) for u in uids if str(u).isdigit()]
        if not ids:
            return {}
        in_clause = ','.join(str(i) for i in ids)  # 均为 int,无注入风险
        res = await db.execute(text(f'SELECT user_id, nick_name, user_name FROM sys_user WHERE user_id IN ({in_clause})'))
        return {str(r[0]): (r[1] or r[2] or str(r[0])) for r in res}
