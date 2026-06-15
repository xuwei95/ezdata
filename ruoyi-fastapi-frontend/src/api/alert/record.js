import request from '@/utils/request'

// 查询告警记录分页列表
export function listRecord(query) {
  return request({ url: '/alert/record/list', method: 'get', params: query })
}

// 标记告警处理状态
export function changeRecordStatus(alertId, status) {
  return request({ url: '/alert/record/changeStatus', method: 'put', data: { alertId, status } })
}

// 删除告警记录
export function delRecord(alertIds) {
  return request({ url: '/alert/record/' + alertIds, method: 'delete' })
}
