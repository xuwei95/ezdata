from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.globals import ThemeType
import pandas as pd
from tabulate import tabulate
# 假设数据已经存储在一个名为 df 的 DataFrame 中
df = pd.DataFrame({
    '日期': ['2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06', '2023-01-09'],
    '开盘': [13.20, 13.71, 14.40, 14.50, 14.75],
    '收盘': [13.77, 14.32, 14.48, 14.62, 14.80],
    '最高': [13.85, 14.42, 14.74, 14.72, 14.88],
    '最低': [13.05, 13.63, 14.37, 14.48, 14.52],
    '成交量': [2194128, 2189683, 1665425, 1195745, 1057659]
})
line = Line(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
line.add_xaxis(df['日期'].tolist())
line.add_yaxis('收盘价', df['收盘'].tolist())
line.set_global_opts(
    title_opts=opts.TitleOpts(title="收盘价趋势图"),
    tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
    xaxis_opts=opts.AxisOpts(type_="category"),
    yaxis_opts=opts.AxisOpts(type_="value"),
)
html_content = line.render_embed()
print(html_content)
a = line.render_notebook()
# f = open('1.html', 'w')
# f.write(html_content)

markdown_table = tabulate(df)
print(markdown_table)
print(df.to_dict(orient='list'))
