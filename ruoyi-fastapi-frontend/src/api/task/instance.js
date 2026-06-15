import request from '@/utils/request'

// 查询任务执行记录分页列表
export function listInstance(query) {
  return request({
    url: '/task/instance/list',
    method: 'get',
    params: query
  })
}

// 查询执行记录详情
export function getInstance(instanceId) {
  return request({
    url: '/task/instance/' + instanceId,
    method: 'get'
  })
}

// 终止正在运行的执行实例
export function stopInstance(instanceId) {
  return request({
    url: '/task/instance/stop/' + instanceId,
    method: 'put'
  })
}

// 删除执行记录
export function delInstance(instanceIds) {
  return request({
    url: '/task/instance/' + instanceIds,
    method: 'delete'
  })
}
