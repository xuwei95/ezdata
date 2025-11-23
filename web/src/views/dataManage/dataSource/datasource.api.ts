import { defHttp } from '/@/utils/http/axios';
import { useMessage } from '/@/hooks/web/useMessage';

const { createConfirm } = useMessage();

enum Api {
  list = '/datasource/list',
  getInfoById = '/datasource/queryById',
  save = '/datasource/add',
  edit = '/datasource/edit',
  deleteOne = '/datasource/delete',
  deleteBatch = '/datasource/deleteBatch',
  allList = '/datasource/queryAllList',
  importExcel = '/datasource/importExcel',
  exportXls = '/datasource/exportXls',
  connTest = '/datasource/connect',
  syncModels = '/datasource/sync_models',
  types = '/datasource/types',
  config = '/datasource/config',
}
/**
 * 列表接口
 * @param params
 */
export const list = (params) => {
  return defHttp.get({ url: Api.list, params }).catch((error) => {
    console.error('获取数据源列表失败:', error);
    throw error;
  });
};
/**
 * 详情接口
 * @param params
 */
export const getInfoById = (params) => defHttp.get({ url: Api.getInfoById, params });
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
/**
 * 连接测试
 * @param params
 */
export const ConnTest = (params) => {
  return defHttp.post({ url: Api.connTest, params, timeout: 60 * 1000 });
};

/**
 * 同步数据模型
 */
export const syncModels = (params) => {
  return defHttp.post({ url: Api.syncModels, params, timeout: 60 * 1000 });
};

/**
 * 获取所有数据源类型
 */
export const getDataSourceTypes = (params?) => defHttp.get({ url: Api.types, params });

/**
 * 根据数据源类型获取连接配置
 */
export const getDataSourceConfig = (type: string) => defHttp.get({ url: `${Api.config}/${type}` });
