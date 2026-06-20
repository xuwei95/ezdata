import request from '@/utils/request'

// ---------------- 知识库 ----------------
export function listDataset(query) {
  return request({ url: '/rag/dataset/list', method: 'get', params: query })
}
export function getDataset(id) {
  return request({ url: `/rag/dataset/${id}`, method: 'get' })
}
export function addDataset(data) {
  return request({ url: '/rag/dataset', method: 'post', data })
}
export function updateDataset(id, data) {
  return request({ url: `/rag/dataset/${id}`, method: 'put', data })
}
export function delDataset(ids) {
  return request({ url: `/rag/dataset/${ids}`, method: 'delete' })
}
export function vectorBackends() {
  return request({ url: '/rag/vector/backends', method: 'get' })
}

// ---------------- 文档 ----------------
export function listDocument(query) {
  return request({ url: '/rag/document/list', method: 'get', params: query })
}
export function addDocument(data) {
  return request({ url: '/rag/document', method: 'post', data })
}
export function delDocument(ids) {
  return request({ url: `/rag/document/${ids}`, method: 'delete' })
}
export function trainDocument(id) {
  return request({ url: `/rag/document/${id}/train`, method: 'post' })
}
export function documentStatus(id) {
  return request({ url: `/rag/document/${id}/status`, method: 'get' })
}

// ---------------- 分段 / QA ----------------
export function listChunk(query) {
  return request({ url: '/rag/chunk/list', method: 'get', params: query })
}
export function saveChunk(data) {
  return request({ url: '/rag/chunk', method: 'post', data })
}
export function delChunk(ids) {
  return request({ url: `/rag/chunk/${ids}`, method: 'delete' })
}
export function starChunk(id, starFlag) {
  return request({ url: `/rag/chunk/${id}/star`, method: 'post', data: { starFlag } })
}
export function bulkImportChunk(data) {
  return request({ url: '/rag/chunk/bulk_import', method: 'post', data })
}

// ---------------- 召回 ----------------
export function retrieval(data) {
  return request({ url: '/rag/retrieval', method: 'post', data })
}
