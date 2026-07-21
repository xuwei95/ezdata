<template>
  <el-dialog
    v-model="visible"
    :title="ed.id ? '编辑单图看板' : '新建单图看板'"
    fullscreen
    append-to-body
    :close-on-click-modal="false"
    class="chart-editor-dialog"
  >
    <div class="editor">
      <div class="ed-head">
        <el-input v-model="ed.name" :placeholder="$t('看板名称')" style="width: 220px" />
        <el-select v-model="ed.modelId" filterable :placeholder="$t('选择数据模型')" style="width: 220px" @change="onModelChange">
          <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
        </el-select>
        <el-input v-model="ed.remark" :placeholder="$t('说明(可选)')" style="width: 240px" />
        <el-select v-model="ed.refreshInterval" size="small" style="width: 116px" :placeholder="$t('自动刷新')">
          <el-option :value="0" :label="$t('不自动刷新')" />
          <el-option :value="10" :label="$t('每 10 秒')" />
          <el-option :value="30" :label="$t('每 30 秒')" />
          <el-option :value="60" :label="$t('每 1 分钟')" />
          <el-option :value="300" :label="$t('每 5 分钟')" />
        </el-select>
        <el-button size="small" :type="varsMgr.open ? 'primary' : 'default'" icon="Setting" @click="varsMgr.open = !varsMgr.open">{{ $t('变量') }}</el-button>
        <el-button type="primary" icon="Check" :disabled="!ed.modelId || !ed.name" :loading="saving" @click="save">{{ $t('保存') }}</el-button>
        <span class="tip">{{ $t('选模型 →(可选)定义变量 → 查询 → 选图表出图 → 保存') }}</span>
      </div>

      <!-- 变量:筛选栏(当前值)+ 定义管理 -->
      <div v-if="ed.vars.length" class="ed-vars">
        <template v-for="v in ed.vars" :key="v.name">
          <span class="vlabel">{{ v.label || v.name }}</span>
          <el-date-picker v-if="v.type === 'date'" v-model="ed.varVals[v.name]" type="date" value-format="YYYY-MM-DD" size="small" style="width: 150px" />
          <el-date-picker v-else-if="v.type === 'daterange'" v-model="ed.varVals[v.name]" type="daterange" value-format="YYYY-MM-DD" size="small" style="width: 230px" start-placeholder="开始" end-placeholder="结束" />
          <el-select v-else-if="v.type === 'select'" v-model="ed.varVals[v.name]" size="small" clearable style="width: 150px">
            <el-option v-for="o in (v.optionsText || '').split(',').map((s) => s.trim()).filter(Boolean)" :key="o" :label="o" :value="o" />
          </el-select>
          <el-input v-else v-model="ed.varVals[v.name]" size="small" style="width: 150px" />
        </template>
      </div>
      <div v-if="varsMgr.open" class="ed-vars-mgr">
        <div v-for="(v, i) in ed.vars" :key="i" class="vrow">
          <el-input v-model="v.name" size="small" :placeholder="$t('变量名(如 city)')" style="width: 150px" />
          <el-input v-model="v.label" size="small" :placeholder="$t('显示名')" style="width: 110px" />
          <el-select v-model="v.type" size="small" style="width: 104px">
            <el-option :label="$t('文本')" value="text" />
            <el-option :label="$t('日期')" value="date" />
            <el-option :label="$t('日期范围')" value="daterange" />
            <el-option :label="$t('下拉')" value="select" />
          </el-select>
          <el-input v-model="v.default" size="small" :placeholder="$t('默认值')" style="width: 110px" />
          <el-input v-if="v.type === 'select'" v-model="v.optionsText" size="small" :placeholder="$t('选项,逗号分隔')" style="flex: 1; min-width: 120px" />
          <el-button size="small" icon="Delete" text @click="ed.vars.splice(i, 1)" />
        </div>
        <div class="vrow-add">
          <el-button size="small" text type="primary" icon="Plus" @click="addVar">{{ $t('添加变量') }}</el-button>
          <span class="tip">{{ VAR_HINT }}</span>
        </div>
      </div>

      <div class="ed-query">
        <div class="q-main">
          <el-input v-model="ed.native" type="textarea" :rows="3" :autosize="{ minRows: 3, maxRows: 10 }"
            :placeholder="$t('原生查询(SQL / ES DSL);选择模型后自动预填,或点「AI 生成查询」')" />
          <div v-if="aiq.open" class="q-panel">
            <el-input v-model="aiq.question" type="textarea" :rows="2"
              :placeholder="$t('用自然语言描述你想查什么,如:各城市销售额 top10')" @keyup.enter.stop="genQuery" />
            <div class="q-panel-bar">
              <el-button size="small" type="primary" :loading="aiq.loading" @click="genQuery">
                {{ aiq.output ? '重新生成' : '生成' }}</el-button>
              <el-button v-if="aiq.output && !aiq.loading" size="small" type="success" @click="applyQuery">{{ $t('采用到查询') }}</el-button>
              <el-button v-if="aiq.output" size="small" @click="aiq.output = ''">{{ $t('清空') }}</el-button>
            </div>
            <pre v-if="aiq.output" class="ai-out">{{ aiq.output }}<span v-if="aiq.loading" class="cursor">▋</span></pre>
          </div>
        </div>
        <div class="q-btns">
          <el-button icon="MagicStick" :disabled="!ed.modelId" @click="aiq.open = !aiq.open">{{ $t('AI 生成查询') }}</el-button>
          <el-button type="primary" icon="Search" :loading="ed.loading" :disabled="!ed.modelId" @click="runQuery">{{ $t('查询') }}</el-button>
        </div>
      </div>
      <div class="ed-viz">
        <EchartsBuilder v-if="ed.rows.length" :rows="ed.rows" :config="ed.cfg" :height="edChartH"
          ai-enabled :ai-loading="aic.loading" @ai-generate="onAiChart"
          @update:config="(c) => (ed.cfg = c)" />
        <el-empty v-else :description="$t('选模型 → 查询,再选图表类型/字段出图')" />
      </div>
    </div>
  </el-dialog>
