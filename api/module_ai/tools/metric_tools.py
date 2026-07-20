"""指标层 agent 工具:list_metrics / query_metric(权威口径,漏斗最顶层)。

只在存在启用指标时挂载 + 注入目录(无指标零开销)。工具走 MetricService 同步路径。
"""

from __future__ import annotations

import json
from typing import Any

from agno.tools import Toolkit

from module_data.service.metric_service import MetricService


def build_metric_catalog(metrics: list[dict] | None) -> str:
    """生成「可用指标」常驻清单 + 优先用指令(注入 system)。空则返回空串。"""
    if not metrics:
        return ''
    lines = [
        '## 可用指标(权威口径 · 取数漏斗最顶层)',
        '问题若能映射到下列指标,**先调用 query_metric(该指标 code[, group_by, filters, top_n]) 取一致权威的数,不要自己写 SQL/聚合**;不匹配再走认源/取数。',
    ]
    for m in metrics:
        dims = '/'.join(m.get('dimensions') or []) or '无'
        unit = f";单位 {m['unit']}" if m.get('unit') else ''
        lines.append(f"- `{m.get('code')}`:{m.get('name')} —— {m.get('caliber') or ''}(可分组维度: {dims}{unit})")
    return '\n'.join(lines)


class MetricTools(Toolkit):
    """指标查询工具:list_metrics 看目录、query_metric 取权威数字。"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(name='metric', tools=[self.list_metrics, self.query_metric], **kwargs)

    def list_metrics(self, keyword: str = '') -> str:
        """列出可用指标(code / 名称 / 口径 / 可分组维度)。拿不准某个数是否已有权威指标时先调它。

        Args:
            keyword: 可选,按 code/名称/口径 模糊筛选
        """
        cat = MetricService.catalog_sync()
        if keyword:
            k = keyword.lower()
            cat = [m for m in cat if k in (m['code'] + m['name'] + m['caliber']).lower()]
        if not cat:
            return '无匹配指标'
        return '\n'.join(
            f"{m['code']}: {m['name']} — {m['caliber']} (维度: {'/'.join(m['dimensions']) or '无'}{'; 单位:' + m['unit'] if m['unit'] else ''})"
            for m in cat
        )

    def query_metric(
        self,
        metric_code: str,
        group_by: list | None = None,
        filters: dict | None = None,
        time_range: dict | None = None,
        top_n: int = 0,
    ) -> str:
        """按指标定义取权威一致的数(平台已编译好口径/聚合,无需你写查询)。

        问题能映射到「可用指标」清单里某项时优先用本工具。

        Args:
            metric_code: 指标代码(来自 list_metrics / 系统提示「可用指标」)
            group_by: 可选,分组维度列名数组(须在该指标「可分组维度」内);不传=按指标默认维度或算总值
            filters: 可选,等值过滤 {字段: 值 或 [值...]}
            time_range: 可选,时间范围 {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"}(该指标有时间字段时生效)
            top_n: 可选,只取前 N(按值降序;0=不限)
        """
        res = MetricService.run_sync(
            metric_code,
            group_by=group_by or None,
            filters=filters or None,
            time_range=time_range or None,
            top_n=top_n or None,
        )
        if res.get('error'):
            return res['error']
        rows = res.get('rows') or []
        head = f'指标 {metric_code}' + (f'(单位:{res["unit"]})' if res.get('unit') else '')
        body = json.dumps(rows, ensure_ascii=False)
        if len(body) > 1500:
            body = body[:1500] + f'…(共 {len(rows)} 行,已截断)'
        return f'{head}\n口径:{res.get("caliber") or ""}\n结果({len(rows)} 行):{body}'
