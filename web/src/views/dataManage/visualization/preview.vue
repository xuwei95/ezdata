<template>
  <div class="board-view">
    <div class="bv-head">
      <el-button icon="Back" text @click="goBack">返回</el-button>
      <span class="bv-title">{{ board.name || '看板预览' }}</span>
      <el-tag v-if="board.modelName" size="small" type="info" class="bv-model">{{ board.modelName }}</el-tag>
      <div class="bv-actions">
        <el-button icon="Refresh" size="small" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <div class="bv-body" v-loading="loading" element-loading-text="加载中…">
      <EchartsBuilder
        v-if="rows.length && cfg"
        :rows="rows"
        :config="cfg"
        :show-controls="false"
        :height="chartH"
      />
      <el-empty v-else :description="err || (loading ? '加载中…' : '该看板无图表配置,无法预览')" />
    </div>
  </div>
</template>

<script setup name="BoardView">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAnalysisTemplate, queryModel } from '@/api/dataManage/data'
import EchartsBuilder from './EchartsBuilder.vue'

const route = useRoute()
const router = useRouter()
const QUERY_CAP = 5000
const CHART_TYPES = [
  'bar', 'bar_stack', 'bar_percent', 'hbar', 'line', 'area', 'line_stack',
  'pie', 'donut', 'rose', 'scatter', 'radar', 'funnel', 'gauge', 'kline',
  'combo', 'waterfall', 'heatmap', 'boxplot', 'treemap', 'sankey', 'kpi', 'table'
]

const loading = ref(false)
const err = ref('')
const rows = ref([])
const cfg = ref(null)
const board = reactive({ name: '', modelName: '', modelId: '', native: null, chartSpec: null })
const chartH = ref(Math.max(440, window.innerHeight - 120)) // 全屏页,无 Layout 头部,给图更多高度

function isEchartsCfg(c) {
  return !!c && typeof c === 'object' && !Array.isArray(c) && CHART_TYPES.includes(c.type)
}
// native 可能是 SQL 字符串或 dict(ES/Mongo);能解析成对象就用对象,否则当 SQL 串
function parseNative(n) {
  const s = (typeof n === 'string' ? n : JSON.stringify(n ?? '')).trim()
  if (s[0] === '{' || s[0] === '[') { try { return JSON.parse(s) } catch (e) { /* 当 SQL */ } }
  return typeof n === 'string' ? n : n
}

async function load() {
  const id = route.params.id
  if (!id) { err.value = '缺少看板 id'; return }
  loading.value = true
  err.value = ''
  rows.value = []
  try {
    const t = (await getAnalysisTemplate(id)).data || {}
    board.name = t.name || ''
    board.modelName = t.modelName || ''
    board.modelId = t.modelId || ''
    board.native = (t.query && t.query.native) ?? null
    board.chartSpec = t.chartSpec || null
    if (!isEchartsCfg(board.chartSpec)) { err.value = '该看板无图表配置(或为旧格式)'; return }
    if (!board.modelId) { err.value = '看板未关联数据模型'; return }
    const q = await queryModel(board.modelId, { native: parseNative(board.native) })
    const data = (q.data.records || []).slice(0, QUERY_CAP)
    if (!data.length) { err.value = '查询无数据'; return }
    rows.value = data
    cfg.value = { ...board.chartSpec }
  } catch (e) {
    err.value = e?.msg || e?.message || '加载失败'
    ElMessage.error(err.value)
  } finally {
    loading.value = false
  }
}

function goBack() {
  // 有历史则返回,否则回看板列表
  if (window.history.length > 1) router.back()
  else router.push('/data/dashboard')
}

onMounted(load)
</script>

<style scoped>
.board-view { min-height: 100vh; box-sizing: border-box; padding: 14px 18px; background: var(--el-bg-color, #fff); }
.bv-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.bv-title { font-size: 16px; font-weight: 600; color: var(--el-text-color-primary); }
.bv-model { margin-left: 2px; }
.bv-actions { margin-left: auto; }
.bv-body { min-height: 440px; border: 1px solid var(--el-border-color-lighter); border-radius: 6px; padding: 10px; }
</style>
