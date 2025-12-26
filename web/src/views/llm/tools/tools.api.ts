import { defHttp } from '/@/utils/http/axios';
import { useMessage } from '/@/hooks/web/useMessage';

const { createConfirm } = useMessage();

enum Api {
  list = '/llm/tool/list',
  getInfoById = '/llm/tool',
  save = '/llm/tool/add',
  edit = '/llm/tool/edit',
  deleteOne = '/llm/tool/delete',
  test = '/llm/tool/test',
  types = '/llm/tool/types',
  queryAllList = '/llm/tool/queryAllList',
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
export const getInfoById = (params) => defHttp.get({ url: `${Api.getInfoById}/${params.id}` });

/**
 * 删除单个
 */
export const deleteOne = (params, handleSuccess) => {
  return defHttp.delete({ url: Api.deleteOne, data: params }, { joinParamsToUrl: true }).then(() => {
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
      return defHttp.delete({ url: Api.deleteOne, data: params }, { joinParamsToUrl: true }).then(() => {
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
 * 测试工具
 * @param params
 */
export const testTool = (params) => {
  return defHttp.post({ url: Api.test, params });
};

/**
 * 获取工具类型列表
 */
export const getToolTypes = () => defHttp.get({ url: Api.types });

/**
 * 查询所有工具列表（内置工具 + 数据库工具）
 * 用于下拉选择
 */
export const queryAllList = () => defHttp.get({ url: Api.queryAllList });
