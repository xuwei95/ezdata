import json
from utils.common_utils import gen_json_to_dict_code


def gen_api_code(params):
    '''
    生成api代码
    :param params:
    :return:
    '''
    base_code = """
import { defHttp } from '/@/utils/http/axios';
import { useMessage } from '/@/hooks/web/useMessage';

const { createConfirm } = useMessage();

enum Api {
  list = '/${module_name}/list',
  getInfoById = '/${module_name}/queryById',
  save = '/${module_name}/add',
  edit = '/${module_name}/edit',
  deleteOne = '/${module_name}/delete',
  deleteBatch = '/${module_name}/deleteBatch',
  ${other_api_urls}
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
${other_api_code}
    """
    module_name = params.get('module_name')
    all_list_params = [i for i in params['buttons'] if i['function'] == 'onImportXls']
    if all_list_params != []:
        all_list_api_url = "allList = '/${module_name}/queryAllList',"
        all_list_api_code = """
/**
 * 全量列表接口
 * @param params
 */
export const allList = (params) => defHttp.get({ url: Api.allList, params });
        """
    else:
        all_list_api_url = ""
        all_list_api_code = ""
    importExcel_params = [i for i in params['buttons'] if i['function'] == 'onImportXls']
    if importExcel_params != []:
        importExcel_api_url = "importExcel = '/${module_name}/importExcel',"
        importExcel_api_code = """
/**
 * 导入api
 */
export const getImportUrl = Api.importExcel;
            """
    else:
        importExcel_api_url = ""
        importExcel_api_code = ""
    exportXls_params = [i for i in params['buttons'] if i['function'] == 'onExportXls']
    if exportXls_params != []:
        exportXls_api_url = "exportXls = '/${module_name}/exportXls',"
        exportXls_api_code = """
/**
 * 导出api
 * @param params
 */
export const getExportUrl = Api.exportXls;
                """
    else:
        exportXls_api_url = ""
        exportXls_api_code = ""
    other_api_urls = f"""
  {all_list_api_url}
  {importExcel_api_url}
  {exportXls_api_url}
    """

    other_api_code = f"""
{all_list_api_code.strip()}
{importExcel_api_code.strip()}
{exportXls_api_code.strip()}
   """
    res_code = base_code.replace('${other_api_urls}', other_api_urls.strip())
    res_code = res_code.replace('${other_api_code}', other_api_code.strip())
    res_code = res_code.replace('${module_name}', module_name).strip() + '\n'
    return res_code


if __name__ == '__main__':
    from web_apps.code_generator.db_models import CodeGenModel, db
    obj = db.session.query(CodeGenModel).filter(CodeGenModel.id == '5deb88593c024033ae6de2f9ed5e7806').first()
    params = obj.to_dict()
    params['fields'] = json.loads(params['fields'])
    params['query_params'] = json.loads(params['query_params'])
    params['buttons'] = json.loads(params['buttons'])
    print(params)
    api_code = gen_api_code(params)
    print(api_code)
    f = open('out/api.ts', 'w')
    f.write(api_code)
