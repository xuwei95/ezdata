"""指标下推的中间表示(AggSpec):把指标定义规整成与源无关的聚合意图。

各源族(SQL/ES/…)的 handler.aggregate(spec) 把它编译成原生聚合下推执行;
遇到超出自身下推能力的形态就抛 AggNotSupported,由上层(MetricService)回退到
"拉数 + pandas 聚合"兜底路径——所以下推永不比现状差,可逐指标灰度。

default_filters 与时间/维度默认值的解析在 MetricService 侧完成,AggSpec 只承载
"最终要算什么":handler 不需懂指标定义。
"""

from __future__ import annotations

from dataclasses import dataclass, field

# 度量聚合语义(各源族各自映射到原生函数)。count=计行数;count_distinct=去重计数。
AGG_FUNCS = frozenset({'sum', 'avg', 'max', 'min', 'count', 'count_distinct'})
GRAINS = frozenset({'day', 'week', 'month'})


class AggNotSupported(Exception):
    """该 AggSpec 超出当前源的下推能力 → 上层应回退到拉数 + pandas 兜底。"""


@dataclass
class AggSpec:
    """一次聚合的完整意图(源无关)。"""

    table: str  # 物理表 / 索引 / 集合名
    measure: dict  # {'agg': sum/avg/max/min/count/count_distinct, 'field': 列名}
    group_by: list[str] = field(default_factory=list)  # 分组维度(已解析:含默认维度)
    filters: dict = field(default_factory=dict)  # {字段: 值 | [值...]} 等值/IN(已并入 default_filters)
    time_field: str | None = None
    time_range: dict | None = None  # {'start': 'YYYY-MM-DD', 'end': ...}
    grain: str | None = None  # 时间分桶 day/week/month(基于 time_field)
    top_n: int = 0  # 按 value 降序取前 N;0=不限

    @property
    def agg(self) -> str:
        return (self.measure.get('agg') or 'sum').lower()

    @property
    def field(self) -> str | None:
        return self.measure.get('field') or None

    def validate(self) -> None:
        """公共前置校验:非法/不可下推的形态直接抛 AggNotSupported(交由兜底)。"""
        if self.agg not in AGG_FUNCS:
            raise AggNotSupported(f'不支持的聚合: {self.agg}')
        if self.agg != 'count' and not self.field:
            # count 可无字段(计行数);其余聚合必须指定度量字段
            raise AggNotSupported(f'聚合 {self.agg} 需要度量字段')
        if self.grain and self.grain not in GRAINS:
            raise AggNotSupported(f'不支持的时间粒度: {self.grain}')
        if self.grain and not self.time_field:
            raise AggNotSupported('指定 grain 需要 time_field')
