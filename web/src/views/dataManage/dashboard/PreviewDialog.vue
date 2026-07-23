<template>
  <el-dialog
    v-model="visible"
    fullscreen
    append-to-body
    class="preview-dialog"
    :show-close="true"
  >
    <template #header>
      <div class="pv-head">
        <span class="pv-title">{{ row?.name || '预览' }}</span>
        <el-tag size="small" :type="TAG[dashType] || 'info'">{{ TYPE_LABEL[dashType] || '单图' }}</el-tag>
        <span v-if="lastUpdate" class="pv-time">更新于 {{ lastUpdate }}</span>
        <div class="pv-actions">
          <el-button size="small" icon="Refresh" :loading="loading" @click="load">{{ $t('刷新') }}</el-button>
          <el-button size="small" type="primary" icon="FullScreen" @click="openFull">{{ $t('新标签纯图页') }}</el-button>
        </div>
      </div>
    </template>

    <div class="pv-body" v-loading="loading" element-loading-text="加载中…">
      <!-- 单图:EchartsBuilder -->
      <template v-if="dashType === 'chart'">
        <EchartsBuilder v-if="rows.length && cfg" :rows="rows" :config="cfg" :show-controls="false" :height="chartH" />
        <el-empty v-else :description="err || '该看板无图表配置,无法预览'" />
      </template>
      <!-- 多图 / 大屏:筛选栏(有变量才显示)+ DashCanvas 只读 -->
      <template v-else>
        <DashFilterBar :filters="filters" :model-value="filterValues" @change="onFilterChange" />
        <DashCanvas v-if="components.length" :key="renderKey" :components="components" :canvas="canvas"
          :chart-params="chartParams" :filters="filters" @filter-change="onFilterChange" />
        <el-empty v-else :description="err || '空看板'" />
      </template>
    </div>
  </el-dialog>
</template>

<script setup name="PreviewDialog">
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getAnalysisTemplate, getDashboard } from '@/api/dataManage/data'
import EchartsBuilder from '../visualization/EchartsBuilder.vue'
import { isEchartsCfg, fetchBoardRows, paramsToValues } from '../visualization/board.js'
import DashCanvas from './DashCanvas.vue'
import DashFilterBar from './DashFilterBar.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  row: { type: Object, default: null } // {id, name, dashType}
})
const emit = defineEmits(['update:modelValue'])
const visible = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })

const TYPE_LABEL = { chart: '单图', board: '多图', screen: '大屏' }
const TAG = { chart: '', board: 'success', screen: 'warning' }
const QUERY_CAP = 5000
const router = useRouter()

const dashType = computed(() => props.row?.dashType || 'chart')
const loading = ref(false)
const err = ref('')
const lastUpdate = ref('')
const chartH = ref(Math.max(420, window.innerHeight - 140))
// 单图
const rows = ref([])
const cfg = ref(null)
// 多图/大屏
const components = ref([])
const canvas = ref({ mode: 'matrix', cols: 24 })
const renderKey = ref(0)
// 联动筛选
const filters = ref([])
const filterValues = reactive({})
const chartParams = computed(() => paramsToValues((filters.value || []).map((f) => ({ ...f, value: filterValues[f.name] }))))
function syncFilterValues() {
  const names = new Set()
  for (const f of filters.value || []) {
    if (!f || !f.name) continue
    names.add(f.name)
    if (!(f.name in filterValues)) filterValues[f.name] = f.default ?? (f.type === 'daterange' ? null : '')
  }
  Object.keys(filterValues).forEach((k) => { if (!names.has(k)) delete filterValues[k] })
}
function onFilterChange({ name, value }) { if (name) filterValues[name] = value }

async function load() {
  const id = props.row?.id
  if (!id) { err.value = '缺少看板 id'; return }
  loading.value = true; err.value = ''
  try {
    if (dashType.value === 'chart') {
      const t = (await getAnalysisTemplate(id, true)).data || {}
      if (!isEchartsCfg(t.chartSpec)) { err.value = '该看板无图表配置(或为旧格式)'; rows.value = []; cfg.value = null; return }
      if (!t.modelId) { err.value = '看板未关联数据模型'; rows.value = []; return }
      const data = await fetchBoardRows(t.modelId, t.query && t.query.native, paramsToValues(t.params), QUERY_CAP, true)
      if (!data.length) { err.value = '查询无数据'; rows.value = []; return }
      rows.value = data
      cfg.value = { ...t.chartSpec }
    } else {
      const d = (await getDashboard(id, true)).data || {}
      canvas.value = d.canvas && Object.keys(d.canvas).length ? d.canvas : { mode: 'matrix', cols: 24 }
      components.value = d.components || []
      filters.value = d.filters || []
      syncFilterValues()
      renderKey.value++
    }
    lastUpdate.value = new Date().toLocaleTimeString()
  } catch (e) { err.value = e?.msg || e?.message || '加载失败'; console.warn('[PreviewDialog] 预览加载失败', err.value) } finally { loading.value = false }
}

// 新标签打开无壳纯图页(单图 BoardView / 多图·大屏 DashViewPage)
function openFull() {
  const id = props.row?.id
  if (!id) return
  const name = dashType.value === 'chart' ? 'BoardView' : 'DashViewPage'
  const { href } = router.resolve({ name, params: { id } })
  window.open(href, '_blank')
}

// 重置上次残留后再加载
watch(() => props.modelValue, (v) => {
  if (v) {
    rows.value = []; cfg.value = null; components.value = []; err.value = ''; lastUpdate.value = ''
    filters.value = []; Object.keys(filterValues).forEach((k) => delete filterValues[k])
    load()
  }
})
</script>

<style scoped>
.pv-head { display: flex; align-items: center; gap: 10px; }
.pv-title { font-size: 16px; font-weight: 600; }
.pv-time { font-size: 12px; color: #909399; }
.pv-actions { margin-left: auto; display: flex; gap: 8px; }
.pv-body { height: calc(100vh - 110px); overflow: auto; }
.pv-body > :deep(.dg-free-vp) { height: 100%; }
</style>
