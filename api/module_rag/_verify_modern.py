"""
现代化架构验证:Agno 语义切分 / 增量跳过 / agent 工具 / Contextual Retrieval。
需 ES8 + DB + DashScope(+ 可选 LLM)。运行:
  PYTHONIOENCODING=utf-8 DB_PORT=13306 DB_PASSWORD=root python -m module_rag._verify_modern
"""

import json
import sys
import uuid
from datetime import datetime

from sqlalchemy import select

from common.context import RequestContext
from config.env import RagConfig
from module_rag.agent_tools import search_knowledge_base
from module_rag.entity.do.rag_do import RagChunk, RagDataset, RagDocument
from module_rag.pipeline import train_document
from module_rag.processing import chunk_text
from module_rag.retrieval import retrieve
from module_rag.runtime_util import build_store
from module_task_schedule.sync_db import get_sync_session_local

TENANT = 100
PASS = FAIL = 0
DOC = ('公司每年提供15天带薪年假。' * 8 + '\n\n'
       '向量数据库采用 Elasticsearch 8,利用 dense_vector 做 kNN 近似检索。' * 8 + '\n\n'
       'ETL 数据集成基于 dlt 实现,支持 MySQL、ES、MongoDB、Kafka 的抽取与加载。' * 8)


def check(label, cond, detail=''):
    global PASS, FAIL
    ok = bool(cond); PASS += ok; FAIL += (not ok)
    print(f'  [{"PASS" if ok else "FAIL"}] {label}' + (f' — {detail}' if detail else ''))


def main():
    token = RequestContext.set_current_tenant_id(TENANT)
    db = get_sync_session_local()()
    ds_id = uuid.uuid4().hex
    doc_id = uuid.uuid4().hex
    try:
        # 0. 切分策略单测(不入库)
        print('== 切分策略 ==')
        for strat in ('recursive', 'fixed', 'document', 'semantic'):
            cs = chunk_text(DOC, strategy=strat, chunk_size=200, overlap=30)
            check(f'{strat} 切分产出', len(cs) >= 1, f'{len(cs)} 段')

        # 建库 + 文档(semantic 策略)
        db.add(RagDataset(id=ds_id, name='modern-test', embedding_provider=RagConfig.embedding_type,
                          embedding_model=RagConfig.embedding_model, vector_backend='elasticsearch',
                          index_name=f'rag_ds_{ds_id}', status=1, create_time=datetime.now()))
        db.add(RagDocument(id=doc_id, dataset_id=ds_id, name='平台说明', document_type='text',
                           meta_data=json.dumps({'text': DOC}, ensure_ascii=False),
                           chunk_strategy=json.dumps({'strategy': 'semantic', 'chunk_size': 300, 'chunk_overlap': 50}),
                           status=1, create_time=datetime.now()))
        db.commit()

        print('== 训练(语义切分)==')
        r1 = train_document(doc_id, TENANT)
        check('训练成功', r1.get('ok'), str(r1))
        check('语义策略生效', r1.get('strategy') == 'semantic', str(r1.get('strategy')))
        check('产出分段', r1.get('chunks', 0) > 0, f"{r1.get('chunks')} 段")

        print('== 增量跳过 ==')
        r2 = train_document(doc_id, TENANT)  # 原文未变 → 跳过
        check('未变跳过', r2.get('skipped') is True, str(r2))
        r3 = train_document(doc_id, TENANT, force=True)  # 强制重训
        check('force 强制重训(不跳过)', not r3.get('skipped'), str(r3))

        print('== 检索 + agent 工具 ==')
        out = retrieve(TENANT, '年假多少天', [ds_id], k=3, retrieval_type='hybrid')
        check('混合召回命中', out['total'] > 0, f"{out['total']} 条")
        txt = search_knowledge_base('ETL 用什么实现', dataset_ids=[ds_id], tenant_id=TENANT, top_k=3)
        check('agent 工具返回片段', ('dlt' in txt or 'ETL' in txt or '集成' in txt), txt[:60].replace('\n', ' '))

        print('== Contextual Retrieval(LLM 可达才生效,失败优雅降级)==')
        from config.env import AiConfig
        if AiConfig.enabled:
            doc2 = uuid.uuid4().hex
            db.add(RagDocument(id=doc2, dataset_id=ds_id, name='ctx', document_type='text',
                               meta_data=json.dumps({'text': DOC}, ensure_ascii=False),
                               chunk_strategy=json.dumps({'strategy': 'recursive', 'chunk_size': 200,
                                                          'chunk_overlap': 30, 'contextual': True}),
                               status=1, create_time=datetime.now()))
            db.commit()
            rc = train_document(doc2, TENANT)
            check('contextual 训练成功(降级也算成功)', rc.get('ok'), str(rc))
        else:
            print('  (跳过:未配置兜底 LLM)')

        return 0 if FAIL == 0 else 1
    finally:
        try:
            ds = db.execute(select(RagDataset).where(RagDataset.id == ds_id)).scalars().first()
            if ds:
                build_store(ds).drop()
            db.execute(RagChunk.__table__.delete().where(RagChunk.dataset_id == ds_id))
            db.execute(RagDocument.__table__.delete().where(RagDocument.dataset_id == ds_id))
            db.execute(RagDataset.__table__.delete().where(RagDataset.id == ds_id))
            db.commit()
        except Exception as e:
            print('cleanup:', e)
        RequestContext.reset_current_tenant_id(token)
        db.close()
        print(f'\n== 结果:{PASS} passed, {FAIL} failed ==')


if __name__ == '__main__':
    sys.exit(main())