</template>

<script setup name="ChartEditor">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { listModel, saveAnalysisTemplate, getSampleQuery, aiChart, getAnalysisTemplate } from '@/api/dataManage/data'
import { getToken } from '@/utils/auth'
import EchartsBuilder from '../visualization/EchartsBuilder.vue'
import { isEchartsCfg, nativeToText, parseNative, fetchBoardRows } from '../visualization/board.js'

const props = defineProps({
  modelValue: { type: Boolean, default: false }, // 弹窗显隐
  id: { type: String, default: '' } // 为空=新建
})
const emit = defineEmits(['update:modelValue', 'saved'])
const visible = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })

const QUERY_CAP = 5000
// 提示文案含双花括号,放脚本常量里(模板里直接写 {{ }} 会被 Vue 当插值解析)
const VAR_HINT = '查询里用 {{变量名}} 引用;日期范围会生成 {{名_start}} / {{名_end}} 两个占位'
const AI_BASE = import.meta.env.VITE_APP_BASE_API || ''
const models = ref([])
const saving = ref(false)
const edChartH = ref(Math.max(360, window.innerHeight - 260))

const ed = reactive({
  id: '', name: '', modelId: '', modelName: '', remark: '',
  native: '', rows: [], cfg: null, loading: false,
  vars: [], varVals: {}, refreshInterval: 0 // 看板变量定义 / 当前值 / 自动刷新间隔(秒)
})
const varsMgr = reactive({ open: false })
const aiq = reactive({ open: false, question: '', output: '', loading: false })
const aic = reactive({ loading: false }) // AI 生成图表配置

