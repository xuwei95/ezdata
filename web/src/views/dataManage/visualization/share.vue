<template>
  <div class="board-share">
    <div class="bs-head">
      <span class="bs-title">{{ board.name || '看板' }}</span>
      <span v-if="lastUpdate" class="bs-time">更新于 {{ lastUpdate }}<template v-if="board.refreshInterval"> · 每 {{ board.refreshInterval }}s 自动</template></span>
    </div>
    <div class="bs-body">
      <EchartsBuilder
        v-if="rows.length && cfg"
        :rows="rows"
        :config="cfg"
        :show-controls="false"
        :height="chartH"
      />
      <el-empty v-else :description="err || (loading ? '加载中…' : '暂无数据')" />
    </div>
  </div>
</template>

<script setup name="BoardShare">
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { getSharedBoard } from '@/api/dataManage/data'
import EchartsBuilder from './EchartsBuilder.vue'

const route = useRoute()
const loading = ref(false)
const err = ref('')
const rows = ref([])
const cfg = ref(null)
const lastUpdate = ref('')
const board = reactive({ name: '', refreshInterval: 0 })
const chartH = ref(Math.max(440, window.innerHeight - 90))
let timer = null

async function load() {
  const token = route.params.token
  if (!token) { err.value = '缺少分享令牌'; return }
  loading.value = true
  err.value = ''
  try {
    const d = (await getSharedBoard(token)).data || {}
    board.name = d.name || ''
    board.refreshInterval = d.refreshInterval || 0
    cfg.value = d.chartSpec || null
    rows.value = d.rows || []
    if (!rows.value.length) { err.value = '查询无数据' }
    lastUpdate.value = new Date().toLocaleTimeString()
    setupTimer()
  } catch (e) {
    err.value = e?.msg || e?.message || '分享不存在或已关闭'
  } finally {
    loading.value = false
  }
}
function setupTimer() {
  if (timer || !(board.refreshInterval > 0)) return
  timer = setInterval(load, board.refreshInterval * 1000)
}

onMounted(load)
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.board-share { min-height: 100vh; box-sizing: border-box; padding: 12px 16px; background: #fff; }
.bs-head { display: flex; align-items: baseline; gap: 12px; margin-bottom: 8px; }
.bs-title { font-size: 16px; font-weight: 600; color: #303133; }
.bs-time { font-size: 12px; color: #909399; }
.bs-body { min-height: 460px; }
</style>
