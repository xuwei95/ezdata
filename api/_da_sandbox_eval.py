"""InfiAgent-DABench × 真实项目沙箱(容器内跑,数据内联进 code 送 /python/run)。

为什么内联:项目沙箱 env 空、**禁文件**、每次全新隔离进程,benchmark 的 CSV 在 host/backend、
沙箱容器读不到 → host 端读表后把内容内联成 code 前导块(df 预载),LLM 只写"对 df 的分析代码",
拼接后经 sandbox_client.run_python 送**真沙箱**执行。这样执行路径与生产代码沙箱完全一致
(同样禁文件/隔离/超时),比 da_eval.py 的主机子进程 exec 更端到端;也让"手册/上下文"消融变真
(沙箱里代码没法自己 open() 读文件补信息)。

对照:da_eval.py(主机子进程,快、可读文件、非生产路径)| 本脚本(真沙箱,内联、禁文件、生产路径)。

跑:MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml run --rm --no-deps -w /app \
      ezdata-backend-dev python _da_sandbox_eval.py [N]

限制:内联把 CSV 文本塞进请求体,大表(>~2MB)跳过并计为 skip(不算错);DABStep 的 23MB 语料
不走内联(需挂卷进沙箱容器),本脚本只覆盖 InfiAgent。
"""

import io  # noqa: F401 (保留:未来内联路径可能用)
import json
import os
import random
import re
import sys
import time

import pandas as pd  # backend 侧:读表 + 净化为 records(沙箱侧的 pandas 在内联 code 里 import)

_INFI = '/app/evals/bench/infiagent_src/examples/DA-Agent/data'
_TABLES = f'{_INFI}/da-dev-tables'
_MAX_INLINE = 2_000_000  # CSV 文本超过则跳过内联(请求体/沙箱超时约束)

# DABStep:语料已随 ./api:/app:ro 挂进沙箱,大数据文件让代码用 pandas 直接读(沙箱禁 open()/io,但 pd.read_* 的 C 层放行);
# 手册/readme 是纯文本,open() 读不了 → host 端内联进 prompt。路径 backend/sandbox 一致(都挂 /app)。
_DABSTEP = '/app/evals/bench/dabstep'
_DAB_CTX = f'{_DABSTEP}/context'

_AT_RE = re.compile(r'@(\w+)\s*\[\s*([^\]]*?)\s*\]')


def _parse_ats(text):
    return {k: v.strip() for k, v in _AT_RE.findall(text or '')}


def _as_float(s):
    try:
        return float(str(s).replace(',', '').replace('%', '').strip())
    except (ValueError, TypeError):
        return None


def _val_eq(pred, gold, tol_abs=0.01, tol_rel=0.01):
    fa, fb = _as_float(pred), _as_float(gold)
    if fa is not None and fb is not None:
        return abs(fa - fb) <= max(tol_abs, tol_rel * max(abs(fa), abs(fb)) + 1e-9)
    na = re.sub(r'\s+', ' ', str(pred).strip().lower().rstrip('.'))
    nb = re.sub(r'\s+', ' ', str(gold).strip().lower().rstrip('.'))
    return na == nb


def _extract_code(raw):
    t = (raw or '').strip()
    m = re.search(r'```(?:python|py)?\s*\n(.*?)```', t, re.S)
    if m:
        return m.group(1).strip()
    if t.startswith('```'):
        t = '\n'.join(t.splitlines()[1:])
        if t.rstrip().endswith('```'):
            t = t.rstrip()[:-3]
    return t.strip()


def _prompt(q, file_path, columns):
    return f"""你是数据分析专家。用 Python(pandas/numpy)解决下面的数据分析问题。

数据文件:{file_path}
沙箱禁用 open()/io,请用 `pd.read_csv({file_path!r})` 读取。该表的列:{columns}

【问题】{q['question']}

【约束】{q.get('constraints', '')}

【输出格式(必须严格遵守)】
{q['format']}

要求:
1. 只输出一个 Python 代码片段(用 ```python 包裹),用 pd.read_csv 读上面文件。
2. **运行环境只有 pandas 和 numpy**——沙箱禁止 scipy / sklearn / statsmodels 等库(import 会失败)。
   相关系数用 `df['a'].corr(df['b'])`(Pearson)或 `method='spearman'`;回归/统计尽量用 pandas/numpy 手算(如最小二乘用 np.polyfit)。
3. 最后必须用 print 打印出符合【输出格式】的那一行,形如 @name[value],value 按要求四舍五入。
4. 除这一行外不要 print 其它内容;不要用 open()、不要重新造数据。"""


def _sample_infi(qs, n, seed=42):
    """固定种子按难度(easy/medium/hard)分层抽样,可复现、覆盖多表。"""
    random.seed(seed)
    by = {}
    for q in qs:
        by.setdefault(q.get('level', 'easy'), []).append(q)
    tot = len(qs)
    picked = []
    for lv in ('easy', 'medium', 'hard'):
        pool = by.get(lv, [])
        random.shuffle(pool)
        k = max(1, round(len(pool) / tot * n)) if n < tot else len(pool)
        picked.extend(pool[:k])
    return picked


