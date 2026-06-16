import request from '@/utils/request'

// 查询任务模板分页列表
export function listTemplate(query) {
  return request({
    url: '/task/template/list',
    method: 'get',
    params: query
  })
}

// 查询启用的任务模板(不分页,供任务表单选择)
export function listTemplateAll() {
  return request({
    url: '/task/template/all',
    method: 'get'
  })
}

// 查询任务模板详情
export function getTemplate(templateId) {
  return request({
    url: '/task/template/' + templateId,
    method: 'get'
  })
}

// 新增任务模板
export function addTemplate(data) {
  return request({
    url: '/task/template',
    method: 'post',
    data: data
  })
}

// 修改任务模板
export function updateTemplate(data) {
  return request({
    url: '/task/template',
    method: 'put',
    data: data
  })
}

// 删除任务模板
export function delTemplate(templateIds) {
  return request({
    url: '/task/template/' + templateIds,
    method: 'delete'
  })
}
