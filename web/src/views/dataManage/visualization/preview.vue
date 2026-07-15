<template>
  <div class="board-view">
    <div class="bv-body">
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
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { getAnalysisTemplate } from '@/api/dataManage/data'
import EchartsBuilder from './EchartsBuilder.vue'
import { isEchartsCfg, fetchBoardRows, paramsToValues } from './board.js'

const route = useRoute()
const QUERY_CAP = 5000

const loading = ref(false)
const err = ref('')
const rows = ref([])
const cfg = ref(null)
const lastUpdate = ref('')
const board = reactive({ name: '', modelName: '', modelId: '', native: null, chartSpec: null, params: null, refreshInterval: 0 })
const chartH = ref(Math.max(440, window.innerHeight - 24)) // 纯图页,无头部,占满视口
let timer = null

async function load() {
  const id = route.params.id
  if (!id) { err.value = '缺少看板 id'; return }
  loading.value = true
  err.value = ''
  try {
    const t = (await getAnalysisTemplate(id, true)).data || {}
    board.name = t.name || ''
    board.modelName = t.modelName || ''
    board.modelId = t.modelId || ''
    board.native = (t.query && t.query.native) ?? null
    board.chartSpec = t.chartSpec || null
    board.params = t.params || null
    board.refreshInterval = t.refreshInterval || 0
    if (!isEchartsCfg(board.chartSpec)) { err.value = '该看板无图表配置(或为旧格式)'; rows.value = []; return }
    if (!board.modelId) { err.value = '看板未关联数据模型'; rows.value = []; return }
    const data = await fetchBoardRows(board.modelId, board.native, paramsToValues(board.params), QUERY_CAP, true)
    if (!data.length) { err.value = '查询无数据'; rows.value = []; return }
    rows.value = data
    cfg.value = { ...board.chartSpec }
    lastUpdate.value = new Date().toLocaleTimeString()
    setupTimer()
  } catch (e) {
    err.value = e?.msg || e?.message || '加载失败'
    console.warn('[BoardView] 预览加载失败', err.value)
  } finally {
    loading.value = false
  }
}

// 按看板的自动刷新间隔定时重取(只建一次)
function setupTimer() {
  if (timer || !(board.refreshInterval > 0)) return
  timer = setInterval(load, board.refreshInterval * 1000)
}

onMounted(load)
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.board-view { min-height: 100vh; box-sizing: border-box; padding: 8px; background: var(--el-bg-color, #fff); }
.bv-body { min-height: 440px; }
</style>
