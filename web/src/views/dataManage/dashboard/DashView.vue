<template>
  <div class="dash-view">
    <!-- 纯图页:无头部,顶部筛选栏(有变量才显示)+ 画布 -->
    <DashFilterBar :filters="filters" :model-value="filterValues" @change="onFilterChange" />
    <DashCanvas v-if="dash.components.length" :key="renderKey" :components="dash.components" :canvas="dash.canvas"
      :chart-params="chartParams" :filters="filters" @filter-change="onFilterChange" />
    <el-empty v-else :description="err || '空看板'" />
  </div>
</template>

<script setup name="DashView">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { getDashboard } from '@/api/dataManage/data'
import { paramsToValues } from '@/views/dataManage/visualization/board.js'
import DashCanvas from './DashCanvas.vue'
import DashFilterBar from './DashFilterBar.vue'

const route = useRoute()
const err = ref('')
const renderKey = ref(0)
const dash = reactive({ name: '', canvas: { mode: 'matrix', cols: 24 }, components: [], refreshInterval: 0 })
const filters = ref([]) // 看板变量定义(存储态,options 数组)
const filterValues = reactive({}) // 当前筛选值 {name: value}
const chartParams = computed(() => paramsToValues((filters.value || []).map((f) => ({ ...f, value: filterValues[f.name] }))))
let timer = null

// 同步变量定义:保留用户已选值(自动刷新 reload 不清空),补默认、删已移除变量
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
  err.value = ''
  try {
    const d = (await getDashboard(route.params.id, true)).data || {}
    dash.name = d.name || ''
    dash.canvas = d.canvas && Object.keys(d.canvas).length ? d.canvas : { mode: 'matrix', cols: 24 }
    dash.components = d.components || []
    dash.refreshInterval = d.refreshInterval || 0
    filters.value = d.filters || []
    syncFilterValues()
    renderKey.value++ // 强制各组件重新取数(自动刷新)
    if (!timer && dash.refreshInterval > 0) timer = setInterval(load, dash.refreshInterval * 1000)
  } catch (e) { err.value = e?.msg || e?.message || '加载失败'; console.warn('[DashView] 展示加载失败', err.value) }
}

onMounted(load)
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
/* 纯图页:铺满视口,让 DashCanvas(大屏 free 模式)按容器整体等比缩放 */
.dash-view { height: 100vh; overflow: auto; box-sizing: border-box; background: var(--el-bg-color, #fff); }
.dash-view > :deep(.dg-free-vp) { height: 100%; }
</style>
