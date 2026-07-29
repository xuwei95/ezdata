"""BIRD-dev × 真实 module_rag 全链路评测(容器内跑,放 /app 根避开 9P 抽风目录扫描)。

尽量贴 agent 流程:把"已验证解法(Q→gold SQL)"灌进真知识库(RagDataset,siliconflow bge-m3
→ ES8),用真 retrieve()(hybrid 语义+关键词)取相似解法作 few-shot,叠加库表结构后生成 SQL、执行判分。

跑:MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml run --rm --no-deps -w /app \
      ezdata-backend-dev python _bird_rag_eval.py [总题数] [smoke]
"""
import asyncio
import json
import logging
import os
import random
import sqlite3
import sys
import time

logging.disable(logging.INFO)

_BIRD = '/app/evals/bench/bird_dev/dev_20240627'
_DEV = f'{_BIRD}/dev.json'
_DBDIR = f'{_BIRD}/dev_databases'
TENANT = 100
QUOTA = {'simple': 22, 'moderate': 16, 'challenging': 12}
POOL_CAP = 80  # 每库灌入的已验证解法上限(够检索即可,控制入库耗时)


def _dbp(db_id):
    return f'{_DBDIR}/{db_id}/{db_id}.sqlite'


def _norm_cell(v):
    if v is None:
        return ''
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        r = round(v, 2)
        return str(int(r)) if r == int(r) else f'{r:.2f}'
    s = str(v).strip()
    try:
        f = float(s)
        r = round(f, 2)
        return str(int(r)) if r == int(r) else f'{r:.2f}'
    except ValueError:
        return s


def _rows_strict(rows):
    return sorted([tuple(_norm_cell(c) for c in row) for row in rows])


def _gold_rows(db_id, sql):
    con = sqlite3.connect(_dbp(db_id))
    try:
        return [tuple(r) for r in con.execute(sql).fetchall()]
    finally:
        con.close()


def _sample(items, total):
    random.seed(42)
    by = {}
    for it in items:
        by.setdefault(it.get('difficulty', 'simple'), []).append(it)
    scale = (total / sum(QUOTA.values())) if total else 1
    quota = {k: max(1, round(v * scale)) for k, v in QUOTA.items()}
    picked = []
    for tier, n in quota.items():
        pool = by.get(tier, [])
        random.shuffle(pool)
        picked.extend(pool[:n])
    return picked


async def _ensure_kb(db, DatasetService, ChunkService, DatasetCreateReq, ChunkSaveReq, RagDataset, select, db_id, pool, tag):
    """建/复用该库的知识库,并灌入 QA 解法(已存在则复用)。库名带样本量 tag → pool 已排除该样本,天然无泄漏。"""
    name = f'bird{tag}_{db_id}'
    exist = (await db.execute(select(RagDataset).where(RagDataset.name == name))).scalars().first()
    if exist:
        did = exist.id
        cnt = exist.chunk_count if hasattr(exist, 'chunk_count') else None
        # 有就复用(避免重复灌);chunk 数未知时也直接复用
        return did, 0
    ds = await DatasetService.create(db, DatasetCreateReq(name=name, description=f'BIRD {db_id} 已验证解法库'), 'admin')
    did = ds.get('id') or ds.get('datasetId')
    n = 0
    for it in pool.get(db_id, [])[:POOL_CAP]:
        q = it['question'] + (f'(提示:{it["evidence"]})' if it.get('evidence') else '')
        await ChunkService.save(db, ChunkSaveReq(dataset_id=did, chunk_type='qa', question=q, answer=it['SQL']), 'admin')
        n += 1
    await db.commit()
    return did, n


