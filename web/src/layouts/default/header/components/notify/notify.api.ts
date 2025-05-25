import { defHttp } from '/@/utils/http/axios';

enum Api {
  listCementByUser = '/sys/notice/listByUser',
  editCementSend = '/sys/notice/send/edit',
  clearAllUnReadMessage = '/sys/annountCement/clearAllUnReadMessage',
}

/**
 * 列表接口
 * @param params
 */
export const listCementByUser = (params?) => defHttp.get({ url: Api.listCementByUser, params });

export const editCementSend = (anntId, params?) => defHttp.put({ url: Api.editCementSend, params: { anntId, ...params } });

/**
 * 清空全部未读消息
 */
export const clearAllUnReadMessage = () => defHttp.post({ url: Api.clearAllUnReadMessage },{ isTransformResponse: false });
