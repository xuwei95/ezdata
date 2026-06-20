"""批量导入功能验证:QA/分段 CSV → 入库 → 召回。需 ES8 + DB + DashScope。"""

import sys
import uuid
from datetime import datetime

from sqlalchemy import select

from common.context import RequestContext
from config.env import RagConfig
from config.get_db import init_create_table  # noqa: F401  (确保表存在的副作用在 async 不便,这里假定已建)
from module_rag.bulk_import import bulk_import_from_file
from module_rag.entity.do.rag_do import RagChunk, RagDataset
from module_rag.retrieval import retrieve
from module_rag.runtime_util import build_store
from module_task_schedule.sync_db import get_sync_session_local
from utils.storage_utils import storage

TENANT = 100
PASS = FAIL = 0


def check(label, cond, detail=''):
    global PASS, FAIL
    ok = bool(cond); PASS += ok; FAIL += (not ok)
    print(f'  [{"PASS" if ok else "FAIL"}] {label}' + (f' — {detail}' if detail else ''))


def main():
    token = RequestContext.set_current_tenant_id(TENANT)
    db = get_sync_session_local()()
    ds_id = uuid.uuid4().hex
    try:
        db.add(RagDataset(id=ds_id, name='bulk-test', embedding_provider=RagConfig.embedding_type,
                          embedding_model=RagConfig.embedding_model, vector_backend='elasticsearch',
                          index_name=f'rag_ds_{ds_id}', status=1, create_time=datetime.now()))
        db.commit()

        qa_csv = 'question,answer\n公司年假有几天,每年15天带薪年假\n试用期多长,试用期为3个月\n'.encode('utf-8')
        ch_csv = 'content\nezdata 数据集成基于 dlt 实现抽取与加载\n知识库向量库默认使用 ES8 的 kNN\n'.encode('utf-8')
        storage.save('upload/_bulk_qa.csv', qa_csv)
        storage.save('upload/_bulk_chunk.csv', ch_csv)

        r1 = bulk_import_from_file(ds_id, 'qa', 'upload/_bulk_qa.csv', TENANT)
        check('QA 导入 2 条', r1.get('imported') == 2, str(r1))
        r2 = bulk_import_from_file(ds_id, 'chunk', 'upload/_bulk_chunk.csv', TENANT)
        check('分段 导入 2 条', r2.get('imported') == 2, str(r2))

        qa = retrieve(TENANT, '公司年假有几天', [ds_id], k=3, retrieval_type='hybrid')
        check('QA 召回命中', any(x['chunk_type'] == 'qa' for x in qa['records']),
              str([x['chunk_type'] for x in qa['records']]))
        ch = retrieve(TENANT, 'ES8 向量检索', [ds_id], k=3, retrieval_type='vector')
        check('分段 向量召回命中', ch['total'] > 0, f"{ch['total']} 条")

        # 分数阈值过滤(高阈值应过滤掉弱匹配)
        hi = retrieve(TENANT, '完全不相关的随机内容xyz', [ds_id], k=5, retrieval_type='vector', score_threshold=0.9)
        check('高分数阈值过滤生效', hi['total'] == 0, f"{hi['total']} 条")
    finally:
        try:
            build_store(db.execute(select(RagDataset).where(RagDataset.id == ds_id)).scalars().first()).drop()
            db.execute(RagChunk.__table__.delete().where(RagChunk.dataset_id == ds_id))
            db.execute(RagDataset.__table__.delete().where(RagDataset.id == ds_id))
            db.commit()
        except Exception as e:
            print('cleanup:', e)
        RequestContext.reset_current_tenant_id(token)
        db.close()
        print(f'\n== 结果:{PASS} passed, {FAIL} failed ==')
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
