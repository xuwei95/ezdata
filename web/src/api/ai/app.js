import request from "@/utils/request";

// 查询AI应用列表
export function listApp(query) {
  return request({ url: "/ai/app/list", method: "get", params: query });
}

// 查询所有AI应用(不分页)
export function listAppAll() {
  return request({ url: "/ai/app/all", method: "get" });
}

// 查询AI应用详细
export function getApp(appId) {
  return request({ url: "/ai/app/" + appId, method: "get" });
}

// 新增AI应用
export function addApp(data) {
  return request({ url: "/ai/app", method: "post", data });
}

// 修改AI应用
export function updateApp(data) {
  return request({ url: "/ai/app", method: "put", data });
}

// 删除AI应用
export function delApp(appId) {
  return request({ url: "/ai/app/" + appId, method: "delete" });
}

// AI 生成系统提示词
export function generatePrompt(data) {
  return request({ url: "/ai/app/prompt/generate", method: "post", data });
}

// 应用 APIKey 列表
export function listAppTokens(appId) {
  return request({ url: "/ai/app/token/list", method: "get", params: { appId } });
}

// 生成应用 APIKey
export function createAppToken(data) {
  return request({ url: "/ai/app/token", method: "post", data });
}

// 启停应用 APIKey
export function setAppTokenStatus(data) {
  return request({ url: "/ai/app/token/status", method: "put", data });
}

// 删除应用 APIKey
export function delAppToken(tokenId) {
  return request({ url: "/ai/app/token/" + tokenId, method: "delete" });
}
