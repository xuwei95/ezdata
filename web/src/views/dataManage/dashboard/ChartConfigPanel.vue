<template>
  <div class="ccp">
    <div class="ccp-top">
      <el-select v-model="local.modelId" filterable :placeholder="$t('选择数据模型')" style="width: 220px" @change="onModel">
        <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
      </el-select>
      <el-button icon="MagicStick" :disabled="!local.modelId" @click="aiq.open = !aiq.open">{{ $t('AI 生成查询') }}</el-button>
      <el-button type="primary" icon="Search" :loading="loading" :disabled="!local.modelId" @click="runQuery">{{ $t('查询') }}</el-button>
    </div>
    <span class="ccp-tip">{{ $t('选模型 →(可选)AI 生成查询 → 查询 → 右侧配图') }}</span>

    <el-input v-model="local.native" type="textarea" :rows="3" :autosize="{ minRows: 3, maxRows: 8 }"
      :placeholder="$t('原生查询(SQL / ES DSL);选模型后自动预填')" @change="emitChange" />

    <!-- AI 生成查询面板 -->
    <div v-if="aiq.open" class="ccp-ai">
      <el-input v-model="aiq.question" type="textarea" :rows="2"
        :placeholder="$t('用自然语言描述你想查什么,如:各城市销售额 top10')" @keyup.enter.stop="genQuery" />
      <div class="ccp-ai-bar">
        <el-button size="small" type="primary" :loading="aiq.loading" @click="genQuery">{{ aiq.output ? '重新生成' : '生成' }}</el-button>
        <el-button v-if="aiq.output && !aiq.loading" size="small" type="success" @click="applyQuery">{{ $t('采用到查询') }}</el-button>
        <el-button v-if="aiq.output" size="small" @click="aiq.output = ''">{{ $t('清空') }}</el-button>
      </div>
      <pre v-if="aiq.output" class="ccp-ai-out">{{ aiq.output }}<span v-if="aiq.loading" class="cursor">▋</span></pre>
    </div>

    <div class="ccp-chart">
      <EchartsBuilder v-if="rows.length" :rows="rows" :config="local.cfg" :show-controls="true" :height="chartH"
        ai-enabled :ai-loading="aic.loading" @ai-generate="onAiChart" @update:config="onCfg" />
      <el-empty v-else :description="$t('先「查询」出数据,再配置图表(可用「AI 生成图表」)')" :image-size="60" />
    </div>
  </div>
</template>

<script setup name="ChartConfigPanel">
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import EchartsBuilder from '@/views/dataManage/visualization/EchartsBuilder.vue'
import { fetchBoardRows, nativeToText, parseNative } from '@/views/dataManage/visualization/board.js'
import { getSampleQuery, aiChart } from '@/api/dataManage/data'
import { getToken } from '@/utils/auth'

const props = defineProps({
  compId: { type: String, default: '' }, // 选中组件 id:仅它变化时才同步/自动取数,避免自身 emit 回环
  inline: { type: Object, default: () => ({}) }, // 组件的 {modelId, native, chartSpec}
  models: { type: Array, default: () => [] },
  chartH: { type: Number, default: 360 },
})
const emit = defineEmits(['update:inline'])

const AI_BASE = import.meta.env.VITE_APP_BASE_API || ''
const local = reactive({ modelId: '', native: '', cfg: null })
const rows = ref([])
const loading = ref(false)
const aiq = reactive({ open: false, question: '', output: '', loading: false })
const aic = reactive({ loading: false })

// 仅在"切换选中组件"时把外部 inline 灌入本地并自动取数一次;
// emitChange 只改父层 inline、不改 compId,因此不会回环触发本 watch(修复"一直查询")。
watch(() => props.compId, () => {
  const i = props.inline || {}
  local.modelId = i.modelId || ''
  local.native = nativeToText(i.native)
  local.cfg = i.chartSpec || null
  rows.value = []
  aiq.open = false; aiq.question = ''; aiq.output = ''
  if (local.modelId && local.native.trim()) runQuery()
}, { immediate: true })

