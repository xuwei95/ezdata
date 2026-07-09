<template>
  <div class="self-analysis">
    <!-- 简单筛选:先缩小数据再进分析(最多取 1000 行) -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-rows">
        <div v-for="(f, i) in filters" :key="i" class="filter-row">
          <el-select v-model="f.field" placeholder="字段" filterable style="width: 160px">
            <el-option v-for="c in fields" :key="c.name" :label="c.name" :value="c.name" />
          </el-select>
          <el-select v-model="f.op" placeholder="操作符" style="width: 116px">
            <el-option v-for="o in operators" :key="o.op" :label="o.label" :value="o.op" />
          </el-select>
          <el-input v-if="!isSort(f.op)" v-model="f.value" placeholder="值(in/区间用英文逗号分隔)" style="width: 200px" />
          <el-button icon="Delete" link @click="filters.splice(i, 1)" />
        </div>
      </div>
      <div class="filter-bar">
        <el-button size="small" icon="Plus" @click="filters.push({ field: '', op: 'eq', value: '' })">加条件</el-button>
        <el-button size="small" type="primary" icon="Search" :loading="loading" @click="load">应用筛选并分析</el-button>
        <el-button size="small" icon="RefreshLeft" :disabled="!filters.length" @click="clearFilters">清空</el-button>
        <span class="tip">拖拽字段即可分析(PyGWalker);最多取 1000 行,更大范围请先筛选。</span>
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

const props = defineProps({ model: { type: Object, required: true } })

const html = ref('')
const loading = ref(false)
const err = ref('')
const fields = ref([])
const operators = ref([])
const filters = ref([])
const wrap = ref()
const frameH = ref(500)

// 排序类算子无需填值
function isSort(op) {
  return op === 'sort_asc' || op === 'sort_desc'
}

async function computeH() {
  await nextTick()
  const top = wrap.value ? wrap.value.getBoundingClientRect().top : 240
  frameH.value = Math.max(360, Math.floor(window.innerHeight - top - 16))
}

// in/nin/between 的值按英文逗号拆成数组,其余原样
function normFilters() {
  return filters.value
    .filter(f => f.field && f.op)
    .map(f => {
      if (isSort(f.op)) return { field: f.field, op: f.op }
      const multi = ['in', 'nin', 'between'].includes(f.op)
      const value = multi ? String(f.value ?? '').split(',').map(s => s.trim()).filter(Boolean) : f.value
      return { field: f.field, op: f.op, value }
    })
}

async function load() {
  if (!props.model || !props.model.id) return
  loading.value = true
  err.value = ''
  html.value = ''
  try {
    const res = await walkerHtml(props.model.id, { filters: normFilters() })
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
.filter-rows { display: flex; flex-direction: column; gap: 6px; }
.filter-row { display: flex; align-items: center; gap: 8px; }
.filter-bar { display: flex; align-items: center; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.filter-bar .tip { font-size: 12px; color: #909399; margin-left: auto; }
.frame-wrap { flex: 1; min-height: 360px; }
.pyg-frame { width: 100%; border: 1px solid #ebeef5; border-radius: 6px; background: #fff; }
</style>
