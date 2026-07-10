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

    <!-- 结果:数据表格 / 可视化 两个子页,数据源都是本次查询结果 -->
    <el-tabs v-model="subTab" class="result-tabs">
      <el-tab-pane label="数据表格" name="grid">
        <div class="result-bar">
          <span class="count" v-if="rows.length">共 {{ rows.length }} 行(虚拟滚动,不分页)</span>
          <span class="count" v-else>暂无数据</span>
          <el-button size="small" icon="Download" :disabled="!rows.length" @click="exportExcel">导出 Excel</el-button>
        </div>
        <div class="grid-wrap" ref="gridWrap">
          <vxe-table :data="rows" :height="gridH" border stripe show-overflow
            :scroll-y="{ enabled: true, gt: 50 }" :scroll-x="{ enabled: true, gt: 20 }"
            :column-config="{ resizable: true }" :loading="loading">
            <vxe-column type="seq" width="60" fixed="left" />
            <vxe-column v-for="c in columns" :key="c" :field="c" :title="c" :width="170" :resizable="true" />
          </vxe-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="可视化" name="viz">
        <div class="viz-bar">
          <el-input v-model="vizQ" size="small" class="viz-q" clearable
            placeholder="一句话生成图表,如:按城市看销售额柱状图" @keyup.enter="genViz" />
          <el-button size="small" type="primary" icon="MagicStick" :loading="vizLoading"
            :disabled="!rows.length" @click="genViz">AI 生成图表</el-button>
          <el-button size="small" icon="Refresh" :loading="vizLoading" :disabled="!rows.length"
            @click="loadViz">重置图表</el-button>
          <span class="muted">用本次查询结果(前 {{ VIZ_CAP }} 行);图表工具栏可导出 PNG/SVG/配置。</span>
        </div>
        <div ref="vizWrap" class="viz-wrap" v-loading="vizLoading" element-loading-text="生成分析视图中…">
          <iframe v-if="vizHtml" :srcdoc="vizHtml" class="pyg-frame" :style="{ height: vizH + 'px' }"
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads" />
          <el-empty v-else-if="!vizLoading" :description="vizErr || '先在上方执行查询,再切到本页可视化'" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup name="DataQueryTab">
import { ref, reactive, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import { queryModel, getSampleQuery, walkerHtml, walkerAiHtml } from '@/api/dataManage/data'
import { getToken } from '@/utils/auth'

const props = defineProps({ model: { type: Object, required: true } })

const VIZ_CAP = 1000
const native = ref('')
const rows = ref([])
const columns = ref([])
const loading = ref(false)
const subTab = ref('grid')
// AI 辅助生成
const aiq = reactive({ open: false, question: '', output: '', loading: false })
const AI_BASE = import.meta.env.VITE_APP_BASE_API || ''

// 可视化子页
const vizHtml = ref('')
const vizLoading = ref(false)
const vizErr = ref('')
const vizQ = ref('')
const vizWrap = ref()
const vizH = ref(500)

// 表格高度:按表格实际位置算,正好贴到视口底部(留出横向滚动条空间)
const gridH = ref(400)
const gridWrap = ref()
async function computeH() {
  await nextTick()
  const top = gridWrap.value ? gridWrap.value.getBoundingClientRect().top : 240
  gridH.value = Math.max(240, Math.floor(window.innerHeight - top - 24))
}
async function computeVizH() {
  await nextTick()
  const top = vizWrap.value ? vizWrap.value.getBoundingClientRect().top : 240
  vizH.value = Math.max(360, Math.floor(window.innerHeight - top - 16))
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
  vizHtml.value = ''; vizErr.value = ''; subTab.value = 'grid'
  if (!props.model || !props.model.id) return
  // 预填原生查询默认示例(各源对应方言,limit 100)
  try {
    const q = (await getSampleQuery(props.model.id)).data.native
    native.value = typeof q === 'string' ? q : JSON.stringify(q, null, 2)
  } catch (e) { /* 忽略 */ }
}
watch(() => props.model && props.model.id, syncModel)
watch(() => aiq.open, computeH)
watch(() => aiq.loading, computeH)
// 切到可视化子页:有数据且尚未生成则自动生成
watch(subTab, (v) => { if (v === 'viz' && rows.value.length && !vizHtml.value) loadViz() })
onMounted(() => { syncModel(); computeH(); window.addEventListener('resize', onResize) })
onUnmounted(() => window.removeEventListener('resize', onResize))
function onResize() { computeH(); computeVizH() }

function fill(records) {
  rows.value = records || []
  columns.value = rows.value.length ? Object.keys(rows.value[0]) : []
  vizHtml.value = ''  // 查询结果变了,作废旧可视化
  if (subTab.value === 'viz' && rows.value.length) loadViz()
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

// 用当前查询结果作数据源生成 PyGWalker 分析视图
async function loadViz() {
  if (!rows.value.length) { vizErr.value = '先执行查询获取数据'; return }
  vizLoading.value = true; vizErr.value = ''; vizHtml.value = ''
  try {
    const res = await walkerHtml(props.model.id, { rows: rows.value.slice(0, VIZ_CAP) })
    vizHtml.value = res.data.html || ''
    await computeVizH()
  } catch (e) {
    vizErr.value = e?.msg || e?.message || '生成失败'
    ElMessage.error(vizErr.value)
  } finally {
    vizLoading.value = false
  }
}

// AI 一句话生成图表(用当前查询结果作数据源;系统 LLM 生成配置,预填后仍可拖拽微调)
async function genViz() {
  if (!rows.value.length) { ElMessage.warning('先执行查询获取数据'); return }
  if (!vizQ.value.trim()) { ElMessage.warning('请描述你想要的图表'); return }
  vizLoading.value = true; vizErr.value = ''; vizHtml.value = ''
  try {
    const res = await walkerAiHtml(props.model.id, { question: vizQ.value, rows: rows.value.slice(0, VIZ_CAP) })
    vizHtml.value = res.data.html || ''
    await computeVizH()
  } catch (e) {
    vizErr.value = e?.msg || e?.message || '生成失败'
    ElMessage.error(vizErr.value)
  } finally {
    vizLoading.value = false
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
.result-tabs { margin-top: 8px; }
.result-bar { display: flex; align-items: center; justify-content: space-between; margin: 2px 0 6px; }
.count { color: #909399; font-size: 13px; }
.viz-bar { display: flex; align-items: center; gap: 8px; margin: 2px 0 8px; flex-wrap: wrap; }
.viz-bar .viz-q { max-width: 340px; }
.viz-bar .muted { color: #909399; font-size: 12px; margin-left: auto; }
.viz-wrap { min-height: 360px; }
.pyg-frame { width: 100%; border: 1px solid #ebeef5; border-radius: 6px; background: #fff; }
.ai-out {
  margin: 8px 0; padding: 8px 10px; max-height: 220px; overflow: auto;
  background: #1e1e1e; color: #d4d4d4; border-radius: 4px;
  font-family: Consolas, Monaco, monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all;
}
.cursor { animation: blink 1s steps(1) infinite; color: #67c23a; }
@keyframes blink { 50% { opacity: 0; } }
</style>