function emitChange() {
  emit('update:inline', { modelId: local.modelId, native: parseNative(local.native), chartSpec: local.cfg })
}
async function onModel(mId) {
  try { const q = (await getSampleQuery(mId)).data.native; local.native = typeof q === 'string' ? q : JSON.stringify(q, null, 2) } catch (e) { /* 忽略 */ }
  rows.value = []
  emitChange()
}
async function runQuery() {
  if (!local.modelId) { ElMessage.warning('请先选择数据模型'); return }
  if (!local.native.trim()) { ElMessage.warning('请输入查询语句'); return }
  loading.value = true
  try {
    rows.value = await fetchBoardRows(local.modelId, local.native, null, 5000)
    emitChange()
  } catch (e) { ElMessage.error('查询失败') } finally { loading.value = false }
}
function onCfg(c) { local.cfg = c; emitChange() }

// ---- AI 生成查询(自然语言 → native)----
function stripFence(t) {
  let s = (t || '').trim()
  if (s.startsWith('```')) s = s.replace(/^```[^\n]*\n/, '').replace(/```\s*$/, '').trim()
  return s
}
async function genQuery() {
  if (!local.modelId) { ElMessage.warning('请先选择数据模型'); return }
  if (!aiq.question.trim()) { ElMessage.warning('请描述你想查什么'); return }
  aiq.output = ''; aiq.loading = true
  try {
    const resp = await fetch(AI_BASE + `/data/model/${local.modelId}/ai-query/stream`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + getToken() },
      body: JSON.stringify({ question: aiq.question })
    })
    if (!resp.ok || !resp.body) throw new Error('HTTP ' + resp.status)
    const reader = resp.body.getReader(); const dec = new TextDecoder()
    for (;;) { const { done, value } = await reader.read(); if (done) break; aiq.output += dec.decode(value, { stream: true }) }
  } catch (e) { ElMessage.error('生成失败: ' + e.message) } finally { aiq.loading = false }
}
function applyQuery() {
  local.native = stripFence(aiq.output).replace(/;\s*$/, '')
  aiq.open = false
  emitChange()
  ElMessage.success('已采用到查询框,点「查询」执行')
}

// ---- AI 生成图表(一句话 + 结果列 → chartSpec)----
async function onAiChart(question) {
  if (!local.modelId) { ElMessage.warning('请先选择数据模型'); return }
  const columns = rows.value.length ? Object.keys(rows.value[0]) : []
  if (!columns.length) { ElMessage.warning('请先查询出数据'); return }
  aic.loading = true
  try {
    const res = await aiChart(local.modelId, { question, columns })
    local.cfg = res.data.cfg
    emitChange()
    ElMessage.success('已生成图表配置')
  } catch (e) { ElMessage.error(e?.msg || e?.message || '生成失败') } finally { aic.loading = false }
}
</script>

<style scoped>
.ccp { display: flex; flex-direction: column; gap: 8px; height: 100%; }
.ccp-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.ccp-tip { font-size: 12px; color: #909399; }
.ccp-ai { padding: 8px 10px; border: 1px dashed #c0c4cc; border-radius: 6px; background: #fafafa; }
.ccp-ai-bar { margin-top: 6px; display: flex; gap: 6px; }
.ccp-ai-out { margin: 8px 0 0; padding: 8px 10px; max-height: 140px; overflow: auto; background: #1e1e1e; color: #d4d4d4; border-radius: 4px; font-family: Consolas, Monaco, monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all; }
.cursor { animation: blink 1s steps(1) infinite; color: #67c23a; }
@keyframes blink { 50% { opacity: 0; } }
.ccp-chart { flex: 1; min-height: 300px; border: 1px solid #ebeef5; border-radius: 6px; padding: 6px; }
</style>
