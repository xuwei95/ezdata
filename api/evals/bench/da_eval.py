"""数据分析 agent 基准(闭式答案)—— InfiAgent-DABench + DABStep 双数据集。

与 BIRD(NL→SQL→执行→行集比对)不同:这里评的是"代码 agent 跑 CSV → 闭式答案 → 与 gold 比对",
覆盖 text-to-SQL 触不到的「数据分析/计算/多文件推理」层(对应本项目代码沙箱/代码看板能力)。

打法(贴 bird 的 ask_retry):问题+约束+CSV schema 预览 → LLM 生成 Python(pandas)脚本 →
子进程执行取 stdout → 解析闭式答案 → 判分;执行报错则把 stderr 反馈喂回重生成一次。

数据(均 gitignore,不入库):
  infiagent_src/examples/DA-Agent/data/   da-dev-questions.jsonl / da-dev-labels.jsonl / da-dev-tables/*.csv (257题/68CSV)
  dabstep/                                 dev.jsonl(10题带答案) + context/(共享语料 24MB)

跑:
  python evals/bench/da_eval.py infiagent [N]   # DAEval,默认 10
  python evals/bench/da_eval.py dabstep  [N]    # DABStep dev(共 10 题)
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_API = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _API)

from ezdata.interface.web import LLMClient  # noqa: E402
from ezdata.interface.web.llm import strip_code_fence  # noqa: E402

_INFI = os.path.join(_HERE, 'infiagent_src', 'examples', 'DA-Agent', 'data')
_INFI_TABLES = os.path.join(_INFI, 'da-dev-tables')
_DABSTEP = os.path.join(_HERE, 'dabstep')
_DAB_CTX = os.path.join(_DABSTEP, 'context')


# ----------------------------- 代码生成 + 执行 -----------------------------

def _extract_code(raw):
    """从模型输出里抠出 python 代码块;没有 fence 就整段当代码。"""
    t = raw.strip()
    m = re.search(r'```(?:python|py)?\s*\n(.*?)```', t, re.S)
    if m:
        return m.group(1).strip()
    return strip_code_fence(t)


def _run_code(code, workdir, timeout=90):
    """把代码写进 workdir 下临时文件执行,cwd=workdir 使相对读表可用。返回 (stdout, stderr, rc)。"""
    fd, path = tempfile.mkstemp(suffix='.py', dir=workdir, text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(code)
        p = subprocess.run(
            [sys.executable, os.path.basename(path)],
            cwd=workdir, capture_output=True, text=True, timeout=timeout,
        )
        return p.stdout.strip(), p.stderr.strip(), p.returncode
    except subprocess.TimeoutExpired:
        return '', f'TIMEOUT>{timeout}s', -1
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def gen_run(llm, prompt, workdir, max_retry=1):
    """生成脚本→执行;报错/空输出则把 stderr 反馈喂回重生成,最多 max_retry 次。"""
    cur = prompt
    last = {'code': '', 'stdout': '', 'stderr': '', 'rc': None}
    for attempt in range(max_retry + 1):
        raw = llm.complete(cur)
        code = _extract_code(raw)
        stdout, stderr, rc = _run_code(code, workdir)
        last = {'code': code, 'stdout': stdout, 'stderr': stderr, 'rc': rc, 'attempts': attempt + 1}
        if rc == 0 and stdout:
            return last
        if attempt < max_retry:
            cur = (
                prompt
                + f'\n\n【你上一次的代码】\n{code}\n\n【执行结果】rc={rc} stderr:\n{stderr[:600]}\n'
                + (f'stdout:\n{stdout[:300]}\n' if stdout else '')
                + '请修正代码,仍只输出一个完整可执行的 Python 脚本(务必 print 出规定格式的答案)。'
            )
    return last


# ----------------------------- schema 预览 -----------------------------

def _csv_preview(path, n_rows=3, max_cols=40):
    import pandas as pd

    try:
        df = pd.read_csv(path, nrows=200)
    except Exception as e:  # 编码/分隔符异常也照实告知模型
        return f'(无法预览: {type(e).__name__}: {e})'
    cols = list(df.columns)[:max_cols]
    dt = '\n'.join(f'  - {c}: {df[c].dtype}' for c in cols)
    head = df[cols].head(n_rows).to_csv(index=False)
    more = '' if len(df.columns) <= max_cols else f'\n(另有 {len(df.columns) - max_cols} 列未列出)'
    return f'列({len(df.columns)}):\n{dt}{more}\n前 {n_rows} 行:\n{head}'


# ----------------------------- 判分 -----------------------------

def _as_float(s):
    try:
        return float(str(s).replace(',', '').replace('%', '').strip())
    except (ValueError, TypeError):
        return None


def _num_eq(a, b, tol_abs=0.01, tol_rel=0.01):
    fa, fb = _as_float(a), _as_float(b)
    if fa is None or fb is None:
        return None  # 不是数值,交给字符串比对
    return abs(fa - fb) <= max(tol_abs, tol_rel * max(abs(fa), abs(fb)) + 1e-9)


def _str_eq(a, b):
    na = re.sub(r'\s+', ' ', str(a).strip().lower().rstrip('.'))
    nb = re.sub(r'\s+', ' ', str(b).strip().lower().rstrip('.'))
    return na == nb


def _val_eq(pred, gold):
    r = _num_eq(pred, gold)
    return r if r is not None else _str_eq(pred, gold)


# ----------------------------- InfiAgent-DABench -----------------------------

def _infi_prompt(q, filename, preview, bare=False):
    # bare(消融):去掉 CSV schema 预览 + constraints 约束提示,只留问题+文件名+输出格式
    preview_block = '' if bare else f'{preview}\n'
    constraint_block = '' if bare else f'\n【约束】{q.get("constraints", "")}\n'
    return f"""你是数据分析专家。用 Python(可用 pandas / numpy / scipy / sklearn)解决下面的数据分析问题。

