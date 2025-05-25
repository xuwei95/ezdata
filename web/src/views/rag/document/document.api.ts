import { defHttp } from '/@/utils/http/axios';
import { useMessage } from '/@/hooks/web/useMessage';

const { createConfirm } = useMessage();

enum Api {
  list = '/rag/document/list',
  allList = '/rag/document/queryAllList',
  getInfoById = '/rag/document/queryById',
  save = '/rag/document/add',
  edit = '/rag/document/edit',
  deleteOne = '/rag/document/delete',
  deleteBatch = '/rag/document/deleteBatch',
  train = '/rag/document/train',
}
/**
 * 列表接口
 * @param params
 */
export const list = (params) => defHttp.get({ url: Api.list, params });
/**
 * 全量列表接口
 * @param params
 */
export const allList = (params) => defHttp.get({ url: Api.allList, params });
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
 * 训练知识库
 * @param params
 */
export const train = (params, handleSuccess) => {
  return defHttp.post({ url: Api.train, params }).then(() => {
    handleSuccess();
  });
};
