"""
P0 验证:EsVectorStore 在 ES8 上跑通最小闭环。

  建 mapping(dense_vector) → bulk 写向量 → kNN / BM25 / 混合检索 → 按文档删除。

用法:确保有一个 ES8 在 ES8_URL(默认 http://127.0.0.1:9201),然后:
  python -m module_rag._verify_es_vector
不依赖 es-py,纯 REST。验证用 8 维玩具向量 + 英文文本(避免依赖 ik 分词)。
"""

import os
import sys

from module_rag.es_vector_store import EsVectorStore

# 解析 ES 地址:ES8_URL > RAG_VECTOR_HOSTS > TASK_ES_HOSTS > 本机(host 9200 / 容器内同集群)
ES_URL = (
    os.environ.get('ES8_URL')
    or os.environ.get('RAG_VECTOR_HOSTS')
    or os.environ.get('TASK_ES_HOSTS')
    or 'http://127.0.0.1:9200'
)
DIMS = 8
INDEX = 'rag_ds_verify'
TENANT = '100'


def _vec(*xs: float) -> list[float]:
    """补齐到 DIMS 维。"""
    v = list(xs) + [0.0] * (DIMS - len(xs))
    return v[:DIMS]


# 三条分段:python / cat / dog,向量在不同坐标轴上拉开,文本可被 BM25 命中
DOCS = [
    {
        'chunk_id': 'c1',
        'document_id': 'd1',
        'dataset_id': 'verify',
        'tenant_id': TENANT,
        'chunk_type': 'chunk',
        'content': 'Python is a popular programming language for data engineering',
        'content_vector': _vec(1, 0, 0, 0),
    },
    {
        'chunk_id': 'c2',
        'document_id': 'd1',
        'dataset_id': 'verify',
        'tenant_id': TENANT,
        'chunk_type': 'chunk',
        'content': 'The cat sat on the warm windowsill in the morning sun',
        'content_vector': _vec(0, 1, 0, 0),
    },
    {
        'chunk_id': 'c3',
        'document_id': 'd2',
        'dataset_id': 'verify',
        'tenant_id': TENANT,
        'chunk_type': 'chunk',
        'content': 'A loyal dog runs fast across the green field chasing a ball',
        'content_vector': _vec(0, 0, 1, 0),
    },
]

PASS, FAIL = 0, 0


def check(label: str, cond: bool, detail: str = '') -> None:
    global PASS, FAIL
    mark = 'PASS' if cond else 'FAIL'
    if cond:
        PASS += 1
    else:
        FAIL += 1
    print(f'  [{mark}] {label}' + (f' — {detail}' if detail else ''))


def main() -> int:
    store = EsVectorStore({'hosts': ES_URL}, INDEX)

    print(f'== ES: {ES_URL} ==')
    check('ping', store.ping())
    if not store.ping():
        print(
            'ES8 不可达,先启动:docker run -d --name ezdata-es8-test -p 9201:9200 '
            '-e discovery.type=single-node -e xpack.security.enabled=false elasticsearch:8.13.4'
        )
        return 1

    # 干净起步
    store.drop()

    print('== 1. 建索引(dense_vector dims=8, cosine, HNSW) ==')
    created = store.ensure_index(DIMS)
    check('索引新建', created)
    check('ensure 幂等(再次不报错)', store.ensure_index(DIMS) is False)

    print('== 2. bulk 写入 3 条分段 ==')
    r = store.add(DOCS)
    check('写入条数=3', r['indexed'] == 3, str(r))
    check('count=3', store.count() == 3)
    check('租户过滤 count', store.count(filters=[{'term': {'tenant_id': TENANT}}]) == 3)

    print('== 3. 向量 kNN(查询向量贴近 c1=python) ==')
    vhits = store.vector_search(_vec(0.9, 0.1, 0, 0), k=2)
    check('kNN 返回结果', len(vhits) >= 1, f'{[h["chunk_id"] for h in vhits]}')
    check(
        'kNN top1 = c1',
        vhits and vhits[0]['chunk_id'] == 'c1',
        f'top1={vhits[0]["chunk_id"] if vhits else None} score={vhits[0].get("score") if vhits else None}',
    )

    print('== 4. BM25 全文(query="dog field") ==')
    khits = store.keyword_search('dog field', k=3)
    check('BM25 命中 c3', any(h['chunk_id'] == 'c3' for h in khits), f'{[h["chunk_id"] for h in khits]}')

    print('== 5. 混合检索(向量贴近 c1 + 文本 "cat") ==')
    hhits = store.hybrid_search(_vec(0.9, 0.1, 0, 0), 'cat windowsill', k=3)
    ids = [h['chunk_id'] for h in hhits]
    check('混合同时召回 c1(向量) 和 c2(全文)', 'c1' in ids and 'c2' in ids, f'{ids}')
    check('结果带 rrf_score', all('rrf_score' in h for h in hhits))

    print('== 6. 租户过滤(错误租户应召回 0) ==')
    none_hits = store.vector_search(_vec(0.9, 0.1, 0, 0), k=2, filters=[{'term': {'tenant_id': '999'}}])
    check('错误租户向量召回=0', len(none_hits) == 0, f'{[h["chunk_id"] for h in none_hits]}')

    print('== 7. 按 document_id 删除(d1 含 c1,c2) ==')
    deleted = store.delete_by_document('d1', tenant_id=TENANT)
    check('删除 2 条', deleted == 2, f'deleted={deleted}')
    check('count 余 1', store.count() == 1)
    rest = store.keyword_search('dog', k=3)
    check('剩余为 c3', [h['chunk_id'] for h in rest] == ['c3'], f'{[h["chunk_id"] for h in rest]}')

    # 收尾
    store.drop()
    print(f'\n== 结果:{PASS} passed, {FAIL} failed ==')
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
