import request from '@/utils/request'

// 控制台概览
export function getOverview() {
  return request({ url: '/dashboard/overview', method: 'get' })
}
