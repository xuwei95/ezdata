<template>
  <div class="dash" v-loading="loading">
    <!-- 概览统计卡 -->
    <el-row :gutter="16">
      <el-col :span="6" v-for="c in statCards" :key="c.key">
        <el-card shadow="hover" class="stat" :body-style="{ padding: '16px' }" @click="go(c.to)">
          <div class="stat-row">
            <el-icon class="stat-ico" :style="{ background: c.color + '1f', color: c.color }"><component :is="c.icon" /></el-icon>
            <div class="stat-main">
              <div class="stat-num">{{ c.value }}</div>
              <div class="stat-label">{{ c.label }}</div>
            </div>
          </div>
          <div class="stat-sub">{{ c.sub || ' ' }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 任务趋势 + 快捷入口 -->
    <el-row :gutter="16" class="mt16">
      <el-col :span="16">
        <el-card shadow="never" header="任务运行趋势(近 7 天)">
          <div ref="trendRef" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" header="快捷入口">
          <div class="quick">
            <div class="quick-item" v-for="q in quickNav" :key="q.to" @click="go(q.to)">
              <el-icon :style="{ color: q.color }"><component :is="q.icon" /></el-icon>
              <span>{{ q.label }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 任务状态 + AI 用量趋势 + 资产分布 -->
    <el-row :gutter="16" class="mt16">
      <el-col :span="6">
        <el-card shadow="never" header="任务状态(近 7 天)"><div ref="taskStatusRef" class="chart sm"></div></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" header="AI 用量趋势(近 7 天)"><div ref="aiUsageRef" class="chart sm"></div></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" header="数据源 · 族分布"><div ref="familyRef" class="chart sm"></div></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" header="知识库文档 · 训练状态"><div ref="ragRef" class="chart sm"></div></el-card>
      </el-col>
    </el-row>

    <!-- 最近运行 -->
    <el-card shadow="never" header="最近运行" class="mt16">
      <el-table :data="recentRuns" size="small" max-height="300">
        <el-table-column label="名称" prop="name" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="s"><el-tag size="small" effect="plain" :type="STATUS_TAG[s.row.status] || 'info'">{{ s.row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column label="耗时" prop="dur" width="90" />
        <el-table-column label="开始时间" prop="startTime" width="170" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup name="Dashboard">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getOverview } from '@/api/dashboard'

const router = useRouter()
const loading = ref(false)
const STATUS_TAG = { SUCCESS: 'success', FAILURE: 'danger', STARTED: 'warning', PENDING: 'info', SKIPPED: 'info' }

const cards = ref({})
const aiTotals = ref({})
const recentRuns = ref([])
const trendRef = ref(); const taskStatusRef = ref(); const familyRef = ref(); const aiUsageRef = ref(); const ragRef = ref()
let charts = []

// 协调的冷色为主调色板(避免刺眼红绿)
const PALETTE = ['#5B8FF9', '#5AD8A6', '#6F5EF9', '#945FB9', '#1E9493', '#F6BD16', '#6DC8EC', '#5D7092']
function fmtTok(n) {
  n = Number(n || 0)
  if (n >= 1e8) return (n / 1e8).toFixed(2) + '亿'
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'
  return String(n)
}
const statCards = computed(() => [
  { key: 'ds', label: '数据源', value: cards.value.dataSources ?? 0, icon: 'Coin', color: '#5B8FF9',
    sub: `数据模型 ${cards.value.dataModels ?? 0}`, to: '/data/manage' },
  { key: 'task', label: '任务', value: (cards.value.tasks ?? 0) + (cards.value.dags ?? 0), icon: 'AlarmClock', color: '#6F5EF9',
    sub: `调度 ${cards.value.tasks ?? 0} · 工作流 ${cards.value.dags ?? 0}`, to: '/task/info' },
  { key: 'aiApp', label: 'AI 应用', value: cards.value.aiApps ?? 0, icon: 'Cpu', color: '#945FB9',
    sub: `工具 ${cards.value.aiTools ?? 0} · 模型 ${cards.value.aiModels ?? 0}`, to: '/ai/app' },
  { key: 'aiUse', label: 'AI 用量(7天)', value: fmtTok(aiTotals.value.totalTokens), icon: 'TrendCharts', color: '#1E9493',
    sub: `会话 ${aiTotals.value.sessions ?? 0} · 轮次 ${aiTotals.value.runs ?? 0}`, to: '/ai/metrics' },
])
const quickNav = [
  { label: '数据管理', icon: 'Coin', color: '#409eff', to: '/data/manage' },
  { label: '任务工作流', icon: 'Share', color: '#9b59b6', to: '/task/dag' },
  { label: '知识库', icon: 'Collection', color: '#1abc9c', to: '/rag/dataset' },
  { label: '召回测试', icon: 'Search', color: '#e6a23c', to: '/rag/retrieval' },
  { label: 'AI 对话', icon: 'ChatDotRound', color: '#f56c6c', to: '/ai/chat' },
  { label: '用量统计', icon: 'TrendCharts', color: '#1E9493', to: '/ai/metrics' },
]

function go(to) { if (to) router.push(to).catch(() => {}) }

const PIE = (title, data) => ({
  color: PALETTE,
  tooltip: { trigger: 'item' },
  legend: { type: 'scroll', bottom: 0, textStyle: { fontSize: 11 } },
  series: [{ name: title, type: 'pie', radius: ['42%', '68%'], center: ['50%', '44%'],
    itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 4 },
    label: { show: true, formatter: '{b}: {c}' }, data }],
})

function renderCharts(d) {
  charts.forEach((c) => c.dispose()); charts = []
  const init = (el, opt) => { if (!el) return; const c = echarts.init(el); c.setOption(opt); charts.push(c) }

  const trend = d.taskTrend || []
  init(trendRef.value, {
    tooltip: { trigger: 'axis' }, legend: { data: ['成功', '失败'], top: 0 },
    grid: { left: 40, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: trend.map((t) => t.date) },
    yAxis: { type: 'value' },
    series: [
      { name: '成功', type: 'line', smooth: true, areaStyle: { opacity: 0.12 }, itemStyle: { color: '#5B8FF9' }, data: trend.map((t) => t.success) },
      { name: '失败', type: 'line', smooth: true, areaStyle: { opacity: 0.12 }, itemStyle: { color: '#FF9845' }, data: trend.map((t) => t.failure) },
    ],
  })
  init(taskStatusRef.value, PIE('任务状态', d.taskStatus || []))
  init(familyRef.value, PIE('族', d.sourceFamily || []))
  init(ragRef.value, PIE('文档状态', d.ragDocStatus || []))

  // AI 用量趋势(token 折线,左轴自适应缩写)
  const ai = (d.aiUsage && d.aiUsage.series) || []
  init(aiUsageRef.value, {
    tooltip: { trigger: 'axis' },
    grid: { left: 8, right: 12, top: 20, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: ai.map((s) => s.date) },
    yAxis: { type: 'value', axisLabel: { formatter: (v) => fmtTok(v) } },
    series: [{ name: 'Token', type: 'line', smooth: true, areaStyle: { opacity: 0.15 },
      itemStyle: { color: '#1E9493' }, data: ai.map((s) => s.tokens) }],
  })
}

function onResize() { charts.forEach((c) => c.resize()) }

function load() {
  loading.value = true
  getOverview().then((res) => {
    const d = res.data || {}
    cards.value = d.cards || {}
    aiTotals.value = (d.aiUsage && d.aiUsage.totals) || {}
    recentRuns.value = d.recentRuns || []
    loading.value = false
    nextTick(() => renderCharts(d))
  }).catch(() => (loading.value = false))
}

onMounted(() => { load(); window.addEventListener('resize', onResize) })
onUnmounted(() => { window.removeEventListener('resize', onResize); charts.forEach((c) => c.dispose()) })
</script>

<style scoped>
.dash { padding: 4px; }
.mt16 { margin-top: 16px; }
.stat { cursor: pointer; border-radius: 10px; transition: transform .15s, box-shadow .15s; }
.stat:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(31, 45, 61, .1); }
.stat-row { display: flex; align-items: center; gap: 12px; }
.stat-ico { display: flex; align-items: center; justify-content: center; width: 48px; height: 48px; border-radius: 12px; font-size: 24px; flex-shrink: 0; }
.stat-num { font-size: 26px; font-weight: 700; line-height: 1.15; color: #1f2d3d; font-variant-numeric: tabular-nums; }
.stat-label { font-size: 13px; color: #909399; margin-top: 2px; }
.stat-sub { margin-top: 10px; font-size: 12px; color: #b6bcc6; min-height: 16px; }
.chart { height: 300px; }
.chart.sm { height: 260px; }
.quick { display: flex; flex-wrap: wrap; gap: 10px; }
.quick-item { flex: 1 1 40%; display: flex; align-items: center; gap: 8px; padding: 14px; border: 1px solid #ebeef5;
  border-radius: 8px; cursor: pointer; transition: all .15s; font-size: 14px; }
.quick-item:hover { border-color: #409eff; background: #ecf5ff; }
.quick-item .el-icon { font-size: 20px; }
</style>
