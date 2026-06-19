import request from '@/utils/request'

// 列表 / 容器
export function listDag(query) {
  return request({ url: '/task/dag/list', method: 'get', params: query })
}
export function createDag(data) {
  return request({ url: '/task/dag', method: 'post', data })
}
export function delDag(ids) {
  return request({ url: '/task/dag/' + ids, method: 'delete' })
}
export function getDagDetail(id) {
  return request({ url: `/task/dag/${id}/detail`, method: 'get' })
}
export function saveDagSettings(id, data) {
  return request({ url: `/task/dag/${id}/settings`, method: 'put', data })
}

// 草稿
export function getDraft(id) {
  return request({ url: `/task/dag/${id}/draft`, method: 'get' })
}
export function saveDraft(id, graph) {
  return request({ url: `/task/dag/${id}/draft`, method: 'put', data: { graph } })
}

// 发布 / 版本 / 回滚
export function publishDag(id, remark) {
  return request({ url: `/task/dag/${id}/publish`, method: 'post', data: { remark } })
}
export function listVersions(id) {
  return request({ url: `/task/dag/${id}/versions`, method: 'get' })
}
export function getVersionGraph(verId) {
  return request({ url: `/task/dag/version/${verId}`, method: 'get' })
}
export function rollbackDag(id, verId) {
  return request({ url: `/task/dag/${id}/rollback/${verId}`, method: 'post' })
}

// 运行 / 监控
export function runDag(id, source = 'published') {
  return request({ url: `/task/dag/${id}/run`, method: 'post', data: { source } })
}
export function debugDag(id) {
  return request({ url: `/task/dag/${id}/debug`, method: 'post' })
}
export function dagRunStatus(runId) {
  return request({ url: `/task/dag/run/${runId}`, method: 'get' })
}
export function listRuns(id) {
  return request({ url: `/task/dag/${id}/runs`, method: 'get' })
}
export function nodeHistory(id, nodeKey) {
  return request({ url: `/task/dag/${id}/node/${nodeKey}/history`, method: 'get' })
}
export function runNode(id, nodeKey) {
  return request({ url: `/task/dag/${id}/node/${nodeKey}/run`, method: 'post' })
}
