import { defHttp } from '/@/utils/http/axios';

enum Api {
  providerList        = '/llm/model/provider/list',
  providerFetchModels = '/llm/model/provider/fetch_models',
  providerSyncModels  = '/llm/model/provider/sync_models',
  modelList           = '/llm/model/list',
  modelAllList        = '/llm/model/queryAllList',
  modelAdd            = '/llm/model/add',
  modelEdit           = '/llm/model/edit',
  modelDelete         = '/llm/model/delete',
  modelSetDefault     = '/llm/model/set_default',
}

export const providerList = () => defHttp.get({ url: Api.providerList });
export const providerFetchModels = (params) => defHttp.get({ url: Api.providerFetchModels, params });
export const providerSyncModels = (params) => defHttp.post({ url: Api.providerSyncModels, params });

export const modelList = (params) => defHttp.get({ url: Api.modelList, params });
export const modelAllList = (params?) => defHttp.get({ url: Api.modelAllList, params });
export const modelAdd = (params) => defHttp.post({ url: Api.modelAdd, params });
export const modelEdit = (params) => defHttp.post({ url: Api.modelEdit, params });
export const modelDelete = (params) => defHttp.delete({ url: Api.modelDelete, data: params }, { joinParamsToUrl: true });
export const modelSetDefault = (params) => defHttp.post({ url: Api.modelSetDefault, params });

export const saveOrUpdateModel = (params, isUpdate) => isUpdate ? modelEdit(params) : modelAdd(params);
