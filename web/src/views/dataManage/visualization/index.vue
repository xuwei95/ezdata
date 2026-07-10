<template>
  <div class="app-container viz-mgr">
    <!-- 顶部:按数据模型过滤 + 新增 -->
    <el-form :inline="true" class="bar">
      <el-form-item label="数据模型">
        <el-select v-model="filterModel" clearable filterable placeholder="全部模型" style="width: 220px"
          @change="loadList">
          <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Plus" @click="openEditor()">新建可视化</el-button>
        <el-button icon="Refresh" @click="loadList">刷新</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="list" border v-loading="loading">
      <el-table-column type="index" label="#" width="55" />
      <el-table-column label="名称" prop="name" min-width="180" show-overflow-tooltip />
      <el-table-column label="数据模型" prop="modelName" min-width="150" show-overflow-tooltip />
      <el-table-column label="图表" width="90">
        <template #default="s">
          <el-tag size="small" :type="s.row.chartSpec ? 'success' : 'info'">
            {{ s.row.chartSpec ? '已配置' : '仅查询' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" prop="updateTime" width="170" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="s">
          <el-button link type="primary" icon="View" @click="openPreview(s.row)">预览</el-button>
          <el-button link type="primary" icon="Edit" @click="openEditor(s.row)">编辑</el-button>
          <el-button link type="danger" icon="Delete" @click="del(s.row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>暂无可视化模板,点「新建可视化」创建</template>
    </el-table>

    <!-- 编辑器:全屏 -->
    <el-dialog v-model="ed.visible" :title="ed.id ? '编辑可视化' : '新建可视化'" fullscreen append-to-body
      :close-on-click-modal="false" class="viz-editor-dialog">
      <div class="editor">
        <div class="ed-head">
          <el-input v-model="ed.name" placeholder="模板名称" style="width: 220px" />
          <el-select v-model="ed.modelId" filterable placeholder="选择数据模型" style="width: 220px" @change="onModelChange">
            <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
          <el-input v-model="ed.remark" placeholder="说明(可选)" style="width: 240px" />
          <el-button type="primary" icon="Check" :disabled="!ed.modelId || !ed.name" @click="save">保存</el-button>
          <span class="tip">用「AI 生成图表」得到图后点「保存」入库(手拖的图暂不带配置,后续支持)</span>
        </div>
        <div class="ed-query">
          <div class="q-main">
            <el-input v-model="ed.native" type="textarea" :rows="3"
              placeholder="原生查询(SQL / ES DSL);选择模型后自动预填,或点「AI 生成查询」" />
            <div v-if="aiq.open" class="q-panel">
              <el-input v-model="aiq.question" type="textarea" :rows="2"
                placeholder="用自然语言描述你想查什么,如:各城市销售额 top10" @keyup.enter.stop="genQuery" />
              <div class="q-panel-bar">
                <el-button size="small" type="primary" :loading="aiq.loading" @click="genQuery">
                  {{ aiq.output ? '重新生成' : '生成' }}</el-button>
                <el-button v-if="aiq.output && !aiq.loading" size="small" type="success" @click="applyQuery">采用到查询</el-button>
                <el-button v-if="aiq.output" size="small" @click="aiq.output = ''">清空</el-button>
              </div>
              <pre v-if="aiq.output" class="ai-out">{{ aiq.output }}<span v-if="aiq.loading" class="cursor">▋</span></pre>
            </div>
          </div>
          <div class="q-btns">
            <el-button icon="MagicStick" :disabled="!ed.modelId" @click="aiq.open = !aiq.open">AI 生成查询</el-button>
            <el-button type="primary" icon="Search" :loading="ed.loading" :disabled="!ed.modelId" @click="runQuery">查询</el-button>
          </div>
        </div>
        <div class="ed-viz-bar">
          <el-input v-model="ed.chartQ" size="small" style="max-width: 320px" clearable
            placeholder="一句话生成图表(AI),如:按城市看销售额柱状图" @keyup.enter="genChart" />
          <el-button size="small" type="primary" icon="MagicStick" :loading="ed.vizLoading"
            :disabled="!ed.rows.length" @click="genChart">AI 生成图表</el-button>
          <el-button size="small" icon="Refresh" :disabled="!ed.rows.length" @click="renderEditor('')">重置图表</el-button>
          <el-button size="small" :type="ed.spike ? 'warning' : 'default'" @click="ed.spike = !ed.spike">
            {{ ed.spike ? '← 回 iframe' : '🧪 原生渲染试验' }}</el-button>
        </div>
        <div class="ed-viz" v-loading="ed.vizLoading" element-loading-text="生成中…">
          <GwSpike v-if="ed.spike" :rows="ed.rows" />
          <template v-else>
            <iframe v-if="ed.html" :srcdoc="ed.html" class="pyg-frame"
              sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads" />
            <el-empty v-else :description="ed.rows.length ? '拖拽分析 或 上方「AI 生成图表」;AI 生成的图可保存入库' : '选模型 → 查询 → 拖拽/AI 生成图'" />
          </template>
        </div>
      </div>
    </el-dialog>

    <!-- 预览:纯图(无配置项),普通弹窗 -->
    <el-dialog v-model="pv.visible" :title="'预览 - ' + pv.name" width="900px" top="6vh" append-to-body
      class="viz-preview-dialog">
      <div class="preview" v-loading="pv.loading" element-loading-text="渲染中…">
        <iframe v-if="pv.html" :srcdoc="pv.html" class="pyg-frame" style="height: 560px"
          sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads" />
        <el-empty v-else :description="pv.err || '无图表配置,无法纯图预览(该模板仅存了查询)'" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup name="Visualization">
import { ref, reactive, onMounted, onUnmounted, defineAsyncComponent } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// 懒加载:原生 graphic-walker 试验组件(若该 alpha 包构建失败,只影响此区、不拖垮页面)
const GwSpike = defineAsyncComponent(() => import('./GwSpike.vue'))
import {
  listModel, listAnalysisTemplate, saveAnalysisTemplate, delAnalysisTemplate,
  getSampleQuery, queryModel, walkerHtml, walkerAiHtml
} from '@/api/dataManage/data'
import { getToken } from '@/utils/auth'

const VIZ_CAP = 1000
const loading = ref(false)
const list = ref([])
const models = ref([])
const filterModel = ref('')

const ed = reactive({
  visible: false, id: '', name: '', modelId: '', modelName: '', remark: '',
  native: '', chartQ: '', rows: [], spec: '', html: '', loading: false, vizLoading: false, spike: false
})
const aiq = reactive({ open: false, question: '', output: '', loading: false })
const pv = reactive({ visible: false, name: '', html: '', loading: false, err: '' })
const AI_BASE = import.meta.env.VITE_APP_BASE_API || ''

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
  const reader = resp.body.getReader(); const dec = new TextDecoder()
  for (;;) { const { done, value } = await reader.read(); if (done) break; onChunk(dec.decode(value, { stream: true })) }
}

async function loadModels() {
  try { models.value = (await listModel({ pageNum: 1, pageSize: 1000 })).rows || [] } catch (e) { /* 忽略 */ }
}
async function loadList() {
  loading.value = true
  try { list.value = (await listAnalysisTemplate(filterModel.value || undefined)).data || [] }
  finally { loading.value = false }
}

// ---- 编辑器 ----
async function openEditor(row) {
  Object.assign(ed, {
    visible: true, id: row?.id || '', name: row?.name || '', modelId: row?.modelId || '',
    modelName: row?.modelName || '', remark: row?.remark || '', chartQ: '', spike: false,
    native: (row?.query && row.query.native) || '', rows: [], html: '', vizLoading: false,
    spec: row?.chartSpec ? JSON.stringify(row.chartSpec) : ''
  })
  aiq.open = false; aiq.question = ''; aiq.output = ''
  if (ed.modelId) { await runQuery(); if (ed.rows.length) await renderEditor(ed.spec) }
}
// AI 生成查询(流式 NL→SQL,采用到查询框)
async function genQuery() {
  if (!ed.modelId) { ElMessage.warning('请先选择数据模型'); return }
  if (!aiq.question.trim()) { ElMessage.warning('请描述你想查什么'); return }
  aiq.output = ''; aiq.loading = true
  try { await streamAi(`/data/model/${ed.modelId}/ai-query/stream`, { question: aiq.question }, (c) => { aiq.output += c }) }
  catch (e) { ElMessage.error('生成失败: ' + e.message) } finally { aiq.loading = false }
}
function applyQuery() {
  ed.native = stripFence(aiq.output).replace(/;\s*$/, '')
  aiq.open = false
  ElMessage.success('已采用到查询框,点「查询」执行')
}
// AI 一句话生成图表(用当前查询结果;系统 LLM 生成配置,预填可继续拖)
async function genChart() {
  if (!ed.rows.length) { ElMessage.warning('先查询获取数据'); return }
  if (!ed.chartQ.trim()) { ElMessage.warning('请描述你想要的图表'); return }
  ed.vizLoading = true
  try {
    const res = await walkerAiHtml(ed.modelId, { question: ed.chartQ, rows: ed.rows.slice(0, VIZ_CAP) })
    ed.html = res.data.html || ''
    ed.spec = res.data.spec || ed.spec
  } catch (e) { ElMessage.error(e?.msg || e?.message || '生成失败') } finally { ed.vizLoading = false }
}
async function onModelChange(mId) {
  const m = models.value.find(x => x.id === mId)
  ed.modelName = m ? m.name : ''
  ed.spec = ''; ed.html = ''; ed.rows = []
  try { const q = (await getSampleQuery(mId)).data.native; ed.native = typeof q === 'string' ? q : JSON.stringify(q, null, 2) } catch (e) { /* 忽略 */ }
}
async function runQuery() {
  if (!ed.modelId) { ElMessage.warning('请先选择数据模型'); return }
  if (!ed.native.trim()) { ElMessage.warning('请输入查询语句'); return }
  ed.loading = true
  try {
    let n = ed.native.trim(); try { n = JSON.parse(n) } catch (e) { /* SQL 串 */ }
    const res = await queryModel(ed.modelId, { native: n })
    ed.rows = res.data.records || []
    ElMessage.success(`查询到 ${res.data.total} 行`)
    await renderEditor(ed.spec)
  } catch (e) { ElMessage.error('查询失败') } finally { ed.loading = false }
}
async function renderEditor(spec) {
  if (!ed.rows.length) return
  ed.vizLoading = true
  try {
    const res = await walkerHtml(ed.modelId, { rows: ed.rows.slice(0, VIZ_CAP), spec: spec || '' })
    ed.html = res.data.html || ''
  } finally { ed.vizLoading = false }
}
async function save() {
  if (!ed.name.trim()) { ElMessage.warning('请填写模板名称'); return }
  if (!ed.modelId) { ElMessage.warning('请选择数据模型'); return }
  await saveAnalysisTemplate({
    id: ed.id || undefined, name: ed.name.trim(), modelId: ed.modelId, modelName: ed.modelName,
    query: { type: 'native', native: ed.native }, chartSpec: ed.spec ? JSON.parse(ed.spec) : null, remark: ed.remark
  })
  ElMessage.success('已保存')
  ed.visible = false
  loadList()
}

// ---- 预览:纯图(gw_mode=renderer,无配置项)----
async function openPreview(row) {
  if (!row.chartSpec) { ElMessage.info('该模板仅存了查询,无图表配置,无法纯图预览'); return }
  Object.assign(pv, { visible: true, name: row.name, html: '', loading: true, err: '' })
  try {
    let n = (row.query && row.query.native) || ''
    try { n = JSON.parse(n) } catch (e) { /* SQL 串 */ }
    const q = await queryModel(row.modelId, { native: n })
    const rows = q.data.records || []
    if (!rows.length) { pv.err = '查询无数据'; return }
    const res = await walkerHtml(row.modelId, { rows: rows.slice(0, VIZ_CAP), spec: JSON.stringify(row.chartSpec), mode: 'renderer' })
    pv.html = res.data.html || ''
  } catch (e) { pv.err = e?.msg || e?.message || '渲染失败'; ElMessage.error(pv.err) } finally { pv.loading = false }
}

async function del(row) {
  try { await ElMessageBox.confirm(`删除可视化「${row.name}」?`, '提示', { type: 'warning' }) } catch (e) { return }
  await delAnalysisTemplate(row.id)
  ElMessage.success('已删除'); loadList()
}

// pygwalker 内层 iframe「保存」→ 桥接脚本回传 visSpec → 记为编辑器当前配置
function onPygMsg(e) {
  const d = e && e.data
  if (d && d.__pygSpec === true) {
    ed.spec = JSON.stringify(d.visSpec || [])
    ElMessage.success('已捕获图表配置,点「保存」入库')
  }
}
onMounted(() => { loadModels(); loadList(); window.addEventListener('message', onPygMsg) })
onUnmounted(() => window.removeEventListener('message', onPygMsg))
</script>

<style scoped>
.viz-mgr .bar { margin-bottom: 8px; }
.editor { display: flex; flex-direction: column; height: calc(100vh - 110px); }
.ed-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.ed-head .tip { font-size: 12px; color: #909399; }
.ed-query { display: flex; gap: 8px; align-items: flex-start; margin-bottom: 8px; }
.q-main { flex: 1; }
.q-panel { margin-top: 6px; padding: 8px 10px; border: 1px dashed #c0c4cc; border-radius: 6px; background: #fafafa; }
.q-panel-bar { margin-top: 6px; display: flex; gap: 6px; }
.q-btns { display: flex; flex-direction: column; gap: 6px; }
.ed-viz-bar { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.ed-viz { flex: 1; min-height: 300px; }
.ai-out {
  margin: 8px 0 0; padding: 8px 10px; max-height: 160px; overflow: auto;
  background: #1e1e1e; color: #d4d4d4; border-radius: 4px;
  font-family: Consolas, Monaco, monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all;
}
.cursor { animation: blink 1s steps(1) infinite; color: #67c23a; }
@keyframes blink { 50% { opacity: 0; } }
.ed-viz { flex: 1; min-height: 260px; }
.preview { height: calc(100vh - 110px); }
.pyg-frame { width: 100%; height: 100%; border: 1px solid #ebeef5; border-radius: 6px; background: #fff; }
</style>
