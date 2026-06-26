import request from "@/utils/request";

// AI 用量总览(token/时延/模型/用户)
export function getAiMetricsOverview(days) {
  return request({
    url: "/ai/metrics/overview",
    method: "get",
    params: { days: days || 7 },
  });
}
