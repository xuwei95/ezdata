<template>
  <div class="app-container viz-mgr">
    <!-- 顶部:按数据模型过滤 + 新增 -->
    <el-form :inline="true" class="bar">
      <el-form-item label="数据模型">
        <el-select v-model="filterModel" clearable filterable placeholder="全部模型" style="width: 220px" @change="loadList">
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
          <el-tag size="small" :type="isEchartsCfg(s.row.chartSpec) ? 'success' : 'info'">
            {{ isEchartsCfg(s.row.chartSpec) ? '已配置' : '仅查询' }}</el-tag>
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
          <span class="tip">选模型 → 查询 → 选图表类型/字段/聚合出图 → 保存</span>
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
        <div class="ed-viz">
          <EchartsBuilder v-if="ed.rows.length" :rows="ed.rows" :config="ed.cfg" :height="edChartH"
            @update:config="(c) => (ed.cfg = c)" />
          <el-empty v-else description="选模型 → 查询,再选图表类型/字段出图" />
        </div>
      </div>
    </el-dialog>

    <!-- 预览:纯图(无配置项),普通弹窗 -->
    <el-dialog v-model="pv.visible" :title="'预览 - ' + pv.name" width="900px" top="6vh" append-to-body>
      <div class="preview" v-loading="pv.loading" element-loading-text="加载中…">
        <EchartsBuilder v-if="pv.rows.length && pv.cfg" :rows="pv.rows" :config="pv.cfg" :show-controls="false" :height="520" />
        <el-empty v-else :description="pv.err || '无图表配置,无法预览'" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup name="Visualization">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listModel, listAnalysisTemplate, saveAnalysisTemplate, delAnalysisTemplate,
  getSampleQuery, queryModel
} from '@/api/dataManage/data'
import { getToken } from '@/utils/auth'
import EchartsBuilder from './EchartsBuilder.vue'

const QUERY_CAP = 5000
const CHART_TYPES = ['bar', 'line', 'area', 'pie', 'scatter']
const loading = ref(false)
const list = ref([])
const models = ref([])
const filterModel = ref('')
const edChartH = ref(Math.max(360, window.innerHeight - 330))

const ed = reactive({
  visible: false, id: '', name: '', modelId: '', modelName: '', remark: '',
  native: '', rows: [], cfg: null, loading: false
})
const aiq = reactive({ open: false, question: '', output: '', loading: false })
const pv = reactive({ visible: false, name: '', rows: [], cfg: null, loading: false, err: '' })
const AI_BASE = import.meta.env.VITE_APP_BASE_API || ''

// 判断是否为 ECharts 图表配置(区分旧 pygwalker 格式/仅查询)
function isEchartsCfg(c) {
  return !!c && typeof c === 'object' && !Array.isArray(c) && CHART_TYPES.includes(c.type)
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
  const reader = resp.body.getReader(); const dec = new TextDecoder()
  for (;;) { const { done, value } = await reader.read(); if (done) break; onChunk(dec.decode(value, { stream: true })) }
}

async function loadModels() {
  try { models.value = (await listModel({ pageNum: 1, pageSize: 1000 })).rows || [] } catch (e) { /* 忽略 */ }
}
async function loadList() {
  loading.value = true
  try { list.value = (await listAnalysisTemplate(filterModel.value || undefined)).data || [] } finally { loading.value = false }
}

// ---- 编辑器 ----
async function openEditor(row) {
  Object.assign(ed, {
    visible: true, id: row?.id || '', name: row?.name || '', modelId: row?.modelId || '',
    modelName: row?.modelName || '', remark: row?.remark || '',
    native: (row?.query && row.query.native) || '', rows: [], loading: false,
    cfg: isEchartsCfg(row?.chartSpec) ? { ...row.chartSpec } : null
  })
  aiq.open = false; aiq.question = ''; aiq.output = ''
  if (ed.modelId) await runQuery()
}
async function onModelChange(mId) {
  const m = models.value.find((x) => x.id === mId)
  ed.modelName = m ? m.name : ''
  ed.rows = []; ed.cfg = null
  try { const q = (await getSampleQuery(mId)).data.native; ed.native = typeof q === 'string' ? q : JSON.stringify(q, null, 2) } catch (e) { /* 忽略 */ }
}
async function runQuery() {
  if (!ed.modelId) { ElMessage.warning('请先选择数据模型'); return }
  if (!ed.native.trim()) { ElMessage.warning('请输入查询语句'); return }
  ed.loading = true
  try {
    let n = ed.native.trim(); try { n = JSON.parse(n) } catch (e) { /* SQL 串 */ }
    const res = await queryModel(ed.modelId, { native: n })
    ed.rows = (res.data.records || []).slice(0, QUERY_CAP)
    ElMessage.success(`查询到 ${res.data.total} 行`)
  } catch (e) { ElMessage.error('查询失败') } finally { ed.loading = false }
}
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
async function save() {
  if (!ed.name.trim()) { ElMessage.warning('请填写模板名称'); return }
  if (!ed.modelId) { ElMessage.warning('请选择数据模型'); return }
  await saveAnalysisTemplate({
    id: ed.id || undefined, name: ed.name.trim(), modelId: ed.modelId, modelName: ed.modelName,
    query: { type: 'native', native: ed.native }, chartSpec: ed.cfg || null, remark: ed.remark
  })
  ElMessage.success('已保存')
  ed.visible = false
  loadList()
}

// ---- 预览:纯图 ----
async function openPreview(row) {
  if (!isEchartsCfg(row.chartSpec)) { ElMessage.info('该模板无图表配置(或为旧格式),请编辑后重新保存'); return }
  Object.assign(pv, { visible: true, name: row.name, rows: [], cfg: null, loading: true, err: '' })
  try {
    let n = (row.query && row.query.native) || ''
    try { n = JSON.parse(n) } catch (e) { /* SQL 串 */ }
    const q = await queryModel(row.modelId, { native: n })
    const rows = (q.data.records || []).slice(0, QUERY_CAP)
    if (!rows.length) { pv.err = '查询无数据'; return }
    pv.rows = rows
    pv.cfg = { ...row.chartSpec }
  } catch (e) { pv.err = e?.msg || e?.message || '加载失败'; ElMessage.error(pv.err) } finally { pv.loading = false }
}

async function del(row) {
  try { await ElMessageBox.confirm(`删除可视化「${row.name}」?`, '提示', { type: 'warning' }) } catch (e) { return }
  await delAnalysisTemplate(row.id)
  ElMessage.success('已删除'); loadList()
}

loadModels(); loadList()
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
.ed-viz { flex: 1; min-height: 300px; }
.preview { min-height: 540px; }
.ai-out {
  margin: 8px 0 0; padding: 8px 10px; max-height: 160px; overflow: auto;
  background: #1e1e1e; color: #d4d4d4; border-radius: 4px;
  font-family: Consolas, Monaco, monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all;
}
.cursor { animation: blink 1s steps(1) infinite; color: #67c23a; }
@keyframes blink { 50% { opacity: 0; } }
</style>
