"""纯逻辑自检(不依赖 ES/DB/网络):切分 / 清洗 / RRF / embedding 构造 / 工厂。"""

from module_rag.cleaner import clean_text
from module_rag.embedding import EmbeddingClient
from module_rag.text_split import split_text
from module_rag.vector_store.base import VectorStore
from module_rag.vector_store.factory import get_vector_store, supported_backends


def main() -> int:
    ok = True

    # 切分
    t = '段落一。' * 50 + '\n\n' + '第二段内容。' * 50
    ch = split_text(t, 120, 30)
    print('split:', len(ch), 'chunks, max len', max(len(c) for c in ch))
    ok &= len(ch) > 1 and all(len(c) <= 160 for c in ch)

    # 清洗(去空字节/控制符 + 压缩空白)
    cleaned = clean_text('hi' + chr(0) + chr(7) + '   there\n\n\n\nx')
    print('clean:', repr(cleaned))
    ok &= chr(0) not in cleaned and '\n\n\n' not in cleaned

    # RRF:y 在两路都靠前 → 融合第一
    a = [{'chunk_id': 'x'}, {'chunk_id': 'y'}, {'chunk_id': 'z'}]
    b = [{'chunk_id': 'y'}, {'chunk_id': 'w'}]
    fused = VectorStore.rrf_fuse([a, b])
    print('rrf:', [h['chunk_id'] for h in fused])
    ok &= fused[0]['chunk_id'] == 'y'

    # embedding 构造 + 已知维度
    c = EmbeddingClient('dashscope', 'text-embedding-v2', 'k')
    print('emb base:', c.base, 'dims:', c._dims)
    ok &= c._dims == 1536 and 'dashscope' in c.base

    # 工厂
    print('backends:', supported_backends())
    store = get_vector_store('elasticsearch', {'hosts': 'http://x:9200'}, 'idx')
    ok &= type(store).__name__ == 'EsVectorStore'
    try:
        get_vector_store('milvus', {}, 'i')
        ok = False  # 应抛 NotImplementedError
    except NotImplementedError:
        print('milvus 预留位正确抛出')

    print('RESULT:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
