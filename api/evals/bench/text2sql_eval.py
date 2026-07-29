"""文本到 SQL 执行准确率(EX)基准 —— 首个可对外报的准确率数字。

- 库:Chinook(公开示例库,11 表、有真实 join)。
- 用例:自建、分 easy/medium/hard;gold 为人工审定 SQL。
- 打法:问题 --Core.ask(NL→SQL)--> 执行 --> 结果集,与 gold SQL 执行结果比对。
- 判定:顺序无关的多重集比对 + 数值容差(2 位小数)。strict=按列序;lenient=列序无关。

跑:python evals/bench/text2sql_eval.py   (在 api/ 下)
"""

import json
import os
import sqlite3
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_API = os.path.dirname(os.path.dirname(_HERE))  # bench -> evals -> api
sys.path.insert(0, _API)

from ezdata.interface.web import ConnectionStore, Core, LLMClient, config  # noqa: E402

DB = os.path.join(_HERE, 'chinook.db')

# id, 难度, 中文问题, gold SQL(人工审定)
CASES = [
    # ---------- easy:单表 / 计数 / 聚合 ----------
    ('e1', 'easy', '一共有多少首曲目(Track)?', 'SELECT COUNT(*) FROM Track'),
    ('e2', 'easy', '有多少个不同的流派(Genre)?', 'SELECT COUNT(*) FROM Genre'),
    ('e3', 'easy', '客户(Customer)分布在多少个不同的国家?', 'SELECT COUNT(DISTINCT Country) FROM Customer'),
    ('e4', 'easy', '所有曲目里最高的单价(UnitPrice)是多少?', 'SELECT MAX(UnitPrice) FROM Track'),
    ('e5', 'easy', '专辑(Album)一共有多少张?', 'SELECT COUNT(*) FROM Album'),
    # ---------- medium:group by / join / order+limit ----------
    ('m1', 'medium', '每个流派有多少首曲目,取数量最多的前5个,给出流派名和数量',
     'SELECT g.Name, COUNT(*) c FROM Track t JOIN Genre g ON t.GenreId=g.GenreId GROUP BY g.GenreId ORDER BY c DESC LIMIT 5'),
    ('m2', 'medium', '每个国家有多少客户,按客户数从多到少列出前5',
     'SELECT Country, COUNT(*) c FROM Customer GROUP BY Country ORDER BY c DESC LIMIT 5'),
    ('m3', 'medium', '曲目数量最多的前3张专辑的标题(Title)和曲目数',
     'SELECT al.Title, COUNT(*) c FROM Track t JOIN Album al ON t.AlbumId=al.AlbumId GROUP BY al.AlbumId ORDER BY c DESC LIMIT 3'),
    ('m4', 'medium', '销售额(发票 Total)合计最高的前5个国家(BillingCountry)及其合计',
     'SELECT BillingCountry, ROUND(SUM(Total),2) s FROM Invoice GROUP BY BillingCountry ORDER BY s DESC LIMIT 5'),
    ('m5', 'medium', '每个流派的平均曲目时长(Milliseconds),取平均时长最长的前5个流派',
     'SELECT g.Name, AVG(t.Milliseconds) a FROM Track t JOIN Genre g ON t.GenreId=g.GenreId GROUP BY g.GenreId ORDER BY a DESC LIMIT 5'),
    ('m6', 'medium', '有多少客户从未下过订单(在 Invoice 里没有记录)?',
     'SELECT COUNT(*) FROM Customer c WHERE c.CustomerId NOT IN (SELECT DISTINCT CustomerId FROM Invoice)'),
    # ---------- hard:多表 join / 子查询 / having / 日期 ----------
    ('h1', 'hard', '消费总额最高的前5位客户,给出名(FirstName)、姓(LastName)和消费总额',
     'SELECT c.FirstName, c.LastName, ROUND(SUM(i.Total),2) s FROM Customer c JOIN Invoice i ON c.CustomerId=i.CustomerId GROUP BY c.CustomerId ORDER BY s DESC LIMIT 5'),
    ('h2', 'hard', '曲目数量最多的前5位艺术家(Artist)的名字和曲目数',
     'SELECT ar.Name, COUNT(*) c FROM Track t JOIN Album al ON t.AlbumId=al.AlbumId JOIN Artist ar ON al.ArtistId=ar.ArtistId GROUP BY ar.ArtistId ORDER BY c DESC LIMIT 5'),
    ('h3', 'hard', '每个流派的总销售额(按 InvoiceLine 的 UnitPrice*Quantity 汇总),取前5',
     'SELECT g.Name, ROUND(SUM(il.UnitPrice*il.Quantity),2) s FROM InvoiceLine il JOIN Track t ON il.TrackId=t.TrackId JOIN Genre g ON t.GenreId=g.GenreId GROUP BY g.GenreId ORDER BY s DESC LIMIT 5'),
    ('h4', 'hard', '有多少不同的客户购买过 Rock 流派的曲目?',
     "SELECT COUNT(DISTINCT i.CustomerId) FROM Invoice i JOIN InvoiceLine il ON i.InvoiceId=il.InvoiceId JOIN Track t ON il.TrackId=t.TrackId JOIN Genre g ON t.GenreId=g.GenreId WHERE g.Name='Rock'"),
    ('h5', 'hard', '2023 年各月的销售额(发票 Total 合计),按月份列出',
     "SELECT strftime('%Y-%m', InvoiceDate) m, ROUND(SUM(Total),2) s FROM Invoice WHERE strftime('%Y', InvoiceDate)='2023' GROUP BY m ORDER BY m"),
    ('h6', 'hard', '有多少首曲目从未被卖出过(不在 InvoiceLine 中)?',
     'SELECT COUNT(*) FROM Track WHERE TrackId NOT IN (SELECT DISTINCT TrackId FROM InvoiceLine)'),
    ('h7', 'hard', '平均每张发票金额最高的前5个国家(BillingCountry)及其平均发票金额',
     'SELECT BillingCountry, ROUND(AVG(Total),2) a FROM Invoice GROUP BY BillingCountry ORDER BY a DESC LIMIT 5'),
    ('h8', 'hard', '每位支持代表(Employee)负责的客户数,给出员工名(FirstName)、姓(LastName)和客户数',
     'SELECT e.FirstName, e.LastName, COUNT(c.CustomerId) c FROM Employee e JOIN Customer c ON c.SupportRepId=e.EmployeeId GROUP BY e.EmployeeId ORDER BY c DESC'),
]


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
    try:  # 数值字符串归一(容差 2 位)
        f = float(s)
        r = round(f, 2)
        return str(int(r)) if r == int(r) else f'{r:.2f}'
    except ValueError:
        return s


