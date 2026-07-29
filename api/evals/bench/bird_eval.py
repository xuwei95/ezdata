"""BIRD-dev 执行准确率(EX)—— 国际公认硬基准,可对标排行榜口径。

- 数据:BIRD dev(1534 题 / 11 库 / simple·moderate·challenging),每题带 evidence(外部知识)。
- 打法:与官方一致,把 evidence 一并喂模型;NL→SQL→执行,与 gold SQL 执行结果集比对。
- 抽样:固定种子分层抽 N 题(默认 simple22/moderate16/challenging12=50),可复现。

跑:python evals/bench/bird_eval.py [总题数]
"""

import json
import os
import random
import sqlite3
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_API = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _API)
sys.path.insert(0, _HERE)

from ezdata import services  # noqa: E402
from ezdata.interface.web import ConnectionStore, Core, LLMClient, config  # noqa: E402
from ezdata.interface.web.core import Core as _CoreCls  # noqa: E402
from ezdata.interface.web.llm import strip_code_fence  # noqa: E402
from ezdata.services import prompts  # noqa: E402
from ezdata.utils.etl_util import json_safe_rows  # noqa: E402
from text2sql_eval import _rows_lenient, _rows_strict  # noqa: E402  复用比对逻辑


def ask_retry(core, name, question, max_retry=2, limit=100000):
    """自纠版 NL→SQL:生成→执行,若报错/空结果则把反馈喂回让模型修正,最多 max_retry 次。"""
    st, cfg, sec = core.store.resolve(name)
    h = services.get_handler(st, cfg, sec)
    family = getattr(h, 'family', '')
    base = prompts.build_query_prompt(h, None, question)
    prompt = base
    last_sql = None
    for attempt in range(max_retry + 1):
        sql = _CoreCls._parse_statement(strip_code_fence(core.llm.complete(prompt)), family)
        last_sql = sql
        fb = None
        try:
            rows = json_safe_rows(services.query(st, cfg, sec, statement=sql, limit=limit))
            if rows or attempt == max_retry:
                return {'statement': sql, 'rows': rows, 'attempts': attempt + 1}
            fb = '执行成功但返回 0 行,请检查表/列/过滤条件是否选对'
        except Exception as e:
            if attempt == max_retry:
                raise
            fb = f'执行报错:{type(e).__name__}: {str(e)[:200]}'
        prompt = base + (
            f'\n\n【你上一次的查询】\n{sql}\n【执行反馈】{fb}\n请据此修正,只输出修正后的单条只读查询。'
        )
    return {'statement': last_sql, 'rows': [], 'attempts': max_retry + 1}

_BIRD = os.path.join(_HERE, 'bird_dev', 'dev_20240627')
_DEV_JSON = os.path.join(_BIRD, 'dev.json')
_DB_DIR = os.path.join(_BIRD, 'dev_databases')

# 分层抽样配额(可被命令行总数近似覆盖)
QUOTA = {'simple': 22, 'moderate': 16, 'challenging': 12}


def _db_path(db_id):
    return os.path.join(_DB_DIR, db_id, f'{db_id}.sqlite')


def _build_pool(items, sample_ids):
    """已验证解法库:除测试样本外的题,按 db_id 归组(模拟"收藏解法"沉淀)。"""
    pool = {}
    for it in items:
        if it['question_id'] in sample_ids:
            continue
        pool.setdefault(it['db_id'], []).append(it)
    return pool


_EC = None
_SEM_INDEX = {}  # db_id -> (归一化向量矩阵, items)


def _emb_client():
    global _EC
    if _EC is None:
        from ezdata.interface.web import config as w
        from module_rag.embedding import EmbeddingClient

        _EC = EmbeddingClient(
            provider=w.get('EMBEDDING_TYPE', 'dashscope'),
            model=w.get('EMBEDDING_MODEL'),
            api_key=w.get('EMBEDDING_API_KEY') or w.get('DASHSCOPE_API_KEY'),
            base_url=(w.get('EMBEDDING_URL') or None),
        )
    return _EC


def _sem_prepare(pool):
    """把已验证解法库按 db_id 向量化(项目同款 embedding 模型),建归一化矩阵供余弦检索。"""
    import numpy as np

    ec = _emb_client()
    for db_id, items in pool.items():
        texts = [it['question'] for it in items]
        vecs = []
        for i in range(0, len(texts), 64):
            vecs.extend(ec.embed(texts[i : i + 64]))
        m = np.asarray(vecs, dtype='float32')
        m /= np.linalg.norm(m, axis=1, keepdims=True) + 1e-9
        _SEM_INDEX[db_id] = (m, items)


def _fewshot_block_sem(it, k=3):
    """语义检索(与真实 RAG 同款 bge-m3 向量 + 余弦)取同库 top-k 已验证解法作示范。"""
    import numpy as np

    idx = _SEM_INDEX.get(it['db_id'])
    if not idx:
        return ''
    m, items = idx
    q = np.asarray(_emb_client().embed_query(it['question']), dtype='float32')
    q /= np.linalg.norm(q) + 1e-9
    top = np.argsort(-(m @ q))[:k]
    lines = ['参考(该数据源上已验证的相似问题 → 正确查询,请模仿其口径/选表选列/join 写法):']
    for j in top:
        c = items[int(j)]
        ev = f'(提示:{c["evidence"]})' if c.get('evidence') else ''
        lines.append(f'问题:{c["question"]}{ev}\nSQL:{c["SQL"]}')
    return '\n'.join(lines) + '\n\n'


