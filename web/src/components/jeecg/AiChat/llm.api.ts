import { defHttp } from '/@/utils/http/axios';

enum Api {
  toolList = '/llm/tool/list',
}
/**
 * 列表接口
 * @param params
 */
export const toolList = (params) => defHttp.get({ url: Api.toolList, params });
