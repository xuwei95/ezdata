import request from '@/utils/request'

// 通用 apikey 管理:数据接口(data_api)/ agent 对话等用途共用。tokenType 区分用途,refId 绑定资源。
export function listToken(query) {
  return request({ url: '/apitoken/list', method: 'get', params: query })
}
export function addToken(data) {
  return request({ url: '/apitoken', method: 'post', data })
}
export function delToken(ids) {
  return request({ url: '/apitoken/' + ids, method: 'delete' })
}
