import { defHttp } from '/@/utils/http/axios';

enum Api {
  list = '/scheduler/celery/worker/base/list',
  getInfoById = '/scheduler/celery/worker/list',
  stopTask = '/scheduler/celery/task/stop',
  addQueue = '/scheduler/celery/worker/queue/add',
  delQueue = '/scheduler/celery/worker/queue/delete',
  addConcurrency = '/scheduler/celery/worker/concurrency/add',
  reduceConcurrency = '/scheduler/celery/worker/concurrency/reduce',
}
/**
 * 列表接口
 * @param params
 */
export const list = (params) => defHttp.get({ url: Api.list, params });
/**
 * 详情接口
 * @param params
 */
export const getInfoById = (params) => defHttp.get({ url: Api.getInfoById, params });
/**
 * 停止单个任务
 */
export const stopTask = (params) => {
  return defHttp.post({ url: Api.stopTask, params }).then(() => {});
};
/**
 * 添加队列
 */
export const addQueue = (params) => {
  return defHttp.post({ url: Api.addQueue, params }).then(() => {});
};
/**
 * 删除队列
 */
export const delQueue = (params) => {
  return defHttp.post({ url: Api.delQueue, params }).then(() => {});
};
/**
 * 增加并发
 */
export const addConcurrency = (params) => {
  return defHttp.post({ url: Api.addConcurrency, params }).then(() => {});
};
/**
 * 减少并发
 */
export const reduceConcurrency = (params) => {
  return defHttp.post({ url: Api.reduceConcurrency, params }).then(() => {});
};
