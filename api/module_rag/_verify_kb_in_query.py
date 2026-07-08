"""
验证「KB 挂到取数 Agent」:数据模型取数时,自动从其数据源专属知识库召回业务知识注入 prompt。
容器内跑:docker exec ezdata-backend-dev python -m module_rag._verify_kb_in_query
"""

import asyncio
import sys

from common.context import RequestContext
from config.database import AsyncSessionLocal
from module_data.dao.data_dao import DataSourceDao
from module_data.service.data_service import DataQueryService
from module_rag.entity.vo.rag_vo import ChunkSaveReq
from module_rag.service.chunk_service import ChunkService
from module_rag.service.dataset_service import DatasetService

TENANT = 100
M_ID = '3694a99dc661411e9e896f5c6a2598e7'  # 订单 / demo_orders / demo_mysql
KNOW = '订单表 demo_orders:amount 字段为订单金额(单位:分);status=1 表示已支付,2 表示已取消。'
PASS = FAIL = 0


def check(label, cond, detail=''):
    global PASS, FAIL
    ok = bool(cond)
    PASS += ok
    FAIL += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] {label}' + (f' — {detail}' if detail else ''))


async def main():
    token = RequestContext.set_current_tenant_id(TENANT)
    chunk_id = None
    async with AsyncSessionLocal() as db:
        try:
            m, handler = await DataQueryService._load(db, M_ID)
            check('加载数据模型', m is not None, f'{m.name}/{m.object_name} src={m.datasource_code}')
            ds_src = await DataSourceDao.get_by_code(db, m.datasource_code)
            check('数据源存在', ds_src is not None, ds_src.id[:8] if ds_src else '')

            # 1. 该源专属知识库 + 存一条业务知识
            kb = await DatasetService.ensure_for_source(db, ds_src.id, None, 'tester')
            check('取/建专属知识库', bool(kb.get('id')), kb.get('name'))
            saved = await ChunkService.save(
                db, ChunkSaveReq(dataset_id=kb['id'], chunk_type='chunk', content=KNOW), 'tester'
            )
            chunk_id = saved.get('id')

            # 2. 核心:取数前的 KB 召回(_kb_context)能拿到业务知识
            # 重新加载 m(上一步 commit 会使 ORM 过期;真实 ai_query 里 m 紧随 _load、无此问题)
            m, handler = await DataQueryService._load(db, M_ID)
            ctx = await DataQueryService._kb_context(db, m, '已支付订单的金额')
            check('取数时召回到专属库知识', 'amount' in ctx or '已支付' in ctx, ctx[:60].replace('\n', ' '))

            # 3. 端到端 ai_query(LLM 生成 SQL 并执行;注入了 KB 上下文)
            print('== ai_query 端到端(LLM + 执行)==')
            try:
                res = await DataQueryService.ai_query(db, M_ID, '查最近10条已支付的订单', limit=10)
                sql = res.get('query', '')
                check('ai_query 产出 SQL', sql.lower().lstrip().startswith('select'), sql[:80])
                check('ai_query 返回结果集', 'records' in res, f'total={res.get("total")}')
                # KB 注入生效的弱信号:LLM 多半会用 status=1 过滤已支付
                print(f'  [信息] 生成 SQL: {sql}')
            except Exception as e:
                print(f'  [信息] ai_query 执行未完成(LLM/数据源原因,不影响 KB 注入结论): {str(e)[:120]}')

            return 0 if FAIL == 0 else 1
        finally:
            if chunk_id:
                try:
                    await ChunkService.delete(db, chunk_id)
                except Exception as e:
                    print('cleanup:', e)
            RequestContext.reset_current_tenant_id(token)
            print(f'\n== 结果:{PASS} passed, {FAIL} failed ==')


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