def _llm_code(llm, prompt):
    """调 LLM 取代码,带网关抖动重试(504/路由/temperature 报错串不算有效输出)。返回抽取后的 code。"""
    raw = ''
    for _t in range(3):
        try:
            raw = llm.complete(prompt, temperature=None) or ''  # opus 弃 temperature,走 openai 分支须置空
            if raw.strip() and not raw.strip().startswith(('`temperature', 'Not Found', 'Route ')):
                break
        except Exception:
            time.sleep(2)
    return _extract_code(raw)


def eval_infiagent(llm, sandbox_client, n):
    qs = [json.loads(l) for l in open(f'{_INFI}/da-dev-questions.jsonl', encoding='utf-8')]
    labels = {json.loads(l)['id']: json.loads(l)['common_answers']
              for l in open(f'{_INFI}/da-dev-labels.jsonl', encoding='utf-8')}
    sample = _sample_infi(qs, n)  # 分层抽样(表也在 ./api:/app 挂载下,代码直接读,不再内联/跳大表)
    print(f'InfiAgent-DABench × 真沙箱 | 模型 {llm.cfg.get("model")} | 分层抽样 {len(sample)}/{len(qs)} 题 | 挂载路径读表')
    print('=' * 78)
    results = []
    for i, q in enumerate(sample):
        row = {'id': q['id'], 'level': q.get('level'), 'file': q['file_name'],
               'ok': False, 'err': '', 'attempts': 0}
        path = f'{_TABLES}/{q["file_name"]}'
        try:
            columns = list(pd.read_csv(path, nrows=1).columns)  # backend 侧取列名喂 prompt
        except Exception as e:
            row['err'] = f'READ:{e}'; results.append(row); print(f'[{i+1:2}] READ 失败 {e}'); continue

        prompt = _prompt(q, path, columns)
        pred, gold = {}, labels.get(q['id'], [])
        for attempt in range(2):  # 单次 + 报错自纠一次
            code = _llm_code(llm, prompt)
            try:
                res = sandbox_client.run_python(code, variable_to_return=None, timeout=120)
            except Exception as e:
                row['err'] = f'SANDBOX:{type(e).__name__}:{str(e)[:80]}'; break
            row['attempts'] = attempt + 1
            if res.get('success') and res.get('stdout'):
                pred = _parse_ats(res['stdout'])
                if pred:
                    break
            err = res.get('error') or '(无 stdout)'
            row['err'] = str(err)[:120]
            prompt = _prompt(q, path, columns) + f'\n\n【上次代码执行失败】{str(err)[:300]}\n请修正后重新只输出代码片段。'

        subs = [pred.get(name) is not None and _val_eq(pred.get(name), gval) for name, gval in gold]
        row['ok'] = bool(subs) and all(subs)
        row['pred'] = pred; row['gold'] = gold
        results.append(row)
        mark = 'OK ' if row['ok'] else 'XX '
        print(f'[{i+1:2}/{len(sample)}] {q.get("level",""):7} {q["file_name"][:22]:22} {mark} '
              f'gold={gold} pred={dict(pred)} {("| " + row["err"]) if not row["ok"] and row["err"] else ""}')

    _summary('InfiAgent-DABench', results, ('easy', 'medium', 'hard'), llm, '')
    _dump(results, '/app/evals/bench/_da_infiagent_sandbox_run.json')


# --------------------------- DABStep(共享语料,代码读挂载文件)---------------------------

def _dab_context_block():
    """规则手册/readme(小文本,沙箱禁 open() 读不了)→内联;大数据文件给结构预览,让代码用 pandas 从挂载路径读。"""
    parts = [f'【数据文件都在目录 {_DAB_CTX}/ 下。沙箱禁用 open()/io,请用 pandas 读取:'
             f'CSV 用 pd.read_csv("{_DAB_CTX}/xxx.csv"),JSON 用 pd.read_json(...);切勿用 open()。】\n']
    for f in ('payments.csv', 'merchant_category_codes.csv', 'acquirer_countries.csv'):
        p = f'{_DAB_CTX}/{f}'
        if os.path.exists(p):
            df = pd.read_csv(p, nrows=2)
            parts.append(f'--- {f} (列: {list(df.columns)}) ---\n{df.head(2).to_csv(index=False)}')
    for f in ('fees.json', 'merchant_data.json'):
        p = f'{_DAB_CTX}/{f}'
        if os.path.exists(p):
            try:
                d = json.load(open(p, encoding='utf-8'))
                sample = d[:1] if isinstance(d, list) else d
                kind = f'list,{len(d)} 条' if isinstance(d, list) else 'dict'
                parts.append(f'--- {f} ({kind}) 样例 ---\n{json.dumps(sample, ensure_ascii=False)[:800]}')
            except Exception:
                pass
    for f in ('manual.md', 'payments-readme.md'):
        p = f'{_DAB_CTX}/{f}'
        if os.path.exists(p):
            parts.append(f'--- {f}(全文,规则以此为准)---\n{open(p, encoding="utf-8").read()}')
    return '\n'.join(parts)


