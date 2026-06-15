import request from '@/utils/request'

// 任务执行明细日志是否支持在线查看(file后端返回false)
export function getTaskLogViewable() {
  return request({
    url: '/task/log/viewable',
    method: 'get'
  })
}

// 按执行实例ID分页查询任务执行明细日志
export function listTaskLog(query) {
  return request({
    url: '/task/log/list',
    method: 'get',
    params: query
  })
}