数据文件:{filename}(就在当前工作目录,用相对路径读取)
{preview_block}
【问题】{q['question']}
{constraint_block}
【输出格式(必须严格遵守)】
{q['format']}

要求:
1. 只输出一个完整、可直接运行的 Python 脚本(用 ```python 包裹)。
2. 脚本最后必须用 print 打印出符合上面【输出格式】的那一行,形如 @name[value],value 按要求四舍五入。
3. 除了这一行答案,不要 print 其它无关内容。"""


_AT_RE = re.compile(r'@(\w+)\s*\[\s*([^\]]*?)\s*\]')


def _parse_ats(text):
    return {k: v.strip() for k, v in _AT_RE.findall(text or '')}


def eval_infiagent(llm, n, bare=False):
    qs = [json.loads(l) for l in open(os.path.join(_INFI, 'da-dev-questions.jsonl'), encoding='utf-8')]
    labels = {json.loads(l)['id']: json.loads(l)['common_answers']
              for l in open(os.path.join(_INFI, 'da-dev-labels.jsonl'), encoding='utf-8')}
    sample = qs[:n]
    mode = 'bare(无schema预览/无约束)' if bare else 'full(schema预览+约束)'
    print(f'InfiAgent-DABench | 模型 {llm.cfg.get("model")} | 抽样 {len(sample)}/{len(qs)} 题 | {mode}')
    print('=' * 78)
    results = []
    for i, q in enumerate(sample):
        preview = '' if bare else _csv_preview(os.path.join(_INFI_TABLES, q['file_name']))
        run = gen_run(llm, _infi_prompt(q, q['file_name'], preview, bare), _INFI_TABLES)
        pred = _parse_ats(run['stdout'])
        gold = labels.get(q['id'], [])
        # 逐子答案比对,全对才算该题正确
        subs = []
        for name, gval in gold:
            pv = pred.get(name)
            subs.append(pv is not None and _val_eq(pv, gval))
        ok = bool(subs) and all(subs)
        row = {'id': q['id'], 'level': q.get('level'), 'file': q['file_name'], 'ok': ok,
               'gold': gold, 'pred': pred, 'rc': run['rc'], 'stderr': run['stderr'][:160],
               'attempts': run.get('attempts', 1)}
        results.append(row)
        mark = 'OK ' if ok else 'XX '
        print(f'[{i + 1:2}/{len(sample)}] {q.get("level",""):7} {q["file_name"][:26]:26} {mark} '
              f'gold={gold} pred={dict(pred)} {("| " + run["stderr"][:60]) if not ok and run["stderr"] else ""}')
    _summary('InfiAgent-DABench', results, 'level', ('easy', 'medium', 'hard'), llm, bare)
    return results


# ----------------------------- DABStep -----------------------------

def _dab_context_block(bare=False):
    """把共享语料摘要成上下文:小文本(manual/readme)内联,CSV/JSON 给结构预览,大文件让代码自读。

    bare(消融):只给文件名清单,不给任何 schema 预览 / JSON 样例 / 内联手册,逼模型盲读文件。
    """
    if bare:
        names = [f for f in ('payments.csv', 'merchant_category_codes.csv', 'acquirer_countries.csv',
                             'fees.json', 'merchant_data.json', 'manual.md', 'payments-readme.md')
                 if os.path.exists(os.path.join(_DAB_CTX, f))]
        return '【共享数据语料文件(均在当前工作目录,自行按需读取/解析):】\n' + '\n'.join(f'  - {f}' for f in names)
    parts = ['【共享数据语料:均在当前工作目录,按需用相对路径读取】\n']
    # CSV 结构预览
    for f in ('payments.csv', 'merchant_category_codes.csv', 'acquirer_countries.csv'):
        p = os.path.join(_DAB_CTX, f)
        if os.path.exists(p):
            parts.append(f'--- {f} ---\n{_csv_preview(p, n_rows=2)}\n')
    # JSON 结构样例
    for f in ('fees.json', 'merchant_data.json'):
        p = os.path.join(_DAB_CTX, f)
        if os.path.exists(p):
            try:
                d = json.load(open(p, encoding='utf-8'))
                sample = d[:1] if isinstance(d, list) else d
                parts.append(f'--- {f}({"list, %d 条" % len(d) if isinstance(d, list) else "dict"})样例 ---\n'
                             f'{json.dumps(sample, ensure_ascii=False)[:800]}\n')
            except Exception:
                pass
    # 规则手册 + readme 全文内联(小,且 hard 题必须读规则)
    for f in ('manual.md', 'payments-readme.md'):
        p = os.path.join(_DAB_CTX, f)
        if os.path.exists(p):
            parts.append(f'--- {f}(全文)---\n{open(p, encoding="utf-8").read()}\n')
    return '\n'.join(parts)


def _dab_prompt(task, ctx):
    return f"""你是数据分析专家。基于下面的共享数据语料,用 Python(pandas/numpy 等)回答问题。

{ctx}

【问题】{task['question']}

【回答规范】{task.get('guidelines', '')}

要求:
1. 只输出一个完整、可直接运行的 Python 脚本(用 ```python 包裹),按需读取上面列出的语料文件。
2. 脚本最后必须只 print 出最终答案本身(严格遵守【回答规范】:比如只要国家代码就只打印代码;要数字就打印数字,不带多余文字/单位/解释)。"""


def eval_dabstep(llm, n, bare=False):
    tasks = [json.loads(l) for l in open(os.path.join(_DABSTEP, 'dev.jsonl'), encoding='utf-8')]
    sample = tasks[:n]
    ctx = _dab_context_block(bare)
    mode = 'bare(仅文件名,无预览/无手册内联)' if bare else 'full(预览+手册内联)'
    print(f'DABStep(dev) | 模型 {llm.cfg.get("model")} | 抽样 {len(sample)}/{len(tasks)} 题 | {mode} | 语料上下文 ~{len(ctx)//1000}k 字')
    print('=' * 78)
    results = []
    for i, task in enumerate(sample):
        run = gen_run(llm, _dab_prompt(task, ctx), _DAB_CTX, max_retry=1)
        pred = (run['stdout'].splitlines() or [''])[-1].strip() if run['stdout'] else ''
        gold = str(task['answer']).strip()
        ok = _val_eq(pred, gold)
        row = {'id': task['task_id'], 'level': task.get('level'), 'ok': ok, 'gold': gold,
               'pred': pred, 'rc': run['rc'], 'stderr': run['stderr'][:160], 'attempts': run.get('attempts', 1)}
        results.append(row)
        mark = 'OK ' if ok else 'XX '
        print(f'[{i + 1:2}/{len(sample)}] {task.get("level",""):5} {mark} gold=[{gold}] pred=[{pred[:50]}] '
              f'{("| " + run["stderr"][:60]) if not ok and run["stderr"] else ""}')
    _summary('DABStep(dev)', results, 'level', ('easy', 'hard'), llm, bare)
    return results


# ----------------------------- 汇总 -----------------------------

def _summary(name, results, key, tiers, llm, bare=False):
    print('=' * 78)
    n = len(results)
    s = sum(r['ok'] for r in results)
    modetag = 'bare' if bare else 'full'
    print(f'{name} 准确率({llm.cfg.get("model")}, {modetag}): {s}/{n} = {s / n * 100:.1f}%')
    for t in tiers:
        sub = [r for r in results if r.get(key) == t]
        if sub:
            ss = sum(r['ok'] for r in sub)
            print(f'  {t:8}: {ss}/{len(sub)} = {ss / len(sub) * 100:.0f}%')
    tag = name.split('(')[0].split('-')[0].lower()
    out = os.path.join(_HERE, f'_da_{tag}_{modetag}_run.json')
    json.dump(results, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2, default=str)
    print(f'明细已写: {out}')


def main():
    args = sys.argv[1:]
    bare = 'bare' in args
    positional = [a for a in args if not a.isdigit() and a != 'bare']
    mode = positional[0] if positional else 'infiagent'
    nums = [a for a in args if a.isdigit()]
    n = int(nums[0]) if nums else 10
    llm = LLMClient()
    if mode.startswith('dab'):
        eval_dabstep(llm, n, bare)
    else:
        eval_infiagent(llm, n, bare)


if __name__ == '__main__':
    main()