function addVar() {
  ed.vars.push({ name: '', label: '', type: 'text', default: '', optionsText: '' })
}
// 变量当前值 → 取数用 {name: value};daterange 展开成 名_start / 名_end
function paramValues() {
  const out = {}
  for (const v of ed.vars) {
    if (!v.name) continue
    let val = ed.varVals[v.name]
    if (val === undefined || val === null || val === '') val = v.default
    if (v.type === 'daterange' && Array.isArray(val)) { out[v.name + '_start'] = val[0]; out[v.name + '_end'] = val[1] }
    else out[v.name] = val
  }
  return out
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

// ---- 编辑器 ----
async function openEditor(row) {
  const defs = Array.isArray(row?.params) ? row.params : []
  Object.assign(ed, {
    id: row?.id || '', name: row?.name || '', modelId: row?.modelId || '',
    modelName: row?.modelName || '', remark: row?.remark || '',
    native: nativeToText(row?.query && row.query.native), rows: [], loading: false,
    cfg: isEchartsCfg(row?.chartSpec) ? { ...row.chartSpec } : null,
    vars: defs.map((p) => ({ name: p.name, label: p.label || '', type: p.type || 'text', default: p.default ?? '', optionsText: (p.options || []).join(',') })),
    varVals: Object.fromEntries(defs.map((p) => [p.name, p.value ?? p.default ?? ''])),
    refreshInterval: row?.refreshInterval || 0
  })
  varsMgr.open = false
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
  if (!nativeToText(ed.native).trim()) { ElMessage.warning('请输入查询语句'); return }
  ed.loading = true
  try {
    ed.rows = await fetchBoardRows(ed.modelId, ed.native, paramValues(), QUERY_CAP)
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
// AI 生成图表配置:一句话 + 当前结果列 → cfg,回填后 EchartsBuilder 自动应用
async function onAiChart(question) {
  if (!ed.modelId) { ElMessage.warning('请先选择数据模型'); return }
  const columns = ed.rows.length ? Object.keys(ed.rows[0]) : []
  if (!columns.length) { ElMessage.warning('请先查询出数据'); return }
  aic.loading = true
  try {
    const res = await aiChart(ed.modelId, { question, columns })
    ed.cfg = res.data.cfg
    ElMessage.success('已生成图表配置')
  } catch (e) { ElMessage.error(e?.msg || e?.message || '生成失败') } finally { aic.loading = false }
}
async function save() {
  if (!ed.name.trim()) { ElMessage.warning('请填写看板名称'); return }
  if (!ed.modelId) { ElMessage.warning('请选择数据模型'); return }
  const params = ed.vars.filter((v) => v.name).map((v) => ({
    name: v.name, label: v.label || '', type: v.type || 'text', default: v.default ?? '',
    value: ed.varVals[v.name] ?? v.default ?? '',
    ...(v.type === 'select' ? { options: (v.optionsText || '').split(',').map((s) => s.trim()).filter(Boolean) } : {})
  }))
  saving.value = true
  try {
    const { data } = await saveAnalysisTemplate({
      id: ed.id || undefined, name: ed.name.trim(), modelId: ed.modelId, modelName: ed.modelName,
      query: { type: 'native', native: parseNative(ed.native) }, chartSpec: ed.cfg || null,
      params, refreshInterval: ed.refreshInterval || 0, remark: ed.remark
    })
    if (data && data.id) ed.id = data.id
    ElMessage.success('已保存')
    emit('saved', ed.id)
    visible.value = false
  } catch (e) { ElMessage.error('保存失败: ' + (e?.msg || e?.message || e)) } finally { saving.value = false }
}

// 打开弹窗时:按 id 拉详情进编辑,无 id 则空白新建
async function onOpen() {
  if (!models.value.length) await loadModels()
  if (props.id) {
    try { const r = await getAnalysisTemplate(props.id); await openEditor(r.data) }
    catch (e) { ElMessage.error('加载看板失败') }
  } else {
    await openEditor()
  }
}
watch(() => props.modelValue, (v) => { if (v) onOpen() })

loadModels()
</script>

<style scoped>
.editor { display: flex; flex-direction: column; height: calc(100vh - 120px); }
.ed-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.ed-head .tip { font-size: 12px; color: #909399; }
.ed-vars { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; padding: 6px 10px; background: #f5f7fa; border-radius: 6px; }
.ed-vars .vlabel { font-size: 12px; color: #606266; }
.ed-vars-mgr { margin-bottom: 8px; padding: 8px 10px; border: 1px dashed #c0c4cc; border-radius: 6px; }
.ed-vars-mgr .vrow { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.ed-vars-mgr .vrow-add { display: flex; align-items: center; gap: 10px; }
.ed-vars-mgr .tip { font-size: 12px; color: #909399; }
.ed-query { display: flex; gap: 8px; align-items: flex-start; margin-bottom: 8px; }
.q-main { flex: 1; }
.q-panel { margin-top: 6px; padding: 8px 10px; border: 1px dashed #c0c4cc; border-radius: 6px; background: #fafafa; }
.q-panel-bar { margin-top: 6px; display: flex; gap: 6px; }
.q-btns { display: flex; flex-direction: column; gap: 6px; }
.ed-viz { flex: 1; min-height: 300px; }
.ai-out {
  margin: 8px 0 0; padding: 8px 10px; max-height: 160px; overflow: auto;
  background: #1e1e1e; color: #d4d4d4; border-radius: 4px;
  font-family: Consolas, Monaco, monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all;
}
.cursor { animation: blink 1s steps(1) infinite; color: #67c23a; }
@keyframes blink { 50% { opacity: 0; } }
</style>
