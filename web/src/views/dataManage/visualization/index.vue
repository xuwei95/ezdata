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
          <span class="tip">改完图后点图内「保存」按钮捕获配置,再点这里「保存」入库</span>
        </div>
        <div class="ed-query">
          <el-input v-model="ed.native" type="textarea" :rows="3"
            placeholder="原生查询(SQL / ES DSL);选择模型后自动预填" />
          <el-button type="primary" icon="Search" :loading="ed.loading" :disabled="!ed.modelId" @click="runQuery">查询</el-button>
        </div>
        <div class="ed-viz" v-loading="ed.vizLoading" element-loading-text="生成中…">
          <iframe v-if="ed.html" :srcdoc="ed.html" class="pyg-frame"
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads" />
          <el-empty v-else :description="ed.rows.length ? '点上方查询后拖拽分析' : '选模型 → 查询 → 拖拽/AI 生成图,点图内保存捕获配置'" />
        </div>
      </div>
    </el-dialog>

    <!-- 预览:全屏纯图(无配置项) -->
    <el-dialog v-model="pv.visible" :title="'预览 - ' + pv.name" fullscreen append-to-body class="viz-preview-dialog">
      <div class="preview" v-loading="pv.loading" element-loading-text="渲染中…">
        <iframe v-if="pv.html" :srcdoc="pv.html" class="pyg-frame"
          sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads" />
        <el-empty v-else :description="pv.err || '无图表配置,无法纯图预览(该模板仅存了查询)'" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup name="Visualization">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listModel, listAnalysisTemplate, saveAnalysisTemplate, delAnalysisTemplate,
  getSampleQuery, queryModel, walkerHtml
} from '@/api/dataManage/data'

const VIZ_CAP = 1000
const loading = ref(false)
const list = ref([])
const models = ref([])
const filterModel = ref('')

const ed = reactive({
  visible: false, id: '', name: '', modelId: '', modelName: '', remark: '',
  native: '', rows: [], spec: '', html: '', loading: false, vizLoading: false
})
const pv = reactive({ visible: false, name: '', html: '', loading: false, err: '' })

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
    modelName: row?.modelName || '', remark: row?.remark || '',
    native: (row?.query && row.query.native) || '', rows: [], html: '', vizLoading: false,
    spec: row?.chartSpec ? JSON.stringify(row.chartSpec) : ''
  })
  if (ed.modelId) { await runQuery(); if (ed.rows.length) await renderEditor(ed.spec) }
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
.ed-query .el-textarea { flex: 1; }
.ed-viz { flex: 1; min-height: 300px; }
.preview { height: calc(100vh - 110px); }
.pyg-frame { width: 100%; height: 100%; border: 1px solid #ebeef5; border-radius: 6px; background: #fff; }
</style>
