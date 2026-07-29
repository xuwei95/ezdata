<template>
  <el-dialog
    v-model="visible"
    :title="ed.id ? '编辑代码看板' : '新建代码看板'"
    fullscreen
    append-to-body
    :close-on-click-modal="false"
    class="code-board-dialog"
  >
    <div class="editor">
      <div class="ed-head">
        <el-input v-model="ed.name" :placeholder="$t('看板名称')" style="width: 220px" />
        <el-select v-model="ed.datasourceCode" filterable :placeholder="$t('选择数据源')" style="width: 220px">
          <el-option v-for="d in sources" :key="d.code" :label="`${d.name}(${d.code})`" :value="d.code" />
        </el-select>
        <el-input v-model="ed.remark" :placeholder="$t('说明(可选)')" style="width: 220px" />
        <el-select v-model="ed.refreshInterval" size="small" style="width: 116px" :placeholder="$t('自动刷新')">
          <el-option :value="0" :label="$t('不自动刷新')" />
          <el-option :value="10" :label="$t('每 10 秒')" />
          <el-option :value="30" :label="$t('每 30 秒')" />
          <el-option :value="60" :label="$t('每 1 分钟')" />
          <el-option :value="300" :label="$t('每 5 分钟')" />
        </el-select>
        <el-button :type="aiq.open ? 'primary' : 'default'" icon="MagicStick" @click="aiq.open = !aiq.open">{{ $t('AI 辅助') }}</el-button>
        <el-button type="primary" icon="View" :loading="previewing" :disabled="!ed.datasourceCode || !ed.code.trim()" @click="preview">{{ $t('预览') }}</el-button>
        <el-button type="success" icon="Check" :disabled="!ed.name.trim() || !ed.datasourceCode || !ed.code.trim()" :loading="saving" @click="save">{{ $t('保存') }}</el-button>
        <span class="tip">{{ HINT }}</span>
      </div>

      <!-- AI 辅助:一句话 → 流式生成「取数 + pyecharts 绘图」代码,直接写进左侧代码框 -->
      <div v-if="aiq.open" class="ed-ai">
        <el-input v-model="aiq.question" type="textarea" :rows="2" class="ai-q"
          :placeholder="$t('描述要画的图,如:白酒板块各股涨跌幅柱状图 / 近30天成交额折线图')" @keyup.enter.stop="genCode" />
        <div class="ai-bar">
          <el-button size="small" type="primary" :loading="aiq.loading" :disabled="!ed.datasourceCode" @click="genCode">
            {{ ed.code.trim() ? '按需求改写代码' : '生成代码' }}</el-button>
          <span class="tip">{{ !ed.datasourceCode ? '请先选择数据源' : (ed.code.trim() ? '将在当前代码基础上按需求做最小改动(小调整会借鉴现有代码);生成后可再「预览」' : 'AI 会用所选数据源的 handler 取数并出图;生成后可再「预览」') }}</span>
        </div>
      </div>

      <div class="ed-body">
        <!-- 左:代码 -->
        <div class="ed-code">
          <div class="pane-label">{{ $t('取数 + 绘图代码') }}</div>
          <el-input v-model="ed.code" type="textarea" class="code-area"
            :autosize="{ minRows: 20 }" :placeholder="CODE_PH" spellcheck="false" />
        </div>
        <!-- 右:预览 -->
        <div class="ed-preview">
          <div class="pane-label">{{ $t('预览') }}</div>
          <div class="pv-box" v-loading="previewing" element-loading-text="沙箱执行中…">
            <iframe v-if="html" class="pv-frame" :srcdoc="fitChart(html)" sandbox="allow-scripts" frameborder="0" />
            <el-empty v-else :description="err || '点「预览」在沙箱跑代码出图'" :image-size="70" />
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup name="CodeBoardEditor">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { listSource, saveDashboard, getDashboard, runCodeChart } from '@/api/dataManage/data'
import { fitChart } from '../visualization/board.js'
import { getToken } from '@/utils/auth'

const props = defineProps({
  modelValue: { type: Boolean, default: false }, // 弹窗显隐
  id: { type: String, default: '' }, // 为空=新建
})
const emit = defineEmits(['update:modelValue', 'saved'])
const visible = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })

// 提示文案含双花括号不会被 Vue 插值(在字符串常量里),但仍放脚本常量统一管理
const HINT = '选数据源 → 写代码(用 handler 取数、pyecharts 画图)→ 预览 → 保存;渲染时在沙箱跑这段代码出图'
const CODE_PH = `# handler 已注入(该数据源的只读连接)。handler.query(...) 返回 list[dict]:
#   SQL 源:   handler.query("SELECT city, amt FROM t LIMIT 10")
#   ES 源:    handler.query({"size": 10, "query": {"match_all": {}}}, None, 10)
#   akshare:  handler.query("stock_zh_a_hist", {"symbol": "600519"})
# 把最终图表 HTML 赋给 result:
from pyecharts.charts import Bar
from pyecharts import options as opts

rows = handler.query("SELECT ...")            # 按你的数据源改写
x = [str(r.get("name", i)) for i, r in enumerate(rows)]
y = [r.get("value", 0) for r in rows]
c = Bar().add_xaxis(x).add_yaxis("值", y).set_global_opts(title_opts=opts.TitleOpts(title="示例"))
result = {"type": "html", "value": c.render_embed()}`

