<template>
  <div class="self-analysis">
    <!-- 简单筛选:先缩小数据再进分析(最多取 1000 行);筛选组件与「数据接口」一致 -->
    <el-card shadow="never" class="filter-card">
      <FilterBuilder v-model="filters" :fields="fields" :operators="operators" />
      <div class="filter-bar">
        <el-button size="small" type="primary" icon="Search" :loading="loading" @click="load">应用筛选并分析</el-button>
        <el-button size="small" icon="RefreshLeft" :disabled="!filters.length" @click="clearFilters">清空</el-button>
        <span class="tip">拖拽字段即可分析(PyGWalker);最多取 1000 行,更大范围请先筛选。做好的图在图表右上角工具栏可导出 PNG/SVG/配置。</span>
      </div>
    </el-card>

    <div ref="wrap" class="frame-wrap" v-loading="loading" element-loading-text="生成分析视图中…">
      <iframe
        v-if="html"
        :srcdoc="html"
        class="pyg-frame"
        :style="{ height: frameH + 'px' }"
        sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
      />
      <el-empty v-else-if="!loading" :description="err || '暂无数据'" />
    </div>
  </div>
</template>

<script setup name="SelfAnalysisTab">
import { ref, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { walkerHtml, getOperators } from '@/api/dataManage/data'
import FilterBuilder from './FilterBuilder.vue'

const props = defineProps({ model: { type: Object, required: true } })

const html = ref('')
const loading = ref(false)
const err = ref('')
const fields = ref([])
const operators = ref([])
const filters = ref([])
const wrap = ref()
const frameH = ref(500)

async function computeH() {
  await nextTick()
  const top = wrap.value ? wrap.value.getBoundingClientRect().top : 240
  frameH.value = Math.max(360, Math.floor(window.innerHeight - top - 16))
}

async function load() {
  if (!props.model || !props.model.id) return
  loading.value = true
  err.value = ''
  html.value = ''
  try {
    // 与「数据接口」一致:原样发 [{field,op,value}],由后端 handler.search 解释
    const res = await walkerHtml(props.model.id, { filters: filters.value.filter(f => f.field && f.op) })
    html.value = res.data.html || ''
    await computeH()
  } catch (e) {
    err.value = e?.msg || e?.message || '生成失败'
    ElMessage.error(err.value)
  } finally {
    loading.value = false
  }
}

function clearFilters() {
  filters.value = []
  load()
}

function sync() {
  fields.value = props.model?.fields || []
  filters.value = []
  if (!operators.value.length) getOperators().then(r => { operators.value = r.data || [] })
  load()
}

watch(() => props.model && props.model.id, sync)
watch(() => filters.value.length, computeH)
onMounted(() => {
  sync()
  window.addEventListener('resize', computeH)
})
</script>

<style scoped>
.self-analysis { display: flex; flex-direction: column; }
.filter-card { margin-bottom: 8px; }
.filter-card :deep(.el-card__body) { padding: 10px 12px; }
.filter-bar { display: flex; align-items: center; gap: 8px; margin-top: 4px; flex-wrap: wrap; }
.filter-bar .tip { font-size: 12px; color: #909399; margin-left: auto; }
.frame-wrap { flex: 1; min-height: 360px; }
.pyg-frame { width: 100%; border: 1px solid #ebeef5; border-radius: 6px; background: #fff; }
</style>