def _fewshot_block(it, pool, k=3):
    """检索同库最相似的 k 条已验证(问题→gold SQL),拼成示范。词面相似(difflib),可复现、无需 embedding。"""
    import difflib

    cands = pool.get(it['db_id'], [])
    if not cands:
        return ''
    q = it['question']
    top = sorted(cands, key=lambda c: difflib.SequenceMatcher(None, q, c['question']).ratio(), reverse=True)[:k]
    lines = ['参考(该数据源上已验证的相似问题 → 正确查询,请模仿其口径/选表选列/join 写法):']
    for c in top:
        ev = f'(提示:{c["evidence"]})' if c.get('evidence') else ''
        lines.append(f'问题:{c["question"]}{ev}\nSQL:{c["SQL"]}')
    return '\n'.join(lines) + '\n\n'


def _gold_rows(db_id, sql):
    con = sqlite3.connect(_db_path(db_id))
    try:
        return [tuple(r) for r in con.execute(sql).fetchall()]
    finally:
        con.close()


def _sample(items, total):
    random.seed(42)
    by = {}
    for it in items:
        by.setdefault(it.get('difficulty', 'simple'), []).append(it)
    picked = []
    if total:  # 命令行给了总数:按 QUOTA 比例缩放
        scale = total / sum(QUOTA.values())
        quota = {k: max(1, round(v * scale)) for k, v in QUOTA.items()}
    else:
        quota = QUOTA
    for tier, n in quota.items():
        pool = by.get(tier, [])
        random.shuffle(pool)
        picked.extend(pool[:n])
    return picked


def main():
    args = [a for a in sys.argv[1:]]
    retry = 'retry' in args
    semantic = 'semantic' in args
    fewshot = 'fewshot' in args or semantic
    nums = [a for a in args if a.isdigit()]
    total = int(nums[0]) if nums else 0
    items = json.load(open(_DEV_JSON, encoding='utf-8'))
    sample = _sample(items, total)
    pool = _build_pool(items, {it['question_id'] for it in sample}) if fewshot else {}
    if semantic:
        print('向量化已验证解法库(bge-m3)...')
        _sem_prepare(pool)

    store = ConnectionStore(os.path.join(_HERE, '_bird_store.db'))
    core = Core(store, LLMClient(config.llm_config()))
    for db_id in sorted({it['db_id'] for it in sample}):
        if not store.get(db_id):
            store.add(db_id, 'sqlite', {'db_file': _db_path(db_id)}, {})

    mode = (
        '自纠(execute+retry×2)' if retry
        else 'few-shot·语义检索(bge-m3×3)' if semantic
        else 'few-shot·词面(difflib×3)' if fewshot
        else '单次(single-shot)'
    )
    print(f'BIRD-dev | 模型 {core.llm.cfg.get("model")} | 抽样 {len(sample)} 题 | 模式 {mode}')
    print('=' * 74)
    results = []
    for i, it in enumerate(sample):
        cid, tier, db_id = it['question_id'], it.get('difficulty', 'simple'), it['db_id']
        row = {'id': cid, 'tier': tier, 'db': db_id, 'strict': False, 'lenient': False, 'err': ''}
        try:
            gold = _gold_rows(db_id, it['SQL'])
        except Exception as e:
            row['err'] = f'GOLD:{e}'
            results.append(row)
            continue
        q = it['question']
        if it.get('evidence'):
            q += f'\n\n【外部知识提示】{it["evidence"]}'
        if fewshot:
            block = _fewshot_block_sem(it) if semantic else _fewshot_block(it, pool)
            q = block + '【实际需求(仿照上面已验证示例的写法)】\n' + q
        t0 = time.time()
        try:
            r = ask_retry(core, db_id, q, limit=100000) if retry else core.ask(db_id, q, tables=None, limit=100000)
            pred = [tuple(d.values()) for d in (r.get('rows') or [])]
            row['strict'] = _rows_strict(gold) == _rows_strict(pred)
            row['lenient'] = _rows_lenient(gold) == _rows_lenient(pred)
            row['stmt'] = r.get('statement')
            row['attempts'] = r.get('attempts', 1)
        except Exception as e:
            row['err'] = f'{type(e).__name__}: {str(e)[:80]}'
        row['ms'] = int((time.time() - t0) * 1000)
        results.append(row)
        mark = 'OK ' if row['strict'] else ('~L ' if row['lenient'] else 'XX ')
        att = f' x{row.get("attempts", 1)}' if retry else ''
        print(f'[{i + 1:2}/{len(sample)}] {tier:11} {db_id:22} {mark}{att} {row["err"]}')

    print('=' * 74)
    n = len(results)
    strict = sum(r['strict'] for r in results)
    lenient = sum(r['lenient'] for r in results)
    print(f'BIRD-dev EX(strict): {strict}/{n} = {strict / n * 100:.1f}%')
    print(f'BIRD-dev EX(lenient 列序无关): {lenient}/{n} = {lenient / n * 100:.1f}%')
    for tier in ('simple', 'moderate', 'challenging'):
        sub = [r for r in results if r['tier'] == tier]
        if sub:
            s = sum(r['strict'] for r in sub)
            print(f'  {tier:12}: {s}/{len(sub)} = {s / len(sub) * 100:.0f}%')
    tag = 'retry' if retry else ('semantic' if semantic else 'fewshot' if fewshot else 'single')
    out = os.path.join(_HERE, f'_bird_{tag}_run.json')
    json.dump(results, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2, default=str)
    print(f'明细已写: {out}')


if __name__ == '__main__':
    main()
