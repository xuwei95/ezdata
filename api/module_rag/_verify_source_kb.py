"""
验证「取数时从数据源专属知识库查询」链路:
  data_source → 专属 RagDataset(source_id) → 灌知识 → search_knowledge_base(query, source_id=...) 召回
在容器内跑:docker exec ezdata-backend-dev python -m module_rag._verify_source_kb
"""

import sys
import uuid
from datetime import datetime

from sqlalchemy import select

from common.context import RequestContext
from config.env import RagConfig
from module_data.entity.do.data_do import DataSource
from module_rag.agent_tools import make_kb_tool, search_knowledge_base
from module_rag.entity.do.rag_do import RagChunk, RagDataset
from module_rag.runtime_util import build_embedding_client, build_store, md5
from module_task_schedule.sync_db import get_sync_session_local

TENANT = 100
PASS = FAIL = 0


def check(label, cond, detail=''):
    global PASS, FAIL
    ok = bool(cond); PASS += ok; FAIL += (not ok)
    print(f'  [{"PASS" if ok else "FAIL"}] {label}' + (f' — {detail}' if detail else ''))


def main():
    token = RequestContext.set_current_tenant_id(TENANT)
    db = get_sync_session_local()()
    created = None
    try:
        src = db.execute(select(DataSource)).scalars().first()
        if not src:
            print('  无数据源,跳过'); return 0
        print(f'== 数据源:{src.name} ({src.id[:8]}) ==')

        # 1. 取或建该源专属知识库
        ds = db.execute(select(RagDataset).where(RagDataset.source_id == src.id)).scalars().first()
        if not ds:
            ds = RagDataset(id=uuid.uuid4().hex, name=f'{src.name} · 专属知识库', source_id=src.id,
                            embedding_provider=RagConfig.embedding_type, embedding_model=RagConfig.embedding_model,
                            vector_backend='elasticsearch', index_name=None, status=1, create_time=datetime.now())
            db.add(ds); db.commit(); created = ds.id
        check('专属知识库存在', ds is not None and ds.source_id == src.id, ds.id[:8])

        # 2. 灌入知识(1 条 QA + 1 条分段)
        client = build_embedding_client(ds)
        store = build_store(ds)
        kb = [  # (type, question, content)
            ('qa', '这个数据源是做什么的', f'数据源「{src.name}」用于演示,存放订单/任务等业务数据'),
            ('chunk', None, f'{src.name} 的 orders 表记录交易流水,字段含 order_id/amount/created_at'),
        ]
        embed_texts = [q if t == 'qa' else c for t, q, c in kb]  # QA embed 问题,chunk embed 内容
        vecs = client.embed(embed_texts)
        store.ensure_index(len(vecs[0]))
        es_docs, rows = [], []
        for (t, q, c), vec in zip(kb, vecs):
            cid = uuid.uuid4().hex
            text = q if t == 'qa' else c
            es_docs.append({'chunk_id': cid, 'content': text, 'content_vector': vec, 'tenant_id': str(TENANT),
                            'dataset_id': ds.id, 'document_id': 'manual', 'chunk_type': t,
                            **({'question': q} if t == 'qa' else {})})
            rows.append(RagChunk(id=cid, dataset_id=ds.id, document_id='manual', chunk_type=t,
                                 content=(None if t == 'qa' else c), question=(q if t == 'qa' else None),
                                 answer=(c if t == 'qa' else None),
                                 question_hash=(md5(q) if t == 'qa' else None), hash=md5(text),
                                 position=0, status=1, create_time=datetime.now()))
        store.add(es_docs)
        for r in rows:
            db.add(r)
        db.commit()
        check('灌入 2 条知识', store.count(filters=[{'term': {'tenant_id': str(TENANT)}}]) >= 2)

        # 3. 关键:按 source_id 走 search_knowledge_base(取数分析时的调用方式)
        print('== search_knowledge_base(source_id=...) ==')
        txt1 = search_knowledge_base('这个数据源是干嘛的', source_id=src.id, tenant_id=TENANT, top_k=3)
        check('按 source_id 召回到内容', len(txt1) > 10 and '数据源' in txt1, txt1[:50].replace('\n', ' '))
        txt2 = search_knowledge_base('orders 表有哪些字段', source_id=src.id, tenant_id=TENANT, top_k=3)
        check('召回 orders 表知识', 'orders' in txt2 or 'order_id' in txt2, txt2[:50].replace('\n', ' '))

        # 4. 闭包工具(Agent 用)
        tool = make_kb_tool(source_id=src.id, tenant_id=TENANT)
        txt3 = tool('交易流水记录在哪')
        check('make_kb_tool 闭包可用', len(txt3) > 10, txt3[:40].replace('\n', ' '))

        # 5. 不存在知识的源 → 空
        empty = search_knowledge_base('随机问题xyz', source_id='nonexistent-source', tenant_id=TENANT)
        check('未知数据源返回提示', '未找到' in empty or '未检索' in empty, empty[:30])

        return 0 if FAIL == 0 else 1
    finally:
        if created:  # 仅清理本次新建的专属库
            try:
                ds = db.execute(select(RagDataset).where(RagDataset.id == created)).scalars().first()
                if ds:
                    build_store(ds).drop()
                db.execute(RagChunk.__table__.delete().where(RagChunk.dataset_id == created))
                db.execute(RagDataset.__table__.delete().where(RagDataset.id == created))
                db.commit()
            except Exception as e:
                print('cleanup:', e)
        RequestContext.reset_current_tenant_id(token)
        db.close()
        print(f'\n== 结果:{PASS} passed, {FAIL} failed ==')


if __name__ == '__main__':
    sys.exit(main())
