import { defHttp } from '/@/utils/http/axios';

enum Api {
  list = '/sys/log/query',
  getInfoById = '/log/queryById',
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
// /**
//  * 删除单个
//  */
// export const deleteOne = (params, handleSuccess) => {
//   return defHttp.delete({ url: Api.deleteOne, params }, { joinParamsToUrl: true }).then(() => {
//     handleSuccess();
//   });
// };
