import { defHttp } from '/@/utils/http/axios';

enum Api {
  loginfo = '/sys/loginfo',
  visitInfo = '/sys/visit/count',
  taskInfo = '/sys/task/count',
  dashboardInfo = '/sys/dashboard/count',
  datamodelTypeInfo = '/sys/datamodel/type/count',
  interfaceInfo = '/sys/interface/count',
  taskStatusInfo = '/sys/task/status/count',
}
/**
 * 日志统计信息
 * @param params
 */
export const getLoginfo = (params) => defHttp.get({ url: Api.loginfo, params }, { isTransformResponse: false });
/**
 * 访问量信息
 * @param params
 */
export const getVisitInfo = (params) => defHttp.get({ url: Api.visitInfo, params }, { isTransformResponse: false });
/**
 * 任务信息
 * @param params
 */
export const getTaskInfo = (params) => defHttp.get({ url: Api.taskInfo, params }, { isTransformResponse: false });

/**
 * dashboard统计信息
 * @param params
 */
export const getDashboardInfo = (params) => defHttp.get({ url: Api.dashboardInfo, params }, { isTransformResponse: false });
/**
 * 数据模型统计信息
 * @param params
 */
export const getDataModelTypeInfo = (params) => defHttp.get({ url: Api.datamodelTypeInfo, params }, { isTransformResponse: false });
/**
 * 任务状态统计信息
 * @param params
 */
export const getTaskStatusInfo = (params) => defHttp.get({ url: Api.taskStatusInfo, params }, { isTransformResponse: false });
/**
 * 数据接口调用统计信息
 * @param params
 */
export const getInterfaceInfo = (params) => defHttp.get({ url: Api.interfaceInfo, params }, { isTransformResponse: false });