def _rows_strict(rows):
    return sorted([tuple(_norm_cell(c) for c in row) for row in rows])


def _rows_lenient(rows):  # 列序无关(允许模型换列顺序)
    return sorted([tuple(sorted(_norm_cell(c) for c in row)) for row in rows])


def _gold_rows(sql):
    con = sqlite3.connect(DB)
    try:
        cur = con.execute(sql)
        return [tuple(r) for r in cur.fetchall()]
    finally:
        con.close()


def main():
    store_path = os.path.join(_HERE, '_store.db')
    store = ConnectionStore(store_path)
    if not store.get('chinook'):
        store.add('chinook', 'sqlite', {'db_file': DB}, {})
    core = Core(store, LLMClient(config.llm_config()))
    model = core.llm.cfg.get('model')
    print(f'库: chinook.db | 模型: {model} | 用例: {len(CASES)}')
    print('=' * 72)

    results = []
    for cid, tier, q, gold in CASES:
        row = {'id': cid, 'tier': tier, 'strict': False, 'lenient': False, 'err': ''}
        try:
            gold_rows = _gold_rows(gold)
        except Exception as e:
            row['err'] = f'GOLD错误: {e}'
            results.append(row)
            print(f'[{cid:3}] {tier:6} GOLD-ERR  {e}')
            continue
        t0 = time.time()
        try:
            r = core.ask('chinook', q, tables=None, limit=2000)
            pred_rows = [tuple(d.values()) for d in (r.get('rows') or [])]
            row['strict'] = _rows_strict(gold_rows) == _rows_strict(pred_rows)
            row['lenient'] = _rows_lenient(gold_rows) == _rows_lenient(pred_rows)
            row['stmt'] = r.get('statement')
        except Exception as e:
            row['err'] = f'{type(e).__name__}: {e}'
        row['ms'] = int((time.time() - t0) * 1000)
        results.append(row)
        mark = 'OK ' if row['strict'] else ('~L ' if row['lenient'] else 'XX ')
        print(f'[{cid:3}] {tier:6} {mark} gold={len(gold_rows)}行 {row["ms"]}ms {row["err"]}')

    print('=' * 72)
    n = len(results)
    strict = sum(1 for r in results if r['strict'])
    lenient = sum(1 for r in results if r['lenient'])
    print(f'EX(strict 列序敏感): {strict}/{n} = {strict / n * 100:.1f}%')
    print(f'EX(lenient 列序无关): {lenient}/{n} = {lenient / n * 100:.1f}%')
    for tier in ('easy', 'medium', 'hard'):
        sub = [r for r in results if r['tier'] == tier]
        if sub:
            s = sum(1 for r in sub if r['strict'])
            print(f'  {tier:6}: {s}/{len(sub)} = {s / len(sub) * 100:.0f}%')
    # 落盘:失败项的生成 SQL,便于复盘
    out = os.path.join(_HERE, '_last_run.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f'明细(含生成 SQL)已写: {out}')


if __name__ == '__main__':
    main()
