<template>
  <div class="dash-view">
    <!-- 纯图页:无头部、无 loading,只渲染画布 -->
    <DashCanvas v-if="dash.components.length" :key="renderKey" :components="dash.components" :canvas="dash.canvas" />
    <el-empty v-else :description="err || '空看板'" />
  </div>
</template>

<script setup name="DashView">
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { getDashboard } from '@/api/dataManage/data'
import DashCanvas from './DashCanvas.vue'

const route = useRoute()
const err = ref('')
const renderKey = ref(0)
const dash = reactive({ name: '', canvas: { mode: 'matrix', cols: 24 }, components: [], refreshInterval: 0 })
let timer = null

async function load() {
  err.value = ''
  try {
    const d = (await getDashboard(route.params.id, true)).data || {}
    dash.name = d.name || ''
    dash.canvas = d.canvas && Object.keys(d.canvas).length ? d.canvas : { mode: 'matrix', cols: 24 }
    dash.components = d.components || []
    dash.refreshInterval = d.refreshInterval || 0
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