def _dab_prompt(task, ctx):
    return f"""你是数据分析专家。基于下面的共享数据语料,用 Python(pandas/numpy)回答问题。

{ctx}

【问题】{task['question']}

【回答规范】{task.get('guidelines', '')}

要求:
1. 只输出一个 Python 代码片段(用 ```python 包裹),用 pd.read_csv / pd.read_json 从上面目录读所需文件(禁 open()/io)。
2. 脚本最后只 print 出最终答案本身(严格遵守【回答规范】:要国家代码就只打印代码、要数字就打印数字,不带多余文字/单位/解释)。"""


def eval_dabstep(llm, sandbox_client, n):
    tasks = [json.loads(l) for l in open(f'{_DABSTEP}/dev.jsonl', encoding='utf-8')]
    sample = tasks[:n]
    ctx = _dab_context_block()
    print(f'DABStep(dev) × 真沙箱 | 模型 {llm.cfg.get("model")} | 抽样 {len(sample)}/{len(tasks)} 题 | 手册内联+大文件代码读 | ctx~{len(ctx)//1000}k')
    print('=' * 78)
    results = []
    for i, task in enumerate(sample):
        row = {'id': task['task_id'], 'level': task.get('level'), 'ok': False, 'skip': False, 'err': '', 'attempts': 0}
        prompt = _dab_prompt(task, ctx)
        gold = str(task['answer']).strip()
        pred = ''
        for attempt in range(2):
            code = _llm_code(llm, prompt)
            try:
                res = sandbox_client.run_python(code, variable_to_return=None, timeout=120)
            except Exception as e:
                row['err'] = f'SANDBOX:{type(e).__name__}:{str(e)[:80]}'; break
            row['attempts'] = attempt + 1
            if res.get('success') and res.get('stdout'):
                pred = (res['stdout'].splitlines() or [''])[-1].strip()
                if pred:
                    break
            err = res.get('error') or '(无 stdout)'
            row['err'] = str(err)[:120]
            prompt = _dab_prompt(task, ctx) + f'\n\n【上次代码执行失败】{str(err)[:300]}\n请修正后重新只输出代码片段。'
        row['ok'] = bool(pred) and _val_eq(pred, gold)
        row['pred'] = pred; row['gold'] = gold
        results.append(row)
        mark = 'OK ' if row['ok'] else 'XX '
        print(f'[{i+1:2}/{len(sample)}] {task.get("level",""):5} {mark} gold=[{gold[:40]}] pred=[{pred[:40]}] '
              f'{("| " + row["err"]) if not row["ok"] and row["err"] else ""}')

    _summary('DABStep(dev)', results, ('easy', 'hard'), llm, '')
    _dump(results, '/app/evals/bench/_da_dabstep_sandbox_run.json')


# --------------------------- 汇总 / 落盘 ---------------------------

def _summary(name, graded, tiers, llm, tail):
    print('=' * 78)
    ok = sum(r['ok'] for r in graded)
    ng = len(graded) or 1
    print(f'{name} × 真沙箱 准确率({llm.cfg.get("model")}): {ok}/{len(graded)} = {ok/ng*100:.1f}%  {tail}')
    for t in tiers:
        sub = [r for r in graded if r.get('level') == t]
        if sub:
            s = sum(r['ok'] for r in sub)
            print(f'  {t:8}: {s}/{len(sub)} = {s/len(sub)*100:.0f}%')


def _dump(results, out):
    json.dump(results, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2, default=str)
    print(f'明细已写: {out}')


def main():
    args = sys.argv[1:]
    mode = next((a for a in args if not a.isdigit()), 'infiagent')
    nums = [a for a in args if a.isdigit()]
    n = int(nums[0]) if nums else 10

    import importlib  # 9P 挂载偶发不完整目录列表 → import 随机失败;带缓存失效重试(同 _bird_rag_eval)
    for attempt in range(12):
        try:
            from ezdata.interface.web import LLMClient
            from module_data import sandbox_client
            break
        except (ModuleNotFoundError, OSError, ImportError) as e:
            print(f'[import 重试 {attempt + 1}] {type(e).__name__}: {e}')
            for m in list(sys.modules):
                if m.split('.')[0] in ('ezdata', 'module_data', 'common', 'config'):
                    sys.modules.pop(m, None)
            importlib.invalidate_caches()
            time.sleep(2)
    else:
        raise RuntimeError('app imports 多次重试仍失败(9P 挂载不健康)')

    if not sandbox_client.enabled():
        print('⚠️ SANDBOX_ENABLED 未开——本脚本要求真沙箱,请确认 compose 里 SANDBOX_ENABLED=true')
        return

    llm = LLMClient()
    if mode.startswith('dab'):
        eval_dabstep(llm, sandbox_client, n)
    else:
        eval_infiagent(llm, sandbox_client, n)


if __name__ == '__main__':
    main()
