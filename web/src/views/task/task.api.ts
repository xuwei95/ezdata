import { defHttp } from '/@/utils/http/axios';
import { useMessage } from '/@/hooks/web/useMessage';

const { createConfirm } = useMessage();

enum Api {
  resetAllJob = '/task/resetAllJob',
  startTask = '/task/start',
  templateParams = '/task/template/params',
  instanceList = '/task/instance/list',
  taskLogs = '/task/instance/logs',
  list = '/task/list',
  daglist = '/task/dag/list',
  dagMenu = '/task/dag/menu',
  dagNodeStatus = '/task/dag/node/status',
  getInfoById = '/task/queryById',
  getParamsById = '/task/queryParamsById',
  save = '/task/add',
  edit = '/task/edit',
  statusUpdate = '/task/status',
  deleteOne = '/task/delete',
  deleteBatch = '/task/deleteBatch',
  allList = '/task/queryAllList',
  importExcel = '/task/importExcel',
  exportXls = '/task/exportXls',
}
/**
 * 列表接口
 * @param params
 */
export const list = (params) => defHttp.get({ url: Api.list, params });
/**
 * 任务执行历史列表接口
 * @param params
 */
export const instanceList = (params) => defHttp.get({ url: Api.instanceList, params });
/**
 * 任务日志接口
 * @param params
 */
export const taskLogs = (params) => defHttp.get({ url: Api.taskLogs, params });
/**
 * dag 任务列表接口
 * @param params
 */
export const dagList = (params) => defHttp.get({ url: Api.daglist, params });
/**
 * dag 任务菜单接口
 * @param params
 */
export const dagMenu = (params) => defHttp.get({ url: Api.dagMenu, params });
/**
 * dag 任务节点状态接口
 * @param params
 */
export const dagNodeStatus = (params) => defHttp.get({ url: Api.dagNodeStatus, params });
/**
 * 根据模版获取参数
 * @param params
 */
export const getTemplateParams = (params) => defHttp.get({ url: Api.templateParams, params });
/**
 * 详情接口
 * @param params
 */
export const getInfoById = (params) => defHttp.get({ url: Api.getInfoById, params });
/**
 * 参数详情接口
 * @param params
 */
export const getParamsById = (params) => defHttp.get({ url: Api.getParamsById, params });
/**
 * 开始所有定时任务
 * @param params
 */
export const resetAllJob = (params) => {
  return defHttp.post({ url: Api.resetAllJob, params });
};
/**
 * 开始任务
 * @param params
 */
export const startTask = (params) => {
  return defHttp.post({ url: Api.startTask, params });
};
/**
 * 更新状态
 * @param params
 */
export const UpdateStatus = (params, handleSuccess) => {
  return defHttp.post({ url: Api.statusUpdate, params }).then(() => {
    handleSuccess();
  });
};
/**
 * 删除单个
 */
export const deleteOne = (params, handleSuccess) => {
  return defHttp.delete({ url: Api.deleteOne, params }, { joinParamsToUrl: true }).then(() => {
    handleSuccess();
  });
};
/**
 * 批量删除
 * @param params
 */
export const batchDelete = (params, handleSuccess) => {
  createConfirm({
    iconType: 'warning',
    title: '确认删除',
    content: '是否删除选中数据',
    okText: '确认',
    cancelText: '取消',
    onOk: () => {
      return defHttp.delete({ url: Api.deleteBatch, data: params }, { joinParamsToUrl: true }).then(() => {
        handleSuccess();
      });
    },
  });
};
/**
 * 保存或者更新
 * @param params
 */
export const saveOrUpdate = (params, isUpdate) => {
  const url = isUpdate ? Api.edit : Api.save;
  return defHttp.post({ url: url, params });
};
/**
 * 全量列表接口
 * @param params
 */
export const allList = (params) => defHttp.get({ url: Api.allList, params });
/**
 * 导入api
 */
export const getImportUrl = Api.importExcel;
/**
 * 导出api
 * @param params
 */
export const getExportUrl = Api.exportXls;
