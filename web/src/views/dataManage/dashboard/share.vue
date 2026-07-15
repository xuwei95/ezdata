<template>
  <div class="dash-share" :class="{ dark: isScreen }">
    <div class="ds-head">
      <span class="ds-title">{{ dash.name || '看板' }}</span>
      <span v-if="lastUpdate" class="ds-time">更新于 {{ lastUpdate }}</span>
    </div>
    <div class="ds-body">
      <DashCanvas v-if="dash.components.length" :key="renderKey" :components="dash.components" :canvas="dash.canvas" />
      <el-empty v-else :description="err || '空看板'" />
    </div>
  </div>
</template>

<script setup name="DashShare">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { getSharedDashboard } from '@/api/dataManage/data'
import DashCanvas from './DashCanvas.vue'

const route = useRoute()
const err = ref('')
const lastUpdate = ref('')
const renderKey = ref(0)
const dash = reactive({ name: '', canvas: { mode: 'matrix', cols: 24 }, components: [], refreshInterval: 0 })
let timer = null
const isScreen = computed(() => (dash.canvas && dash.canvas.mode) === 'free')

async function load() {
  try {
    const d = (await getSharedDashboard(route.params.token)).data || {}
    dash.name = d.name || ''
    dash.canvas = d.canvas && Object.keys(d.canvas).length ? d.canvas : { mode: 'matrix', cols: 24 }
    dash.components = d.components || []   // 已含 rows/chartSpec
    dash.refreshInterval = d.refreshInterval || 0
    renderKey.value++
    lastUpdate.value = new Date().toLocaleTimeString()
    if (!timer && dash.refreshInterval > 0) timer = setInterval(load, dash.refreshInterval * 1000)
  } catch (e) { err.value = e?.msg || e?.message || '分享不存在或已关闭' }
}

onMounted(load)
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.dash-share { min-height: 100vh; box-sizing: border-box; padding: 10px 14px; background: #fff; }
.dash-share.dark { background: #0b1a2b; color: #cfe3ff; }
.ds-head { display: flex; align-items: baseline; gap: 12px; margin-bottom: 8px; }
.ds-title { font-size: 16px; font-weight: 600; }
.ds-time { font-size: 12px; opacity: 0.7; }
.ds-body { min-height: 60vh; }
</style>
