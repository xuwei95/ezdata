"""指标层 ES 族下推 测试(无在线集群,用 FakeES)。

验证:①AggSpec → ES DSL 构造正确(terms/.keyword/order/range/count)
②聚合响应 → 行映射正确 ③不可下推形态(多维/grain/非法聚合)抛 AggNotSupported → 回退兜底。
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ezdata.handlers.agg_spec import AggNotSupported, AggSpec
from ezdata.handlers.base import Column
from ezdata.handlers.elasticsearch_handler.elasticsearch_handler import ElasticsearchHandler

_ES_COLS = {'dt': 'date', 'symbol': 'keyword', 'sector': 'text', 'sector.keyword': 'keyword', 'amount': 'double'}


def _norm(rows):
    def cell(v):
        return round(float(v), 4) if isinstance(v, (int, float)) and not isinstance(v, bool) else (None if v is None else str(v))

    return sorted(tuple(sorted((k, cell(v)) for k, v in r.items())) for r in rows)


# --------------------------------------------------------------------------- #
# DSL 构造(_build_agg_request 纯函数)
# --------------------------------------------------------------------------- #
def test_es_build_request_group_by_metric():
    spec = AggSpec(table='idx', measure={'agg': 'sum', 'field': 'amount'}, group_by=['sector'], top_n=3)
    body, dim = ElasticsearchHandler._build_agg_request(spec, _ES_COLS)
    assert dim == 'sector'
    assert body['size'] == 0
    terms = body['aggs']['sector']['terms']
    assert terms['field'] == 'sector.keyword'  # text 字段自动补 .keyword
    assert terms['size'] == 3  # top_n → terms size
    assert terms['order'] == {'value': 'desc'}  # 有度量按度量降序
    assert body['aggs']['sector']['aggs']['value'] == {'sum': {'field': 'amount'}}


def test_es_build_request_filters_and_time_range():
    spec = AggSpec(
        table='idx', measure={'agg': 'sum', 'field': 'amount'}, group_by=['sector'],
        filters={'sector': 'bank', 'symbol': ['000001', '600519']}, time_field='dt',
        time_range={'start': '2024-01-01', 'end': '2024-01-31'},
    )
    body, _ = ElasticsearchHandler._build_agg_request(spec, _ES_COLS)
    fl = body['query']['bool']['filter']
    assert {'terms': {'sector.keyword': ['bank']}} in fl  # 文本等值 → keyword terms
    assert {'terms': {'symbol': ['000001', '600519']}} in fl  # keyword 字段原样
    assert {'range': {'dt': {'gte': '2024-01-01', 'lte': '2024-01-31'}}} in fl


def test_es_build_request_count_distinct_and_count():
    body, _ = ElasticsearchHandler._build_agg_request(
        AggSpec(table='idx', measure={'agg': 'count_distinct', 'field': 'symbol'}), _ES_COLS
    )
    assert body['aggs']['value'] == {'cardinality': {'field': 'symbol'}}
    body2, _ = ElasticsearchHandler._build_agg_request(  # count 无度量子聚合(取 doc_count / count API)
        AggSpec(table='idx', measure={'agg': 'count', 'field': None}, group_by=['sector']), _ES_COLS
    )
    assert 'aggs' not in body2['aggs']['sector']
    assert body2['aggs']['sector']['terms']['order'] == {'_count': 'desc'}


@pytest.mark.parametrize('bad', [
    AggSpec(table='idx', measure={'agg': 'sum', 'field': 'amount'}, group_by=['sector', 'symbol']),  # 多维
    AggSpec(table='idx', measure={'agg': 'sum', 'field': 'amount'}, time_field='dt', grain='month'),  # grain
    AggSpec(table='idx', measure={'agg': 'median', 'field': 'amount'}),  # 非法聚合
])
def test_es_unsupported_shapes_raise(bad):
    with pytest.raises(AggNotSupported):
        ElasticsearchHandler._build_agg_request(bad, _ES_COLS)


# --------------------------------------------------------------------------- #
# 聚合响应 → 行映射(FakeES 回放)
# --------------------------------------------------------------------------- #
class _FakeES:
    """最小 ES client 假体:按预置响应回放 search / count。"""

    def __init__(self, search_resp=None, count_resp=None):
        self._search_resp = search_resp or {}
        self._count_resp = count_resp or {'count': 0}
        self.last_search = None
        self.last_count = None

    def search(self, index, body):
        self.last_search = {'index': index, 'body': body}
        return self._search_resp

    def count(self, index, body):
        self.last_count = {'index': index, 'body': body}
        return self._count_resp


def _es_handler(fake):
    h = ElasticsearchHandler({'hosts': 'http://x:9200'})
    h._client = fake  # 注入假 client,跳过真实连接
    h.get_columns = lambda table: [Column(name=k, type=v) for k, v in _ES_COLS.items()]  # 跳过 mapping 探测
    return h


def test_es_aggregate_group_by_maps_rows():
    resp = {'aggregations': {'sector': {'buckets': [
        {'key': 'insurance', 'doc_count': 1, 'value': {'value': 300.0}},
        {'key': 'bank', 'doc_count': 2, 'value': {'value': 260.0}},
        {'key': 'baijiu', 'doc_count': 2, 'value': {'value': 250.0}},
    ]}}}
    h = _es_handler(_FakeES(search_resp=resp))
    out = h.aggregate(AggSpec(table='idx', measure={'agg': 'sum', 'field': 'amount'}, group_by=['sector']))
    assert _norm(out) == _norm([
        {'sector': 'insurance', 'value': 300.0},
        {'sector': 'bank', 'value': 260.0},
        {'sector': 'baijiu', 'value': 250.0},
    ])
    assert h._client.last_search['body']['aggs']['sector']['terms']['field'] == 'sector.keyword'


def test_es_aggregate_total_metric_maps_single_value():
    h = _es_handler(_FakeES(search_resp={'aggregations': {'value': {'value': 860.0}}}))
    out = h.aggregate(AggSpec(table='idx', measure={'agg': 'sum', 'field': 'amount'}))
    assert out == [{'value': 860.0}]


def test_es_aggregate_count_uses_count_api():
    h = _es_handler(_FakeES(count_resp={'count': 5}))
    out = h.aggregate(AggSpec(table='idx', measure={'agg': 'count', 'field': None}))
    assert out == [{'value': 5}]
    assert h._client.last_count is not None  # 走了 count API,而非空聚合
