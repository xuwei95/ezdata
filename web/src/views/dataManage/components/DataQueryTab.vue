<template>
  <div class="query-tab">
    <div class="native-bar">
      <div class="bar">
        <span class="muted">原生查询(SQL 字符串 / ES DSL JSON)</span>
        <el-button size="small" icon="MagicStick" @click="aiq.open = !aiq.open">AI 生成查询</el-button>
      </div>
      <el-input v-model="native" type="textarea" :rows="4"
        placeholder="例如:SELECT * FROM xxx WHERE ...;或点「AI 生成查询」用自然语言生成" />

      <!-- AI 辅助生成:流式打印 → 确认采用到查询框 -->
      <div v-if="aiq.open" class="ai-panel">
        <el-input v-model="aiq.question" type="textarea" :rows="2"
          placeholder="用自然语言描述你想查什么,例如:最近一周金额最高的 10 笔订单" @keyup.enter.stop="genQuery" />
        <div class="bar" style="margin-top: 6px">
          <el-button size="small" type="primary" icon="MagicStick" :loading="aiq.loading" @click="genQuery">
            {{ aiq.output ? '重新生成' : '生成' }}</el-button>
          <span class="muted">生成结果见下方,确认后采用到查询框</span>
        </div>
        <pre v-if="aiq.output" class="ai-out">{{ aiq.output }}<span v-if="aiq.loading" class="cursor">▋</span></pre>
        <div v-if="aiq.output && !aiq.loading" class="bar">
          <el-button size="small" type="success" icon="Check" @click="applyQuery">采用到查询</el-button>
          <el-button size="small" @click="aiq.output = ''">清空</el-button>
        </div>
      </div>

      <el-button type="primary" icon="Search" :loading="loading" @click="runNative" style="margin-top: 8px">查询</el-button>
    </div>

    <div class="result-bar">
      <span class="count" v-if="rows.length">共 {{ rows.length }} 行(虚拟滚动,不分页)</span>
      <span class="count" v-else>暂无数据</span>
      <el-button size="small" icon="Download" :disabled="!rows.length" @click="exportExcel">导出 Excel</el-button>
    </div>

    <!-- vxe-table 数据网格:行/列虚拟滚动 + 列可拖宽 + 高度占满底部 -->
    <div class="grid-wrap" ref="gridWrap">
      <vxe-table :data="rows" :height="gridH" border stripe show-overflow
        :scroll-y="{ enabled: true, gt: 50 }" :scroll-x="{ enabled: true, gt: 20 }"
        :column-config="{ resizable: true }" :loading="loading">
        <vxe-column type="seq" width="60" fixed="left" />
        <vxe-column v-for="c in columns" :key="c" :field="c" :title="c" :width="170" :resizable="true" />
      </vxe-table>
    </div>
  </div>
</template>

<script setup name="DataQueryTab">
import { ref, reactive, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import { queryModel, getSampleQuery } from '@/api/dataManage/data'
import { getToken } from '@/utils/auth'

const props = defineProps({ model: { type: Object, required: true } })

const native = ref('')
const rows = ref([])
const columns = ref([])
const loading = ref(false)
// AI 辅助生成
const aiq = reactive({ open: false, question: '', output: '', loading: false })
const AI_BASE = import.meta.env.VITE_APP_BASE_API || ''

// 表格高度:按表格实际位置算,正好贴到视口底部(留出横向滚动条空间)
const gridH = ref(400)
const gridWrap = ref()
async function computeH() {
  await nextTick()
  const top = gridWrap.value ? gridWrap.value.getBoundingClientRect().top : 240
  gridH.value = Math.max(240, Math.floor(window.innerHeight - top - 24))
}

function stripFence(t) {
  let s = (t || '').trim()
  if (s.startsWith('```')) s = s.replace(/^```[^\n]*\n/, '').replace(/```\s*$/, '').trim()
  return s
}

async function streamAi(url, body, onChunk) {
  const resp = await fetch(AI_BASE + url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + getToken() },
    body: JSON.stringify(body)
  })
  if (!resp.ok || !resp.body) throw new Error('HTTP ' + resp.status)
  const reader = resp.body.getReader()
  const dec = new TextDecoder()
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    onChunk(dec.decode(value, { stream: true }))
  }
}

function exportExcel() {
  if (!rows.value.length) return
  const ws = XLSX.utils.json_to_sheet(rows.value, { header: columns.value })
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'data')
  XLSX.writeFile(wb, `${props.model.name || 'data'}_${Date.now()}.xlsx`)
}

async function syncModel() {
  native.value = ''; rows.value = []; columns.value = []
  aiq.open = false; aiq.question = ''; aiq.output = ''
  if (!props.model || !props.model.id) return
  // 预填原生查询默认示例(各源对应方言,limit 100)
  try {
    const q = (await getSampleQuery(props.model.id)).data.native
    native.value = typeof q === 'string' ? q : JSON.stringify(q, null, 2)
  } catch (e) { /* 忽略 */ }
}
watch(() => props.model && props.model.id, syncModel)
// AI 面板展开/收起、生成开始结束都会改变表格起点,重算高度
watch(() => aiq.open, computeH)
watch(() => aiq.loading, computeH)
onMounted(() => { syncModel(); computeH(); window.addEventListener('resize', computeH) })
onUnmounted(() => window.removeEventListener('resize', computeH))

function fill(records) {
  rows.value = records || []
  columns.value = rows.value.length ? Object.keys(rows.value[0]) : []
}

// 执行原生查询(SQL 串或 ES DSL JSON,自动识别)
async function runNative() {
  if (!native.value.trim()) { ElMessage.warning('请输入查询语句'); return }
  loading.value = true
  try {
    let n = native.value.trim()
    try { n = JSON.parse(n) } catch (e) { /* 当作 SQL 字符串 */ }
    const res = await queryModel(props.model.id, { native: n })
    fill(res.data.records)
    ElMessage.success(`查询到 ${res.data.total} 行`)
  } catch (e) {
    ElMessage.error('查询失败')
  } finally {
    loading.value = false
  }
}

// AI 流式生成查询(辅助:打在下方,确认后采用到查询框)
async function genQuery() {
  if (!aiq.question.trim()) { ElMessage.warning('请描述你想查什么'); return }
  aiq.output = ''; aiq.loading = true
  try {
    await streamAi(`/data/model/${props.model.id}/ai-query/stream`, { question: aiq.question },
      (c) => { aiq.output += c })
  } catch (e) {
    ElMessage.error('生成失败: ' + e.message)
  } finally {
    aiq.loading = false
  }
}
function applyQuery() {
  native.value = stripFence(aiq.output).replace(/;\s*$/, '')
  aiq.open = false
  ElMessage.success('已采用到查询框,点「查询」执行')
}
</script>

<style scoped>
.native-bar .bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.native-bar .muted { color: #909399; font-size: 12px; }
.ai-panel { margin-top: 8px; padding: 10px; border: 1px dashed #c0c4cc; border-radius: 6px; background: #fafafa; }
.result-bar { display: flex; align-items: center; justify-content: space-between; margin: 10px 0 6px; }
.count { color: #909399; font-size: 13px; }
.ai-out {
  margin: 8px 0; padding: 8px 10px; max-height: 220px; overflow: auto;
  background: #1e1e1e; color: #d4d4d4; border-radius: 4px;
  font-family: Consolas, Monaco, monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all;
}
.cursor { animation: blink 1s steps(1) infinite; color: #67c23a; }
@keyframes blink { 50% { opacity: 0; } }
</style>
