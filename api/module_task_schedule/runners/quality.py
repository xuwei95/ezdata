"""ETL 数据质量断言(纯函数,便于单测)。

规则(rules: list[dict],每条 {'type': ...}):
  - row_count_min : {'type':'row_count_min','min':100}                  数据集行数下限(数据集级)
  - not_null      : {'type':'not_null','fields':['a','b']}              指定字段不得为 None/''
  - unique        : {'type':'unique','fields':['id']}                   指定字段(组合)在数据内唯一
  - value_range   : {'type':'value_range','field':'age','min':0,'max':120}  数值区间(含端点,min/max 可缺)
  - allowed_values: {'type':'allowed_values','field':'status','values':['A','B']}  枚举白名单

行级规则(not_null/unique/value_range/allowed_values)由 check_quality 对一批数据评估;
row_count_min 属数据集级,由 check_row_count 单独评估(流式下对累计行数校验)。
每条 violation: {'rule','field','expected','actual','message'};message 供告警正文直接展示。
"""

from typing import Any

_ROW_RULES = {'not_null', 'unique', 'value_range', 'allowed_values'}


class DataQualityError(Exception):
    """数据质量断言失败(on_violation='block' 时抛出,使任务失败)。"""


def _to_float(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _sample(items: list[Any], n: int = 5) -> list[Any]:
    return items[:n]


def check_quality(data: list[dict], rules: list[dict]) -> list[dict]:
    """评估行级规则,返回 violations 列表(空=通过)。不评估 row_count_min。"""
    violations: list[dict] = []
    total = len(data)
    for rule in rules or []:
        rtype = rule.get('type')
        if rtype not in _ROW_RULES:
            continue

        if rtype == 'not_null':
            for f in rule.get('fields') or []:
                bad = sum(1 for r in data if r.get(f) in (None, ''))
                if bad:
                    violations.append({
                        'rule': 'not_null', 'field': f, 'expected': '无空值',
                        'actual': f'{bad}/{total} 行为空',
                        'message': f'字段「{f}」有 {bad}/{total} 行为空(not_null)',
                    })

        elif rtype == 'allowed_values':
            f = rule.get('field')
            allow = set(rule.get('values') or [])
            bad_vals = {r.get(f) for r in data if r.get(f) is not None and r.get(f) not in allow}
            if bad_vals:
                violations.append({
                    'rule': 'allowed_values', 'field': f, 'expected': sorted(allow, key=str),
                    'actual': _sample(sorted(bad_vals, key=str)),
                    'message': f'字段「{f}」出现非白名单值:{_sample(sorted(bad_vals, key=str))}(allowed_values)',
                })

        elif rtype == 'value_range':
            f = rule.get('field')
            lo, hi = rule.get('min'), rule.get('max')
            bad = 0
            for r in data:
                v = _to_float(r.get(f))
                if v is None:
                    continue  # 非数值/空交给 not_null 管
                if (lo is not None and v < float(lo)) or (hi is not None and v > float(hi)):
                    bad += 1
            if bad:
                violations.append({
                    'rule': 'value_range', 'field': f, 'expected': f'[{lo}, {hi}]',
                    'actual': f'{bad}/{total} 行越界',
                    'message': f'字段「{f}」有 {bad}/{total} 行超出区间 [{lo}, {hi}](value_range)',
                })

        elif rtype == 'unique':
            fields = rule.get('fields') or []
            seen: set = set()
            dups: set = set()
            for r in data:
                key = tuple(r.get(f) for f in fields)
                if key in seen:
                    dups.add(key)
                else:
                    seen.add(key)
            if dups:
                violations.append({
                    'rule': 'unique', 'field': ','.join(fields), 'expected': '唯一',
                    'actual': f'{len(dups)} 个重复键',
                    'message': f'字段「{",".join(fields)}」有 {len(dups)} 个重复键值(unique)',
                })

    return violations


def check_row_count(total_rows: int, rules: list[dict]) -> list[dict]:
    """评估数据集级 row_count_min 规则,返回 violations。"""
    violations: list[dict] = []
    for rule in rules or []:
        if rule.get('type') != 'row_count_min':
            continue
        min_rows = int(rule.get('min') or 0)
        if total_rows < min_rows:
            violations.append({
                'rule': 'row_count_min', 'field': None, 'expected': f'>= {min_rows}',
                'actual': total_rows,
                'message': f'装载行数 {total_rows} 低于下限 {min_rows}(row_count_min)',
            })
    return violations


def has_row_rules(rules: list[dict]) -> bool:
    return any((r.get('type') in _ROW_RULES) for r in (rules or []))


def has_row_count_rule(rules: list[dict]) -> bool:
    return any((r.get('type') == 'row_count_min') for r in (rules or []))
