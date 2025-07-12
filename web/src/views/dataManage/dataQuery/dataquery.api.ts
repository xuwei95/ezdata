import { defHttp } from '/@/utils/http/axios';

export enum Api {
  queryModelTree = '/datamodel/tree',
  getInfoById = '/datamodel/getInfoById',
  queryModelData = '/datamodel/query',
  previewEtl = '/datamodel/etl_preview',
  starQa = '/rag/chunk/qa/star',
}

/**
 * 获取模型树列表
 */
export const queryModelTree = (params?) => defHttp.get({ url: Api.queryModelTree, params });

/**
 * 详情接口
 * @param params
 */
export const getInfoById = (params) => defHttp.get({ url: Api.getInfoById, params });

/**
 * 数据查询接口
 * @param params
 */
export const queryData = (params) => defHttp.post({ url: Api.queryModelData, params, timeout: 60 * 1000 });
/**
 * 数据集成预览接口
 * @param params
 */
export const previewEtlData = (params) => defHttp.post({ url: Api.previewEtl, params });
/**
 * 对话标记接口
 * @param params
 */
export const starQaData = (params) => defHttp.post({ url: Api.starQa, params });
