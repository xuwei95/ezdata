"""种子:代码看板(dash_type='code')示例 —— 真跑数据源(demo_es 的行业板块汇总)出图。
用途:演示 / 回归测试代码看板端到端(创建·预览·纯图页·匿名分享)。保留,不随测试删除。

运行:docker exec ezdata-backend-dev python sql/seed_code_boards.py
"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # /app 上根,便于直接 python sql/xxx.py
logging.disable(logging.INFO)

BOARDS = [
    {
        'name': '示例·行业涨幅 Top10(代码看板)',
        'ds': 'demo_es',
        'code': '''
from pyecharts.charts import Bar
from pyecharts import options as opts
rows = handler.query({'index': 'fin_industry_summary', 'body': {'size': 200, 'query': {'match_all': {}}}}, None, 200)
rows = [r for r in rows if r.get('change_pct') is not None]
rows.sort(key=lambda r: r['change_pct'], reverse=True)
top = rows[:10]
x = [r['board_name'] for r in top]
y = [round(float(r['change_pct']), 2) for r in top]
c = (Bar()
     .add_xaxis(x)
     .add_yaxis('涨幅%', y)
     .set_global_opts(title_opts=opts.TitleOpts(title='行业涨幅 Top10'),
                      xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30))))
result = {'type': 'html', 'value': c.render_embed()}
''',
    },
    {
        'name': '示例·行业资金净流入 Top10(代码看板)',
        'ds': 'demo_es',
        'code': '''
from pyecharts.charts import Bar
from pyecharts import options as opts
rows = handler.query({'index': 'fin_industry_summary', 'body': {'size': 200, 'query': {'match_all': {}}}}, None, 200)
rows = [r for r in rows if r.get('net_inflow') is not None]
rows.sort(key=lambda r: r['net_inflow'], reverse=True)
top = rows[:10][::-1]  # 横向条形从下往上递增
x = [r['board_name'] for r in top]
y = [round(float(r['net_inflow']), 2) for r in top]
c = (Bar()
     .add_xaxis(x)
     .add_yaxis('净流入(亿)', y)
     .reversal_axis()
     .set_series_opts(label_opts=opts.LabelOpts(position='right'))
     .set_global_opts(title_opts=opts.TitleOpts(title='行业资金净流入 Top10')))
result = {'type': 'html', 'value': c.render_embed()}
''',
    },
    {
        'name': '示例·行业内涨跌家数占比(代码看板)',
        'ds': 'demo_es',
        'code': '''
from pyecharts.charts import Pie
from pyecharts import options as opts
rows = handler.query({'index': 'fin_industry_summary', 'body': {'size': 200, 'query': {'match_all': {}}}}, None, 200)
up = sum(int(r.get('up_count') or 0) for r in rows)
down = sum(int(r.get('down_count') or 0) for r in rows)
c = (Pie()
     .add('', [('上涨', up), ('下跌', down)])
     .set_global_opts(title_opts=opts.TitleOpts(title='行业内涨跌家数占比'))
     .set_series_opts(label_opts=opts.LabelOpts(formatter='{b}: {c} ({d}%)')))
result = {'type': 'html', 'value': c.render_embed()}
''',
    },
]


async def main():
    from config.database import AsyncSessionLocal
    from module_data.entity.vo.data_vo import DashboardVo
    from module_data.service.data_service import DashboardService

    async with AsyncSessionLocal() as db:
        for b in BOARDS:
            vo = DashboardVo(
                name=b['name'], dash_type='code', remark='代码看板示例种子',
                refresh_interval=0, canvas={'mode': 'single'},
                components=[{'id': 'c1', 'type': 'code', 'inline': {'datasourceCode': b['ds'], 'code': b['code']}}],
                filters=[],
            )
            did = await DashboardService.save(db, vo, 'admin')
            print(f"[seed] {b['name']} -> id={did}")


if __name__ == '__main__':
    asyncio.run(main())
