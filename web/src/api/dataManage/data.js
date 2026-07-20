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
// 同步该数据源到目录检索索引(异步 worker 任务)
export function syncSourceCatalog(id) {
  return request({ url: `/data/source/${id}/sync-catalog`, method: 'post' })
}
export function listTables(id) {
  return request({ url: `/data/source/${id}/tables`, method: 'get' })
}
export function listColumns(id, table) {
  return request({ url: `/data/source/${id}/columns`, method: 'get', params: { table } })
}

// ---------------- 指标(语义层) ----------------
export function listMetric(query) {
  return request({ url: '/data/metric/list', method: 'get', params: query })
}
export function getMetric(id) {
  return request({ url: '/data/metric/info/' + id, method: 'get' })
}
export function addMetric(data) {
  return request({ url: '/data/metric', method: 'post', data })
}
export function updateMetric(data) {
  return request({ url: '/data/metric', method: 'put', data })
}
export function delMetric(ids) {
  return request({ url: '/data/metric/' + ids, method: 'delete' })
}
export function previewMetric(code) {
  return request({ url: `/data/metric/${code}/preview`, method: 'post' })
}
// ---------------- 数据血缘 ----------------
export function getLineage(params) {
  return request({ url: '/data/lineage', method: 'get', params })
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
// 查询/检索是幂等读操作:多图看板会并发发出相同 native 的取数,须关闭"防重复提交"拦截,否则第二个组件被 request.js 拦成「数据正在处理,请勿重复提交」。
// silent=true(预览/展示模式):失败不弹 msg,改打 console(见 request.js)。
export function queryModel(id, data, silent = false) {
  return request({ url: `/data/model/${id}/query`, method: 'post', data, headers: { repeatSubmit: false }, silent })
}
export function searchModel(id, data, silent = false) {
  return request({ url: `/data/model/${id}/search`, method: 'post', data, headers: { repeatSubmit: false }, silent })
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
// 看板详情(独立预览页按 id 拉取)
export function getAnalysisTemplate(id, silent = false) {
  return request({ url: `/data/analysis-template/detail/${id}`, method: 'get', silent })
}
export function saveAnalysisTemplate(data) {
  return request({ url: '/data/analysis-template', method: 'post', data })
}
// 对话图表存为看板:data={name, datasourceCode, native, chartSpec};后端自动挂 custom_query 模型
export function saveChartAsBoard(data) {
  return request({ url: '/data/analysis-template/from-chart', method: 'post', data })
}
// 代码转看板预览:按 数据源 + native 只读取数,返回 {records,total} 供画图。data={datasourceCode, native}
// (代码转看板的「流式生成 native+cfg」用 fetch 直连 /data/analysis-template/code-to-board/stream)
export function previewNative(data) {
  return request({ url: '/data/analysis-template/preview-native', method: 'post', data, timeout: 120000 })
}
export function delAnalysisTemplate(ids) {
  return request({ url: '/data/analysis-template/' + ids, method: 'delete' })
}
// 看板匿名分享:开启/重置 → 返回 {token};关闭 → 置空
export function genBoardShare(id) {
  return request({ url: `/data/analysis-template/${id}/share`, method: 'post' })
}
export function revokeBoardShare(id) {
  return request({ url: `/data/analysis-template/${id}/share`, method: 'delete' })
}
// 公开看板(免登录,凭 token):isToken:false 不带鉴权头
export function getSharedBoard(token) {
  return request({ url: `/open/board/${token}`, method: 'get', headers: { isToken: false } })
}

// ---------------- 多图看板 / 大屏(dash_type=board/screen)----------------
export function listDashboards(dashType) {
  return request({ url: '/data/dashboard/list', method: 'get', params: { dashType } })
}
export function getDashboard(id, silent = false) {
  return request({ url: `/data/dashboard/detail/${id}`, method: 'get', silent })
}
export function saveDashboard(data) {
  return request({ url: '/data/dashboard', method: 'post', data })
}
export function delDashboard(ids) {
  return request({ url: '/data/dashboard/' + ids, method: 'delete' })
}
export function genDashboardShare(id) {
  return request({ url: `/data/dashboard/${id}/share`, method: 'post' })
}
export function revokeDashboardShare(id) {
  return request({ url: `/data/dashboard/${id}/share`, method: 'delete' })
}
// 公开多图看板/大屏(免登录):返回 {name,canvas,components(含 rows/chartSpec),filters}
export function getSharedDashboard(token) {
  return request({ url: `/open/dashboard/${token}`, method: 'get', headers: { isToken: false } })
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

