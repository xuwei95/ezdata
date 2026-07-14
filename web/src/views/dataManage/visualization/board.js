// 单图看板共享工具:图表类型清单、cfg 版本、native 文本/对象互转、取数。
// 供 index.vue(编辑器)/ preview.vue(独立预览)/ share.vue(公开分享)复用,避免各拷一份。
import { queryModel } from '@/api/dataManage/data'

// 与 EchartsBuilder 的 TYPE_GROUPS 保持一致(用于 isEchartsCfg 守卫,区分旧 pygwalker 数组格式)
export const CHART_TYPES = [
  'bar', 'bar_stack', 'bar_percent', 'hbar', 'line', 'area', 'line_stack',
  'pie', 'donut', 'rose', 'scatter', 'radar', 'funnel', 'gauge', 'kline',
  'combo', 'waterfall', 'heatmap', 'boxplot', 'treemap', 'sankey', 'kpi', 'table'
]

// chart_spec 结构版本:EchartsBuilder.migrate 按此做向后兼容
export const CFG_VERSION = 1

// 是否为 ECharts 图表配置(区分旧 pygwalker 格式/仅查询)
export function isEchartsCfg(c) {
  return !!c && typeof c === 'object' && !Array.isArray(c) && CHART_TYPES.includes(c.type)
}

// native 可能是 SQL 字符串,也可能是 dict(ES DSL / Mongo pipeline,代码转看板生成);
// 文本框显示统一转字符串(dict → 缩进 JSON),否则 v-model 到对象会渲染成 [object Object]。
export function nativeToText(n) {
  if (n === null || n === undefined) return ''
  return typeof n === 'string' ? n : JSON.stringify(n, null, 2)
}

// 文本框内容 → 执行用 native:能 JSON.parse 成对象/数组就用对象(ES/Mongo),否则原样当 SQL 串。
export function parseNative(t) {
  const s = (typeof t === 'string' ? t : nativeToText(t)).trim()
  if (s[0] === '{' || s[0] === '[') { try { return JSON.parse(s) } catch (e) { /* 非法 JSON,当 SQL */ } }
  return s
}

// 看板变量定义数组(存储态 [{name,label,type,default,value,options}])→ 取数用的 {name: value} 映射。
// daterange 展开成 名_start / 名_end 两个占位。空值回退默认值。
export function paramsToValues(defs) {
  const out = {}
  for (const p of (defs || [])) {
    if (!p || !p.name) continue
    let val = p.value
    if (val === undefined || val === null || val === '') val = p.default
    if (p.type === 'daterange' && Array.isArray(val)) {
      out[p.name + '_start'] = val[0]
      out[p.name + '_end'] = val[1]
    } else {
      out[p.name] = val
    }
  }
  return out
}

// 按数据模型 + native(+ 看板变量 params)取数,返回裁剪后的行。统一编辑/预览的取数逻辑。
export async function fetchBoardRows(modelId, native, params, cap = 5000) {
  const body = { native: parseNative(native) }
  if (params && Object.keys(params).length) body.params = params
  const res = await queryModel(modelId, body)
  return (res.data.records || []).slice(0, cap)
}
