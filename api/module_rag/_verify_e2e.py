"""
知识库端到端测试(服务层,真实 DB + ES8 + DashScope embedding)。

流程:建库 → 加文本文档 → 训练(抽取/清洗/切分/向量化/入库)→ 召回(向量/全文/混合)
      → 加 QA → QA 命中 → 清理。

前置:dev DB 可用、ES8 在 RAG_VECTOR_HOSTS、DashScope key 有效(均取自 .env.dev)。
运行:cd api && python -m module_rag._verify_e2e
"""

import asyncio
import sys

from common.context import RequestContext
from config.database import AsyncSessionLocal
from config.get_db import init_create_table
from module_rag.entity.vo.rag_vo import ChunkSaveReq, DatasetCreateReq, DocumentCreateReq
from module_rag.pipeline import train_document
from module_rag.retrieval import retrieve
from module_rag.service.chunk_service import ChunkService
from module_rag.service.dataset_service import DatasetService
from module_rag.service.document_service import DocumentService

TENANT = 100

LONG_TEXT = """
ezdata 是一个 AI 原生的数据平台,核心能力包括数据源管理、数据模型、ETL 数据集成与任务调度。
数据集成基于 dlt(data load tool)实现,支持 MySQL、Elasticsearch、MongoDB、Kafka 等多种数据源的抽取与加载。
任务调度模块提供普通任务调度与任务工作流(DAG),DAG 采用 AntV X6 画布编辑,事件驱动编排,支持分布式与单机两种运行模式。
知识库模块提供 RAG 检索增强:文档经过抽取、清洗、切分、向量化后写入向量库,检索时支持向量召回、全文召回与混合检索,并可选 rerank 重排。
向量库默认使用 ES8,利用其原生 dense_vector 与 kNN 能力,同时承担日志存储与数据服务,实现一套 Elasticsearch 三种用途。
员工福利方面,公司提供每年 15 天带薪年假,以及补充医疗保险。
""".strip()

PASS, FAIL = 0, 0


def check(label, cond, detail=''):
    global PASS, FAIL
    ok = bool(cond)
    PASS += ok
    FAIL += (not ok)
    print(f'  [{"PASS" if ok else "FAIL"}] {label}' + (f' — {detail}' if detail else ''))


async def main() -> int:
    await init_create_table()
    token = RequestContext.set_current_tenant_id(TENANT)
    ds_id = doc_id = None
    try:
        # 1. 建库 + 文本文档(不自动训练,测试里同步训练以便确定性)
        async with AsyncSessionLocal() as db:
            ds_id = (await DatasetService.create(
                db, DatasetCreateReq(name='e2e-kb', vector_backend='elasticsearch',
                                     remark='端到端测试库'), 'tester'))['id']
            doc_id = (await DocumentService.create(
                db, DocumentCreateReq(dataset_id=ds_id, name='doc-平台介绍', document_type='text',
                                      text=LONG_TEXT, auto_train=False,
                                      chunk_strategy={'chunk_size': 180, 'chunk_overlap': 40}), 'tester'))['id']
        check('建库 + 建文档', ds_id and doc_id, f'ds={ds_id[:8]} doc={doc_id[:8]}')

        # 2. 训练(同步)
        print('== 训练(抽取→清洗→切分→向量化→入库)==')
        res = train_document(doc_id, TENANT)
        check('训练成功', res.get('ok'), str(res))
        check('产出分段 >0', res.get('chunks', 0) > 0, f'chunks={res.get("chunks")}')

        # 3. 三种检索
        print('== 检索 ==')
        for mode in ('vector', 'keyword', 'hybrid'):
            out = retrieve(TENANT, 'ETL 数据集成用什么实现', [ds_id], k=3, retrieval_type=mode)
            check(f'{mode} 召回命中', out['total'] > 0, f'{out["total"]} 条')
            if mode == 'hybrid' and out['records']:
                top = out['records'][0]['content'] or ''
                check('hybrid top 命中 dlt 相关', 'dlt' in top or 'ETL' in top or '集成' in top, top[:40])

        # 4. 租户隔离:错误租户应召回 0
        wrong = retrieve(999, 'ETL', [ds_id], k=3, retrieval_type='vector')
        check('错误租户召回 0', wrong['total'] == 0)

        # 5. QA 命中
        print('== QA ==')
        async with AsyncSessionLocal() as db:
            await ChunkService.save(db, ChunkSaveReq(
                dataset_id=ds_id, chunk_type='qa', question='公司年假有几天',
                answer='公司提供每年 15 天带薪年假'), 'tester')
        qa = retrieve(TENANT, '公司年假有几天', [ds_id], k=3, retrieval_type='hybrid')
        check('QA 精确命中', any(r['chunk_type'] == 'qa' for r in qa['records']),
              str([r['chunk_type'] for r in qa['records']]))

        return 0 if FAIL == 0 else 1
    finally:
        # 清理
        if ds_id:
            async with AsyncSessionLocal() as db:
                try:
                    await DatasetService.delete(db, ds_id)
                except Exception as e:  # noqa: BLE001
                    print('  清理失败:', e)
        RequestContext.reset_current_tenant_id(token)
        print(f'\n== 结果:{PASS} passed, {FAIL} failed ==')


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
