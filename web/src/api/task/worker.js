import request from '@/utils/request'

// 获取 Worker 列表(实时)
export function listWorkers() {
  return request({ url: '/task/worker/list', method: 'get' })
}

// 获取 Worker 当前运行任务
export function listWorkerTasks(worker) {
  return request({ url: '/task/worker/tasks', method: 'get', params: { worker } })
}

// 增加消费队列
export function addConsumer(data) {
  return request({ url: '/task/worker/consumer/add', method: 'put', data })
}

// 移除消费队列
export function cancelConsumer(data) {
  return request({ url: '/task/worker/consumer/cancel', method: 'put', data })
}

// 增加并发
export function poolGrow(data) {
  return request({ url: '/task/worker/pool/grow', method: 'put', data })
}

// 减少并发
export function poolShrink(data) {
  return request({ url: '/task/worker/pool/shrink', method: 'put', data })
}

// 设置弹性并发
export function autoscale(data) {
  return request({ url: '/task/worker/pool/autoscale', method: 'put', data })
}
