import request from "@/utils/request";

// 查询AI工具列表
export function listTool(query) {
  return request({
    url: "/ai/tool/list",
    method: "get",
    params: query,
  });
}

// 查询AI工具详细
export function getTool(toolId) {
  return request({
    url: "/ai/tool/" + toolId,
    method: "get",
  });
}

// 新增AI工具
export function addTool(data) {
  return request({
    url: "/ai/tool",
    method: "post",
    data: data,
  });
}

// 修改AI工具
export function updateTool(data) {
  return request({
    url: "/ai/tool",
    method: "put",
    data: data,
  });
}

// 删除AI工具
export function delTool(toolId) {
  return request({
    url: "/ai/tool/" + toolId,
    method: "delete",
  });
}

// 测试MCP工具连接
export function testTool(data) {
  return request({
    url: "/ai/tool/test",
    method: "post",
    data: data,
  });
}
