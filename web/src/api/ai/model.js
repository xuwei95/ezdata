import request from "@/utils/request";

// 查询AI模型列表
export function listModel(query) {
  return request({
    url: "/ai/model/list",
    method: "get",
    params: query,
  });
}

// 查询所有AI模型列表
export function listModelAll() {
  return request({
    url: "/ai/model/all",
    method: "get",
  });
}

// 查询AI模型详细
export function getModel(modelId) {
  return request({
    url: "/ai/model/" + modelId,
    method: "get",
  });
}

// 新增AI模型
export function addModel(data) {
  return request({
    url: "/ai/model",
    method: "post",
    data: data,
  });
}

// 修改AI模型
export function updateModel(data) {
  return request({
    url: "/ai/model",
    method: "put",
    data: data,
  });
}

// 删除AI模型
export function delModel(modelId) {
  return request({
    url: "/ai/model/" + modelId,
    method: "delete",
  });
}

// 测试AI模型连接(真跑一次极小补全,回连通性/时延/用量)
export function testModel(data) {
  return request({
    url: "/ai/model/test",
    method: "post",
    data: data,
  });
}
