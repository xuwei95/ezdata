"""用例集加载(YAML)。一个 .yaml 文件可含单条(dict)或多条(list)用例。"""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass, field
from typing import Any

import yaml

CASES_DIR = os.path.join(os.path.dirname(__file__), 'cases')


@dataclass
class EvalCase:
    id: str
    question: str
    model_id: int = 0                       # 0 = 环境兜底模型;>0 = 指定模型(A/B 用)
    app_id: str | None = None               # 指定应用(带工具/数据源范围)
    runs: int = 3                            # 重跑次数(弱模型稳定性 → 通过率)
    tags: list[str] = field(default_factory=list)
    checks: list[dict] = field(default_factory=list)   # [{type: ..., <参数>}]
    known_tables: list[str] = field(default_factory=list)  # no_hallucinated_table 用
    fixtures: list[str] = field(default_factory=list)  # replay 模式:该用例的录制文件(相对 fixtures/)

    @staticmethod
    def _from_dict(d: dict[str, Any]) -> EvalCase:
        return EvalCase(
            id=d['id'],
            question=d.get('question', ''),
            model_id=int(d.get('model_id', 0)),
            app_id=d.get('app_id'),
            runs=int(d.get('runs', 3)),
            tags=list(d.get('tags') or []),
            checks=list(d.get('checks') or []),
            known_tables=list(d.get('known_tables') or []),
            fixtures=list(d.get('fixtures') or []),
        )


def load_cases(path: str | None = None) -> list[EvalCase]:
    """加载用例。path 为空则扫 cases/ 下所有 *.yaml;可传单文件。"""
    files = [path] if path else sorted(glob.glob(os.path.join(CASES_DIR, '*.yaml')))
    cases: list[EvalCase] = []
    seen: set[str] = set()
    for fp in files:
        with open(fp, encoding='utf-8') as f:
            doc = yaml.safe_load(f) or []
        items = doc if isinstance(doc, list) else [doc]
        for it in items:
            c = EvalCase._from_dict(it)
            if c.id in seen:
                raise ValueError(f'用例 id 重复: {c.id}({fp})')
            seen.add(c.id)
            cases.append(c)
    return cases
