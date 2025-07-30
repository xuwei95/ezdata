import { defHttp } from '/@/utils/http/axios';
import { Modal } from 'ant-design-vue';

export enum Api {
  //知识库管理
  list = '/llm/chat_app/list',
  save = '/llm/chat_app/edit',
  release = '/llm/chat_app/release',
  delete = '/llm/chat_app/delete',
  queryById = '/llm/chat_app/queryById',
  queryBathById = '/rag/dataset/queryAllList',
  queryFlowById = '/airag/flow/queryById',
  promptGenerate = '/llm/chat_app/app/prompt/generate',
  // 数据模型和工具批量查询
  queryDataModelBatchById = '/datamodel/queryAllList',
  queryToolBatchById = '/llm/tool/list',

}

/**
 * 查询应用
 * @param params
 */
export const appList = (params) => {
  return defHttp.get({ url: Api.list, params }, { isTransformResponse: false });
};
/**
 * 查询应用
 * @param params
 */
export const toolList = (params) => {
  return defHttp.get({ url: Api.queryToolBatchById, params }, { isTransformResponse: false });
};
/**
 * 查询知识库
 * @param params
 */
export const queryKnowledgeBathById = (params) => {
  return defHttp.get({ url: Api.queryBathById, params }, { isTransformResponse: false });
};

/**
 * 根据应用id查询应用
 * @param params
 */
export const queryById = (params) => {
  return defHttp.get({ url: Api.queryById, params }, { isTransformResponse: false });
};

/**
 * 新增应用
 * @param params
 */
export const saveApp = (params) => {
  return defHttp.post({ url: Api.save, params });
};

// 发布应用
export function releaseApp(appId: string, release = false) {
  return defHttp.post({
    url: Api.release,
    params: {
      id: appId,
      release: release,
    }
  }, {joinParamsToUrl: true});
}

/**
 * 删除应用
 * @param params
 * @param handleSuccess
 */
export const deleteApp = (params, handleSuccess) => {
  Modal.confirm({
    title: '确认删除',
    content: '是否删除名称为'+params.name+'的应用吗？',
    okText: '确认',
    cancelText: '取消',
    onOk: () => {
      return defHttp.delete({ url: Api.delete, params }, { joinParamsToUrl: true }).then(() => {
        handleSuccess();
      });
    },
  });
};


/**
 * 根据应用id查询流程
 * @param params
 */
export const queryFlowById = (params) => {
  return defHttp.get({ url: Api.queryFlowById, params }, { isTransformResponse: false });
};

/**
 * 批量查询数据模型
 * @param params
 */
export const queryDataModelBatchById = (params) => {
  return defHttp.get({ url: Api.queryDataModelBatchById, params }, { isTransformResponse: false });
};

/**
 * 批量查询工具
 * @param params
 */
export const queryToolBatchById = (params) => {
  return defHttp.get({ url: Api.queryToolBatchById, params }, { isTransformResponse: false });
};

/**
 * 应用编排
 * @param params
 */
export const promptGenerate = (params) => {
  return defHttp.post(
    {
      url: Api.promptGenerate+'?prompt='+ params.prompt,
      adapter: 'fetch',
      responseType: 'stream',
      timeout: 5 * 60 * 1000,
    },
    {
      isTransformResponse: false,
    }
  );
};
