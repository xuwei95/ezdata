<template>
  <div class="query-tab">
    <div class="native-bar">
      <div class="bar">
        <span class="muted">原生查询(SQL 字符串 / ES DSL JSON)</span>
        <el-button size="small" icon="MagicStick" @click="aiq.open = !aiq.open">AI 生成查询</el-button>
      </div>
      <el-input v-model="native" type="textarea" :rows="6" :autosize="{ minRows: 6, maxRows: 14 }"
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
          <el-select v-model="curTpl" size="small" placeholder="应用看板" clearable filterable style="width: 160px"
            :disabled="!templates.length" @change="applyTemplate">
            <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
          <el-button size="small" icon="Star" :disabled="!rows.length" @click="openSaveTpl">存为看板</el-button>
          <el-button v-if="curTpl" size="small" icon="Delete" link type="danger" @click="delTpl">删</el-button>
          <span class="muted">左侧「AI 生成图表」可一句话出图,或自选类型/字段;配置可「存为看板」。</span>
        </div>
        <div ref="vizWrap" class="viz-wrap">
          <EchartsBuilder v-if="rows.length" :rows="rows" :config="vizCfg" :height="vizH"
            ai-enabled :ai-loading="aic.loading" @ai-generate="onAiChart" @update:config="(c) => (vizCfg = c)" />
          <el-empty v-else description="先在上方执行查询,再切到本页可视化" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 存为看板 -->
    <el-dialog v-model="tplDlg.visible" title="保存为看板" width="440px" append-to-body>
      <el-form label-width="72px">
        <el-form-item label="看板名称" required>
          <el-input v-model="tplDlg.name" placeholder="如:各城市销售额柱状图" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="tplDlg.remark" type="textarea" :rows="2" />
        </el-form-item>
        <el-alert type="success" :closable="false" show-icon title="将保存:本次原生查询 + 当前图表配置(类型/字段/聚合/样式)" />
      </el-form>
      <template #footer>
        <el-button type="primary" @click="doSaveTpl">保存</el-button>
        <el-button @click="tplDlg.visible = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="DataQueryTab">
import { ref, reactive, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as XLSX from 'xlsx'
import {
  queryModel, getSampleQuery, aiChart,
  listAnalysisTemplate, saveAnalysisTemplate, delAnalysisTemplate
} from '@/api/dataManage/data'
import { getToken } from '@/utils/auth'
import EchartsBuilder from '@/views/dataManage/visualization/EchartsBuilder.vue'

const props = defineProps({ model: { type: Object, required: true } })

const native = ref('')
const rows = ref([])
const columns = ref([])
const loading = ref(false)
const subTab = ref('grid')
// AI 辅助生成查询
const aiq = reactive({ open: false, question: '', output: '', loading: false })
const AI_BASE = import.meta.env.VITE_APP_BASE_API || ''

// 可视化子页(EchartsBuilder)
const vizWrap = ref()
const vizH = ref(500)
const vizCfg = ref(null)           // 当前图表配置(EchartsBuilder cfg)
const aic = reactive({ loading: false }) // AI 生成图表配置
// 看板(取数 + 图表配置,可复用)
const templates = ref([])
const curTpl = ref('')
const tplDlg = reactive({ visible: false, name: '', remark: '' })

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
  subTab.value = 'grid'; vizCfg.value = null; curTpl.value = ''; templates.value = []
  if (!props.model || !props.model.id) return
  loadTemplates()
  // 预填原生查询默认示例(各源对应方言,limit 100)
  try {
    const q = (await getSampleQuery(props.model.id)).data.native
    native.value = typeof q === 'string' ? q : JSON.stringify(q, null, 2)
  } catch (e) { /* 忽略 */ }
}
watch(() => props.model && props.model.id, syncModel)
watch(() => aiq.open, computeH)
watch(() => aiq.loading, computeH)
watch(subTab, (v) => { if (v === 'viz') computeVizH() })
onMounted(() => {
  syncModel(); computeH()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => { window.removeEventListener('resize', onResize) })
function onResize() { computeH(); computeVizH() }

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
    if (subTab.value === 'viz') computeVizH()
    ElMessage.success(`查询到 ${res.data.total} 行`)
  } catch (e) {
    ElMessage.error('查询失败')
  } finally {
    loading.value = false
  }
}

// AI 一句话生成图表配置:当前结果列 + 需求 → cfg,回填后 EchartsBuilder 自动应用
async function onAiChart(question) {
  const cols = rows.value.length ? Object.keys(rows.value[0]) : []
  if (!cols.length) { ElMessage.warning('先执行查询获取数据'); return }
  aic.loading = true
  try {
    const res = await aiChart(props.model.id, { question, columns: cols })
    vizCfg.value = res.data.cfg
    ElMessage.success('已生成图表配置')
  } catch (e) {
    ElMessage.error(e?.msg || e?.message || '生成失败')
  } finally { aic.loading = false }
}

// ---------------- 分析模板 ----------------
async function loadTemplates() {
  if (!props.model || !props.model.id) { templates.value = []; return }
  try { templates.value = (await listAnalysisTemplate(props.model.id)).data || [] } catch (e) { /* 忽略 */ }
}
function openSaveTpl() { tplDlg.name = ''; tplDlg.remark = ''; tplDlg.visible = true }
async function doSaveTpl() {
  if (!tplDlg.name.trim()) { ElMessage.warning('请填写看板名称'); return }
  await saveAnalysisTemplate({
    name: tplDlg.name.trim(),
    modelId: props.model.id,
    modelName: props.model.name,
    query: { type: 'native', native: native.value },
    chartSpec: vizCfg.value || null,
    remark: tplDlg.remark
  })
  ElMessage.success('已保存为看板')
  tplDlg.visible = false
  loadTemplates()
}
// 应用模板:回填查询 → 取数 → 用模板图表配置渲染
async function applyTemplate(tid) {
  if (!tid) return
  const t = templates.value.find(x => x.id === tid)
  if (!t) return
  native.value = (t.query && t.query.native) || native.value
  subTab.value = 'viz'
  await runNative()
  if (rows.value.length) vizCfg.value = t.chartSpec || null
}
async function delTpl() {
  if (!curTpl.value) return
  try { await ElMessageBox.confirm('删除该看板?', '提示', { type: 'warning' }) } catch (e) { return }
  await delAnalysisTemplate(curTpl.value)
  ElMessage.success('已删除'); curTpl.value = ''; loadTemplates()
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
.viz-bar .muted { color: #909399; font-size: 12px; margin-left: auto; }
.viz-wrap { min-height: 360px; }
.ai-out {
  margin: 8px 0; padding: 8px 10px; max-height: 220px; overflow: auto;
  background: #1e1e1e; color: #d4d4d4; border-radius: 4px;
  font-family: Consolas, Monaco, monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all;
}
.cursor { animation: blink 1s steps(1) infinite; color: #67c23a; }
@keyframes blink { 50% { opacity: 0; } }
</style>
