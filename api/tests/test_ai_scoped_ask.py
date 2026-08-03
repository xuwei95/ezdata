"""DataQueryService.prep_ask 组装「AI 洞察」上下文(数据源编码/表名/列/业务说明)。

只测上下文组装,mock 掉 _load 以免连库;覆盖 fields 缓存命中 与 空则 get_columns 兜底 两条路径。
"""

import asyncio
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from module_data.service.data_service import DataQueryService


def test_prep_ask_uses_fields_cache(monkeypatch) -> None:
    m = types.SimpleNamespace(
        datasource_code='mysql_demo',
        object_name='orders',
        name='订单',
        fields=[{'name': 'city'}, {'name': 'amount'}, {'nope': 1}],  # 无 name 的项应被过滤
        remark='订单业务表',
    )

    async def fake_load(cls, db, m_id):
        return m, object()

    monkeypatch.setattr(DataQueryService, '_load', classmethod(fake_load))

    res = asyncio.run(DataQueryService.prep_ask(None, '1'))
    assert res['datasource_code'] == 'mysql_demo'
    assert res['table'] == 'orders'
    assert res['columns'] == ['city', 'amount']
    assert res['business'] == '订单业务表'


def test_prep_ask_falls_back_to_get_columns(monkeypatch) -> None:
    """fields 缓存为空时,实时 get_columns 兜底取列。"""
    m = types.SimpleNamespace(
        datasource_code='es_demo', object_name='idx_daily', name='日线', fields=[], remark=''
    )

    class _Handler:
        def get_columns(self, table):
            assert table == 'idx_daily'
            return [types.SimpleNamespace(name='ts'), types.SimpleNamespace(name='close')]

    async def fake_load(cls, db, m_id):
        return m, _Handler()

    monkeypatch.setattr(DataQueryService, '_load', classmethod(fake_load))

    res = asyncio.run(DataQueryService.prep_ask(None, '9'))
    assert res['columns'] == ['ts', 'close']
    assert res['table'] == 'idx_daily'
    assert res['business'] == ''