async def main():
    args = sys.argv[1:]
    smoke = 'smoke' in args
    norag = 'norag' in args  # 同模型单次基线(不建库/不检索),做干净对比
    nums = [a for a in args if a.isdigit()]
    total = int(nums[0]) if nums else (8 if smoke else 50)

    # 9P 挂载偶发返回不完整目录列表 → import 随机 ModuleNotFoundError/OSError;带缓存失效重试自愈
    # 9P 挂载偶发返回不完整目录列表 → import 随机 ModuleNotFoundError/OSError;带缓存失效重试自愈
    import importlib

    for attempt in range(12):
        try:
            from sqlalchemy import select

            from common.context import RequestContext
            from config.database import AsyncSessionLocal
            from ezdata import services
            from ezdata.interface.web.core import Core
            from ezdata.interface.web.llm import LLMClient, strip_code_fence
            from ezdata.services import prompts
            from ezdata.utils.etl_util import json_safe_rows
            from module_rag.entity.do.rag_do import RagDataset
            from module_rag.entity.vo.rag_vo import ChunkSaveReq, DatasetCreateReq
            from module_rag.retrieval import retrieve
            from module_rag.service.chunk_service import ChunkService
            from module_rag.service.dataset_service import DatasetService

            break
        except (ModuleNotFoundError, OSError, ImportError) as e:
            print(f'[import 重试 {attempt + 1}] {type(e).__name__}: {e}')
            for m in list(sys.modules):  # 清掉 9P 报错留下的半成品包,否则子模块永远找不到
                if m.split('.')[0] in ('module_rag', 'module_admin', 'ezdata', 'common', 'config'):
                    sys.modules.pop(m, None)
            importlib.invalidate_caches()
            time.sleep(2)
    else:
        raise RuntimeError('app imports 多次重试仍失败(9P 挂载不健康)')

    RequestContext.set_current_tenant_id(TENANT)
    items = json.load(open(_DEV, encoding='utf-8'))
    sample = _sample(items, total)
    if smoke:
        sample = sample[:8]
    sample_ids = {it['question_id'] for it in sample}
    pool = {}
    for it in items:
        if it['question_id'] not in sample_ids:
            pool.setdefault(it['db_id'], []).append(it)

    llm = LLMClient()
    mode = 'norag 单次基线' if norag else '真RAG 全链路'
    print(f'BIRD×{mode} | 模型 {llm.cfg.get("model")} | emb {os.environ.get("EMBEDDING_MODEL", "?")} | 抽样 {len(sample)} | 每库灌≤{POOL_CAP}')

    # ---- 灌库(真 module_rag:embed→ES);库名带样本量 tag,pool 已排除该样本 → 无泄漏、可复用 ----
    kb = {}
    if not norag:
        async with AsyncSessionLocal() as db:
            for db_id in sorted({it['db_id'] for it in sample}):
                did, n = await _ensure_kb(db, DatasetService, ChunkService, DatasetCreateReq, ChunkSaveReq, RagDataset, select, db_id, pool, len(sample))
                kb[db_id] = did
                print(f'  KB {db_id:24} -> {did} (灌入 {n} 条解法)')
    print('=' * 74)

    # ---- 评测:真 retrieve() 取 few-shot → 生成 → 执行判分 ----
    results = []
    for i, it in enumerate(sample):
        db_id, tier = it['db_id'], it.get('difficulty', 'simple')
        row = {'id': it['question_id'], 'tier': tier, 'db': db_id, 'strict': False, 'err': '', 'nhit': 0}
        try:
            gold = _gold_rows(db_id, it['SQL'])
        except Exception as e:
            row['err'] = f'GOLD:{e}'; results.append(row); continue
        t0 = time.time()
        try:
            # 1) 真检索:同库 hybrid 语义+关键词(norag 基线跳过)
            recs = []
            if not norag:
                try:
                    res = retrieve(TENANT, it['question'], [kb[db_id]], k=3, retrieval_type='hybrid')
                except Exception:
                    res = retrieve(TENANT, it['question'], [kb[db_id]], k=3, retrieval_type='vector')
                recs = [r for r in res.get('records', []) if r.get('chunk_type') == 'qa']
            row['nhit'] = len(recs)
            fs = ''
            if recs:
                lines = ['参考(该数据源上已验证的相似问题 → 正确查询,模仿其口径/选表选列/join):']
                for r in recs:
                    lines.append(f'问题:{r.get("question")}\nSQL:{r.get("answer")}')
                fs = '\n'.join(lines) + '\n\n'
            # 2) schema(sqlite handler)+ few-shot + 问题 → 生成
            st, cfg, sec = 'sqlite', {'db_file': _dbp(db_id)}, {}
            h = services.get_handler(st, cfg, sec)
            q = it['question'] + (f'\n\n【外部知识提示】{it["evidence"]}' if it.get('evidence') else '')
            aug = fs + '【实际需求(仿照上面已验证示例的写法)】\n' + q
            prompt = prompts.build_query_prompt(h, None, aug)
            # 网关偶发 504/空/非 SQL(deepseek 抖动)→ 重试,别把网关问题记成答错
            sql = ''
            for _try in range(5):
                try:
                    raw = strip_code_fence(llm.complete(prompt) or '')
                except Exception:
                    time.sleep(2)
                    continue
                sql = Core._parse_statement(raw, getattr(h, 'family', ''))
                if sql and sql.lower().lstrip().startswith(('select', 'with')):
                    break
                time.sleep(2)
            row['stmt'] = sql
            # 3) 执行判分
            rows = json_safe_rows(services.query(st, cfg, sec, statement=sql, limit=100000))
            pred = [tuple(d.values()) for d in rows]
            row['strict'] = _rows_strict(gold) == _rows_strict(pred)
        except Exception as e:
            row['err'] = f'{type(e).__name__}: {str(e)[:80]}'
        row['ms'] = int((time.time() - t0) * 1000)
        results.append(row)
        mark = 'OK ' if row['strict'] else 'XX '
        print(f'[{i + 1:3}/{len(sample)}] {tier:11} {db_id:22} {mark} hit{row["nhit"]} {row["err"]}')

    print('=' * 74)
    n = len(results)
    s = sum(r['strict'] for r in results)
    print(f'BIRD-dev × {mode}({llm.cfg.get("model")}) EX(strict): {s}/{n} = {s / n * 100:.1f}%')
    for tier in ('simple', 'moderate', 'challenging'):
        sub = [r for r in results if r['tier'] == tier]
        if sub:
            print(f'  {tier:12}: {sum(r["strict"] for r in sub)}/{len(sub)} = {sum(r["strict"] for r in sub) / len(sub) * 100:.0f}%')
    fn = '/app/evals/bench/_bird_norag_run.json' if norag else '/app/evals/bench/_bird_rag_run.json'
    json.dump(results, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=2, default=str)
    print('明细已写:', fn)


if __name__ == '__main__':
    asyncio.run(main())
