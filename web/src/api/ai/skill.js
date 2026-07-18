import request from "@/utils/request";

// 查询AI技能列表
export function listSkill(query) {
  return request({
    url: "/ai/skill/list",
    method: "get",
    params: query,
  });
}

// 查询AI技能详细
export function getSkill(skillId) {
  return request({
    url: "/ai/skill/" + skillId,
    method: "get",
  });
}

// 新增AI技能
export function addSkill(data) {
  return request({
    url: "/ai/skill",
    method: "post",
    data: data,
  });
}

// 修改AI技能
export function updateSkill(data) {
  return request({
    url: "/ai/skill",
    method: "put",
    data: data,
  });
}

// 删除AI技能
export function delSkill(skillId) {
  return request({
    url: "/ai/skill/" + skillId,
    method: "delete",
  });
}
