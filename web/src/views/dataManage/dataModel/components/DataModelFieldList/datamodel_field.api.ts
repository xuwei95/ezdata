import { defHttp } from '/@/utils/http/axios';
import { useMessage } from '/@/hooks/web/useMessage';

const { createConfirm } = useMessage();

enum Api {
  list = '/datamodel/field/list',
  getInfoById = '/datamodel/field/queryById',
  save = '/datamodel/field/add',
  edit = '/datamodel/field/edit',
  sync = '/datamodel/field/sync',
  deleteOne = '/datamodel/field/delete',
  deleteBatch = '/datamodel/field/deleteBatch',
  allList = '/datamodel/field/allList',
  importExcel = '/datamodel/field/importExcel',
  exportXls = '/datamodel/field/exportXls',
  syncModelFields = '/datamodel/field/sync_fields',
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
 * 同步
 */
export const syncOne = (params, handleSuccess) => {
  return defHttp.post({ url: Api.sync, params }).then(() => {
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
 * 同步模型字段
 * @param params
 */
export const syncModelFields = (params) => {
  return defHttp.post({ url: Api.syncModelFields, params });
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
