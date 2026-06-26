<template>
  <div class="app-container" v-loading="loading">
    <div class="ai-metrics-bar">
      <span class="title">AI 用量可观测</span>
      <el-radio-group v-model="days" size="small" @change="load">
        <el-radio-button :value="1">今日</el-radio-button>
        <el-radio-button :value="7">7 天</el-radio-button>
        <el-radio-button :value="30">30 天</el-radio-button>
        <el-radio-button :value="90">90 天</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 指标卡 -->
    <el-row :gutter="12" class="stat-row">
      <el-col :span="4"><div class="stat"><div class="v">{{ fmt(totals.totalTokens) }}</div><div class="l">总 Token</div></div></el-col>
      <el-col :span="4"><div class="stat"><div class="v">{{ fmt(totals.inputTokens) }}</div><div class="l">输入 Token</div></div></el-col>
      <el-col :span="4"><div class="stat"><div class="v">{{ fmt(totals.outputTokens) }}</div><div class="l">输出 Token</div></div></el-col>
      <el-col :span="4"><div class="stat"><div class="v">{{ totals.sessions }}</div><div class="l">会话数</div></div></el-col>
      <el-col :span="4"><div class="stat"><div class="v">{{ totals.runs }}</div><div class="l">对话轮次</div></div></el-col>
      <el-col :span="4"><div class="stat"><div class="v">{{ totals.avgDuration }}s<small> · {{ totals.successRate }}%</small></div><div class="l">平均时长 · 成功率</div></div></el-col>
    </el-row>

    <!-- 趋势 -->
    <div class="panel">
      <div class="panel-title">用量趋势(按天)</div>
      <div ref="trendRef" class="chart"></div>
    </div>

    <el-row :gutter="12">
      <el-col :span="12">
        <div class="panel">
          <div class="panel-title">按模型</div>
          <el-table :data="byModel" size="small" border>
            <el-table-column label="模型" prop="model" show-overflow-tooltip />
            <el-table-column label="轮次" prop="runs" width="90" align="center" />
            <el-table-column label="Token" width="130" align="right"><template #default="s">{{ fmt(s.row.tokens) }}</template></el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="panel">
          <div class="panel-title">按用户(Top 10)</div>
          <el-table :data="byUser" size="small" border>
            <el-table-column label="用户" prop="userName" show-overflow-tooltip />
            <el-table-column label="轮次" prop="runs" width="90" align="center" />
            <el-table-column label="Token" width="130" align="right"><template #default="s">{{ fmt(s.row.tokens) }}</template></el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="AiMetrics">
import { ref, reactive, nextTick, onMounted, onBeforeUnmount } from "vue";
import * as echarts from "echarts";
import { getAiMetricsOverview } from "@/api/ai/metrics";

const loading = ref(false);
const days = ref(7);
const totals = reactive({ totalTokens: 0, inputTokens: 0, outputTokens: 0, sessions: 0, runs: 0, avgDuration: 0, successRate: 0 });
const byModel = ref([]);
const byUser = ref([]);
const trendRef = ref(null);
let trendChart = null;

function fmt(n) {
  n = Number(n || 0);
  if (n >= 1e8) return (n / 1e8).toFixed(2) + "亿";
  if (n >= 1e4) return (n / 1e4).toFixed(1) + "万";
  return String(n);
}

function renderTrend(series) {
  if (!trendRef.value) return;
  if (!trendChart) trendChart = echarts.init(trendRef.value);
  trendChart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["Token", "轮次"], right: 10 },
    grid: { left: 50, right: 50, top: 30, bottom: 30 },
    xAxis: { type: "category", data: series.map((s) => s.date) },
    yAxis: [
      { type: "value", name: "Token" },
      { type: "value", name: "轮次" },
    ],
    series: [
      { name: "Token", type: "line", smooth: true, areaStyle: {}, data: series.map((s) => s.tokens) },
      { name: "轮次", type: "bar", yAxisIndex: 1, data: series.map((s) => s.runs) },
    ],
  });
}

function load() {
  loading.value = true;
  getAiMetricsOverview(days.value)
    .then((res) => {
      const d = res.data || {};
      Object.assign(totals, d.totals || {});
      byModel.value = d.byModel || [];
      byUser.value = d.byUser || [];
      nextTick(() => renderTrend(d.series || []));
    })
    .finally(() => (loading.value = false));
}

function onResize() {
  trendChart && trendChart.resize();
}
onMounted(() => {
  load();
  window.addEventListener("resize", onResize);
});
onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  trendChart && trendChart.dispose();
});
</script>

<style scoped lang="scss">
.ai-metrics-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  .title { font-size: 16px; font-weight: 600; }
}
.stat-row { margin-bottom: 12px; }
.stat {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 14px 16px;
  .v { font-size: 22px; font-weight: 600; color: var(--el-color-primary); small { font-size: 13px; color: var(--el-text-color-secondary); } }
  .l { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px; }
}
.panel {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
  .panel-title { font-size: 14px; font-weight: 600; margin-bottom: 10px; }
  .chart { height: 320px; }
}
</style>
