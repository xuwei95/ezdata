import request from '@/utils/request'

// 实时获取可用运行队列(在线 worker 正在消费的队列)
export function listRunQueues() {
  return request({
    url: '/task/info/queues',
    method: 'get'
  })
}

// 查询任务分页列表
export function listTask(query) {
  return request({
    url: '/task/info/list',
    method: 'get',
    params: query
  })
}

// 查询任务详情
export function getTask(taskId) {
  return request({
    url: '/task/info/' + taskId,
    method: 'get'
  })
}

// 新增任务
export function addTask(data) {
  return request({
    url: '/task/info',
    method: 'post',
    data: data
  })
}

// 修改任务
export function updateTask(data) {
  return request({
    url: '/task/info',
    method: 'put',
    data: data
  })
}

// 删除任务
export function delTask(taskIds) {
  return request({
    url: '/task/info/' + taskIds,
    method: 'delete'
  })
}

// 修改任务状态(启用/停用)
export function changeTaskStatus(id, status) {
  const data = { id, status }
  return request({
    url: '/task/info/changeStatus',
    method: 'put',
    data: data
  })
}

// 手动执行一次任务
export function runTask(taskId) {
  return request({
    url: '/task/info/run/' + taskId,
    method: 'put'
  })
}
