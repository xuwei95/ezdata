import request from '@/utils/request'

// ---------------- 元信息 ----------------
export function getSourceTypes() {
  return request({ url: '/data/source/types', method: 'get' })
}
export function getSourceSchema(sourceType) {
  return request({ url: '/data/source/schema/' + sourceType, method: 'get' })
}
// 数据源类型品牌图标(返回 svg 文本)
export function getSourceTypeIcon(sourceType) {
  return request({ url: '/data/source/type-icon/' + sourceType, method: 'get' })
}
export function getOperators() {
  return request({ url: '/data/operators', method: 'get' })
}

// ---------------- 数据源 ----------------
export function listSource(query) {
  return request({ url: '/data/source/list', method: 'get', params: query })
}
export function getSource(id) {
  return request({ url: '/data/source/info/' + id, method: 'get' })
}
export function addSource(data) {
  return request({ url: '/data/source', method: 'post', data })
}
export function updateSource(data) {
  return request({ url: '/data/source', method: 'put', data })
}
export function delSource(ids) {
  return request({ url: '/data/source/' + ids, method: 'delete' })
}
export function testSource(data) {
  return request({ url: '/data/source/test', method: 'post', data })
}
export function listTables(id) {
  return request({ url: `/data/source/${id}/tables`, method: 'get' })
}
export function listColumns(id, table) {
  return request({ url: `/data/source/${id}/columns`, method: 'get', params: { table } })
}

// ---------------- 数据模型 ----------------
export function listModel(query) {
  return request({ url: '/data/model/list', method: 'get', params: query })
}
export function getModel(id) {
  return request({ url: '/data/model/info/' + id, method: 'get' })
}
export function addModel(data) {
  return request({ url: '/data/model', method: 'post', data })
}
export function updateModel(data) {
  return request({ url: '/data/model', method: 'put', data })
}
export function delModel(ids) {
  return request({ url: '/data/model/' + ids, method: 'delete' })
}

// ---------------- 查询 / 接口 ----------------
export function queryModel(id, data) {
  return request({ url: `/data/model/${id}/query`, method: 'post', data })
}
export function searchModel(id, data) {
  return request({ url: `/data/model/${id}/search`, method: 'post', data })
}
export function aiQueryModel(id, data) {
  return request({ url: `/data/model/${id}/ai-query`, method: 'post', data })
}
export function getSampleQuery(id) {
  return request({ url: `/data/model/${id}/sample-query`, method: 'get' })
}
// AI 生成 EchartsBuilder 图表配置:data={question, columns};返回 {cfg}
export function aiChart(id, data) {
  return request({ url: `/data/model/${id}/ai-chart`, method: 'post', data, timeout: 120000 })
}

// ---------------- 分析模板(取数 + 图表配置,可复用)----------------
export function listAnalysisTemplate(modelId) {
  return request({ url: '/data/analysis-template/list', method: 'get', params: { modelId } })
}
export function saveAnalysisTemplate(data) {
  return request({ url: '/data/analysis-template', method: 'post', data })
}
// 对话图表存为看板:data={name, datasourceCode, native, chartSpec};后端自动挂 custom_query 模型
export function saveChartAsBoard(data) {
  return request({ url: '/data/analysis-template/from-chart', method: 'post', data })
}
export function delAnalysisTemplate(ids) {
  return request({ url: '/data/analysis-template/' + ids, method: 'delete' })
}

// ---------------- ETL 调试 ----------------
export function previewEtl(data) {
  // 代码取数/爬虫预览可能较慢,超时放到 300s(与后端沙箱超时一致)
  return request({ url: '/data/etl/preview', method: 'post', data, timeout: 300000 })
}
export function testLoadEtl(data) {
  return request({ url: '/data/etl/test-load', method: 'post', data, timeout: 300000 })
}
export function aiQueryEtl(data) {
  return request({ url: '/data/etl/ai-query', method: 'post', data })
}
export function aiTransformEtl(data) {
  return request({ url: '/data/etl/ai-transform', method: 'post', data })
}

