import request from '@/utils/request'

// 查询告警策略分页列表
export function listStrategy(query) {
  return request({ url: '/alert/strategy/list', method: 'get', params: query })
}

// 查询启用的告警策略(不分页,供任务绑定)
export function listStrategyAll() {
  return request({ url: '/alert/strategy/all', method: 'get' })
}

// 查询告警策略详情
export function getStrategy(strategyId) {
  return request({ url: '/alert/strategy/' + strategyId, method: 'get' })
}

// 新增告警策略
export function addStrategy(data) {
  return request({ url: '/alert/strategy', method: 'post', data })
}

// 修改告警策略
export function updateStrategy(data) {
  return request({ url: '/alert/strategy', method: 'put', data })
}

// 删除告警策略
export function delStrategy(strategyIds) {
  return request({ url: '/alert/strategy/' + strategyIds, method: 'delete' })
}