const AI_BASE = import.meta.env.VITE_APP_BASE_API || ''
const sources = ref([])
const saving = ref(false)
const previewing = ref(false)
const html = ref('')
const err = ref('')

const ed = reactive({ id: '', name: '', datasourceCode: '', code: '', remark: '', refreshInterval: 0 })
const aiq = reactive({ open: false, question: '', loading: false })

function stripFence(t) {
  let s = (t || '').trim()
  if (s.startsWith('```')) s = s.replace(/^```[^\n]*\n/, '').replace(/```\s*$/, '').trim()
  return s
}

// 流式生成绘图代码:边收边写进代码框,结束去掉可能的 ``` 围栏
async function genCode() {
  if (!ed.datasourceCode) { ElMessage.warning('请先选择数据源'); return }
  if (!aiq.question.trim()) { ElMessage.warning('请描述要画的图'); return }
  aiq.loading = true
  const before = ed.code
  ed.code = ''
  try {
    const resp = await fetch(AI_BASE + '/data/dashboard/ai-code/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + getToken() },
      body: JSON.stringify({ datasourceCode: ed.datasourceCode, question: aiq.question, code: before }),
    })
    if (!resp.ok || !resp.body) throw new Error('HTTP ' + resp.status)
    const reader = resp.body.getReader(); const dec = new TextDecoder()
    for (;;) { const { done, value } = await reader.read(); if (done) break; ed.code += dec.decode(value, { stream: true }) }
    ed.code = stripFence(ed.code)
    if (!ed.code) { ed.code = before; ElMessage.warning('未生成代码') }
    else ElMessage.success('已生成,点「预览」看效果')
  } catch (e) {
    ed.code = before
    ElMessage.error('生成失败: ' + (e?.message || e))
  } finally { aiq.loading = false }
}

async function loadSources() {
  try {
    const res = await listSource({ pageNum: 1, pageSize: 1000 })
    sources.value = res.rows || res.data || []
  } catch (e) { /* 忽略 */ }
}

async function openEditor() {
  Object.assign(ed, { id: '', name: '', datasourceCode: '', code: '', remark: '', refreshInterval: 0 })
  html.value = ''; err.value = ''
  if (props.id) {
    try {
      const d = (await getDashboard(props.id)).data || {}
      const comp = (d.components || [])[0] || {}
      const inl = comp.inline || {}
      Object.assign(ed, {
        id: d.id || props.id, name: d.name || '',
        datasourceCode: inl.datasourceCode || '', code: inl.code || '',
        remark: d.remark || '', refreshInterval: d.refreshInterval || 0,
      })
    } catch (e) { ElMessage.error('加载看板失败') }
  }
}

async function preview() {
  if (!ed.datasourceCode || !ed.code.trim()) return
  previewing.value = true; err.value = ''; html.value = ''
  try {
    const res = await runCodeChart({ datasourceCode: ed.datasourceCode, code: ed.code })
    html.value = (res.data && res.data.html) || ''
    if (!html.value) err.value = '未产出图表'
  } catch (e) { err.value = e?.msg || e?.message || '执行失败' } finally { previewing.value = false }
}

async function save() {
  if (!ed.name.trim()) { ElMessage.warning('请填写看板名称'); return }
  if (!ed.datasourceCode) { ElMessage.warning('请选择数据源'); return }
  if (!ed.code.trim()) { ElMessage.warning('请输入代码'); return }
  saving.value = true
  try {
    const { data } = await saveDashboard({
      id: ed.id || undefined,
      name: ed.name.trim(),
      dashType: 'code',
      remark: ed.remark,
      refreshInterval: ed.refreshInterval || 0,
      canvas: { mode: 'single' },
      components: [{ id: 'c1', type: 'code', inline: { datasourceCode: ed.datasourceCode, code: ed.code } }],
      filters: [],
    })
    if (data && data.id) ed.id = data.id
    ElMessage.success('已保存')
    emit('saved', ed.id)
    visible.value = false
  } catch (e) { ElMessage.error('保存失败: ' + (e?.msg || e?.message || e)) } finally { saving.value = false }
}

watch(() => props.modelValue, (v) => { if (v) { if (!sources.value.length) loadSources(); openEditor() } })
loadSources()
</script>

<style scoped>
.editor { display: flex; flex-direction: column; height: calc(100vh - 120px); }
.ed-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.ed-head .tip { font-size: 12px; color: #909399; }
.ed-ai { margin-bottom: 8px; padding: 8px 10px; border: 1px dashed #c0c4cc; border-radius: 6px; background: #fafafa; }
.ed-ai .ai-bar { margin-top: 6px; display: flex; align-items: center; gap: 10px; }
.ed-ai .tip { font-size: 12px; color: #909399; }
.ed-body { flex: 1; display: flex; gap: 12px; min-height: 0; }
.ed-code, .ed-preview { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.pane-label { font-size: 12px; color: #606266; margin-bottom: 4px; }
.code-area { flex: 1; }
.code-area :deep(textarea) { font-family: Consolas, Monaco, 'Courier New', monospace; font-size: 13px; line-height: 1.5; height: 100% !important; }
.pv-box { flex: 1; border: 1px solid #ebeef5; border-radius: 6px; overflow: hidden; display: flex; align-items: center; justify-content: center; background: #fff; }
.pv-frame { width: 100%; height: 100%; border: 0; }
</style>
