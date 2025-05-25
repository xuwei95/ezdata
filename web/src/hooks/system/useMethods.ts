import { defHttp } from '/@/utils/http/axios';
import { useMessage } from '/@/hooks/web/useMessage';
import { useGlobSetting } from '/@/hooks/setting';

const { createMessage, createWarningModal } = useMessage();
const glob = useGlobSetting();
import * as XLSX from 'xlsx';

/**
 * 导出文件xlsx的mime-type
 */
export const XLSX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
/**
 * 导出文件xlsx的文件后缀
 */
export const XLSX_FILE_SUFFIX = '.xlsx';

export function useMethods() {
  /**
   * 导出xls
   * @param name
   * @param url
   */
  async function exportXls(name, url, params, isXlsx = false) {
    //update-begin---author:wangshuai---date:2024-01-25---for:【QQYUN-8118】导出超时时间设置长点---
    const data = await defHttp.get({ url: url, params: params, responseType: 'blob', timeout: 60000 }, { isTransformResponse: false });
    //update-end---author:wangshuai---date:2024-01-25---for:【QQYUN-8118】导出超时时间设置长点---
    if (!data) {
      createMessage.warning('文件下载失败');
      return;
    }
    if (!name || typeof name != 'string') {
      name = '导出文件';
    }
    let blobOptions = { type: 'application/vnd.ms-excel' };
    let fileSuffix = '.xls';
    if (isXlsx === true) {
      blobOptions['type'] = XLSX_MIME_TYPE;
      fileSuffix = XLSX_FILE_SUFFIX;
    }
    if (typeof window.navigator.msSaveBlob !== 'undefined') {
      window.navigator.msSaveBlob(new Blob([data], blobOptions), name + fileSuffix);
    } else {
      let url = window.URL.createObjectURL(new Blob([data], blobOptions));
      let link = document.createElement('a');
      link.style.display = 'none';
      link.href = url;
      link.setAttribute('download', name + fileSuffix);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link); //下载完成移除元素
      window.URL.revokeObjectURL(url); //释放掉blob对象
    }
  }
  /**
   * 导出数据列表到excel
   * @param name
   * @param dataList
   */
  async function handleExportExcel(name, dataList) {
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(dataList); // dataArray是要导出的数据数组
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1'); // 'Sheet1'是工作表的名称
    const buffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    if (!name || typeof name != 'string') {
      name = '导出文件';
    }
    const data = new Blob([buffer], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(data);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', name);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  /**
   * 导入xls
   * @param data 导入的数据
   * @param url
   * @param success 成功后的回调
   */
  async function importXls(data, url, success) {
    const isReturn = (fileInfo) => {
      try {
        if (fileInfo.code === 201) {
          let {
            message,
            result: { msg, fileUrl, fileName },
          } = fileInfo;
          let href = glob.uploadUrl + fileUrl;
          createWarningModal({
            title: message,
            centered: false,
            content: `<div>
                                <span>${msg}</span><br/> 
                                <span>具体详情请<a href = ${href} download = ${fileName}> 点击下载 </a> </span> 
                              </div>`,
          });
          //update-begin---author:wangshuai ---date:20221121  for：[VUEN-2827]导入无权限，提示图标错误------------
        } else if (fileInfo.code === 500 || fileInfo.code === 510) {
          createMessage.error(fileInfo.message || `${data.file.name} 导入失败`);
          //update-end---author:wangshuai ---date:20221121  for：[VUEN-2827]导入无权限，提示图标错误------------
        } else {
          createMessage.success(fileInfo.message || `${data.file.name} 文件上传成功`);
        }
      } catch (error) {
        console.log('导入的数据异常', error);
      } finally {
        typeof success === 'function' ? success(fileInfo) : '';
      }
    };
    await defHttp.uploadFile({ url }, { file: data.file }, { success: isReturn });
  }

  return {
    handleExportExcel,
    handleExportXls: (name: string, url: string, params?: object) => exportXls(name, url, params),
    handleImportXls: (data, url, success) => importXls(data, url, success),
    handleExportXlsx: (name: string, url: string, params?: object) => exportXls(name, url, params, true),
  };
}
