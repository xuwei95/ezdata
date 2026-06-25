<template>
  <div class="builtin-task-form etl-form">
    <el-row :gutter="16">
      <!-- 左:抽取 + 转换 -->
      <el-col :span="13">
        <el-divider content-position="left">抽取(源)</el-divider>
        <el-form label-width="84px">
          <el-form-item label="源数据源" required>
            <el-select v-model="model.extract.datasource_code" filterable placeholder="选择源数据源" style="width: 100%"
              @change="onSrcChange">
              <el-option v-for="s in sources" :key="s.code" :label="`${s.name} (${s.sourceType})`" :value="s.code" />
            </el-select>
          </el-form-item>
          <!-- 流式源:单选要消费的表/主题 -->
          <el-form-item label="表/主题" required v-if="srcIsStream">
            <el-select v-model="model.extract.object" filterable clearable placeholder="要消费的表/主题"
              style="width: 100%" :loading="objLoading">
              <el-option v-for="t in objects" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <!-- 批量源:多选相关表 -->
          <el-form-item label="相关表" v-else>
            <el-select v-model="model.extract.tables" multiple filterable clearable collapse-tags
              placeholder="选 1 张=预填查询并作目标表;多张=喂 AI 连表;不选=全库结构给 AI"
              style="width: 100%" :loading="objLoading" @change="onTablesChange">
              <el-option v-for="t in objects" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>

          <!-- 批量源:原生查询 -->
          <el-form-item label="原生查询" required v-if="!srcIsStream">
            <div style="width: 100%">
              <div class="bar">
                <span class="muted">{{ srcFamily === 'api' ? '接口调用:函数名 + 参数(JSON)' : '原生 SQL / DSL' }}</span>
                <el-button size="small" icon="MagicStick" @click="aiq.open = !aiq.open">AI 生成查询</el-button>
              </div>
              <el-input v-model="model.extract.native" type="textarea" :rows="6"
                :placeholder="srcFamily === 'api' ? '如:{&quot;func&quot;:&quot;stock_zh_a_daily&quot;,&quot;params&quot;:{&quot;symbol&quot;:&quot;sh600519&quot;}}' : '例如:SELECT * FROM orders WHERE status=\'PAID\''" />
              <!-- AI 生成面板:生成后流式打印,确认再采用 -->
              <div v-if="aiq.open" class="ai-panel">
                <el-input v-model="aiq.question" type="textarea" :rows="2"
                  placeholder="用自然语言描述要抽取的数据,如:金额>1000 的已支付订单,按金额降序" />
                <div class="bar" style="margin-top: 6px">
                  <el-button size="small" type="primary" icon="MagicStick" :loading="aiq.loading" @click="genQuery">
                    {{ aiq.output ? '重新生成' : '生成' }}</el-button>
                  <span class="muted">生成结果见下方,确认后再采用</span>
                </div>
                <pre v-if="aiq.output" class="ai-out">{{ aiq.output }}<span v-if="aiq.loading" class="cursor">▋</span></pre>
                <div v-if="aiq.output" class="bar">
                  <el-button size="small" type="success" icon="Check" :disabled="aiq.loading"
                    @click="applyQuery">采用到查询</el-button>
                  <el-button size="small" @click="aiq.output = ''">清空</el-button>
                </div>
              </div>
            </div>
          </el-form-item>

          <!-- 流式源:逐条消费,有界/持续 -->
          <el-form-item label="最大条数" v-else>
            <el-input-number v-model="model.extract.max_events" :min="0" :step="100" controls-position="right"
              style="width: 160px" />
            <span class="muted" style="margin-left: 10px">0 = 持续消费(任务常驻),&gt;0 = 读这一批后结束</span>
          </el-form-item>

          <el-divider content-position="left">转换(可选)</el-divider>
          <el-form-item label="启用转换">
            <el-switch v-model="model.transform.enabled" />
          </el-form-item>
          <el-form-item label="转换代码" v-if="model.transform.enabled">
            <div style="width: 100%">
              <div class="bar">
                <span class="muted">def transform(row)</span>
                <el-button size="small" icon="MagicStick" @click="ait.open = !ait.open">AI 生成转换</el-button>
              </div>
              <code-editor v-model="model.transform.code" language="python" height="180px"
                placeholder="定义 transform(row) 逐行转换并返回 row" />
              <!-- AI 生成面板 -->
              <div v-if="ait.open" class="ai-panel">
                <el-input v-model="ait.question" type="textarea" :rows="2"
                  placeholder="用自然语言描述转换逻辑,如:把 amount 乘 1.13 存为 amount_with_tax" />
                <div class="bar" style="margin-top: 6px">
                  <el-button size="small" type="primary" icon="MagicStick" :loading="ait.loading" @click="genTransform">
                    {{ ait.output ? '重新生成' : '生成' }}</el-button>
                  <span class="muted">可用字段取自最近一次预览</span>
                </div>
                <pre v-if="ait.output" class="ai-out">{{ ait.output }}<span v-if="ait.loading" class="cursor">▋</span></pre>
                <div v-if="ait.output" class="bar">
                  <el-button size="small" type="success" icon="Check" :disabled="ait.loading"
                    @click="applyTransform">采用到转换</el-button>
                  <el-button size="small" @click="ait.output = ''">清空</el-button>
                </div>
              </div>
            </div>
          </el-form-item>

          <el-divider content-position="left">装载(目标)</el-divider>
          <el-form-item label="目标源" required>
            <el-select v-model="model.load.datasource_code" filterable placeholder="选择目标数据源" style="width: 100%">
              <el-option v-for="s in sources" :key="s.code" :label="`${s.name} (${s.sourceType})`" :value="s.code" />
            </el-select>
          </el-form-item>
          <el-form-item :label="destIsFile ? '对象 Key' : '目标表'" required>
            <el-input v-model="model.load.table"
              :placeholder="destIsFile ? '对象 key,如 exports/orders.csv' : '目标表名(默认同主表)'"
              clearable style="width: 100%" />
          </el-form-item>
          <el-form-item label="文件格式" v-if="destIsFile">
            <el-radio-group v-model="model.load.format">
              <el-radio value="csv">CSV</el-radio>
              <el-radio value="json">JSON</el-radio>
              <el-radio value="jsonl">JSONL</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="写入模式" v-else>
            <el-radio-group v-model="model.load.mode">
              <el-radio value="append">追加</el-radio>
              <el-radio value="replace">覆盖</el-radio>
              <el-radio value="merge">合并</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </el-col>

      <!-- 右:预览 / 测试写入 -->
      <el-col :span="11">
        <el-divider content-position="left">抽取预览(调试)</el-divider>
        <div class="bar">
          <div>
            <el-button type="primary" icon="View" :loading="previewLoading" @click="doPreview">预览抽取数据</el-button>
            <el-button icon="Upload" :loading="loadLoading" :disabled="!previewRowsRaw.length"
              @click="doTestLoad">测试写入目标</el-button>
          </div>
          <div>
            <el-radio-group v-model="previewTab" size="small" v-if="hasTransformed" style="margin-right: 8px">
              <el-radio-button value="raw">原始</el-radio-button>
              <el-radio-button value="transformed">转换后</el-radio-button>
            </el-radio-group>
            <el-button size="small" icon="Document" :disabled="!previewRows.length"
              @click="jsonDlg = true">原始JSON</el-button>
          </div>
        </div>
        <div class="muted" style="margin: 6px 0">
          {{ srcIsStream ? '流式源抽 1 条事件预览' : `取前 ${previewLimit} 条样本` }};嵌套对象以 JSON 显示,可点「原始JSON」查看完整结构。
        </div>
        <vxe-table :data="previewRows" border height="460" size="mini" :column-config="{ resizable: true }"
          :loading="previewLoading">
          <vxe-column type="seq" width="50" fixed="left" />
          <vxe-column v-for="c in previewCols" :key="c" :field="c" :title="c" :width="150" show-overflow>
            <template #default="{ row }">{{ fmtCell(row[c]) }}</template>
          </vxe-column>
          <template #empty>点击「预览抽取数据」查看样本</template>
        </vxe-table>
      </el-col>
    </el-row>

    <!-- 原始数据 JSON 查看 -->
    <el-dialog v-model="jsonDlg" title="原始数据(JSON)" width="60%" append-to-body>
      <code-editor :model-value="previewJson" language="json" height="60vh" read-only />
    </el-dialog>
  </div>
</template>

<script setup name="DataIntegrationTask">
import CodeEditor from '@/components/CodeEditor'
import { listSource, listTables, previewEtl, testLoadEtl } from '@/api/dataManage/data'
import { getToken } from '@/utils/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  taskParams: { type: Object, default: () => ({}) },
  templateInfo: { type: Object, default: () => ({}) }
})

const DEFAULT_TRANSFORM = `def transform(row):
    # row 为一条记录(dict),返回修改后的 dict
    return row`

const sources = ref([])
const objects = ref([])
const objLoading = ref(false)
const previewLoading = ref(false)
const loadLoading = ref(false)
const previewLimit = 50
const previewRowsRaw = ref([])
const previewRowsTransformed = ref([])
const previewCols = ref([])
const previewTab = ref('raw')
const jsonDlg = ref(false)

// 单元格:嵌套对象/数组转成 JSON 字符串显示,避免 [object Object]
function fmtCell(v) {
  if (v === null || v === undefined) return ''
  return typeof v === 'object' ? JSON.stringify(v) : v
}

// native 是 Any:SQL 源为字符串,ES/Mongo 等 DSL 源为 dict/数组。
// 文本框只能编辑字符串 → 入框时 dict 转 JSON 文本(否则显示 [object Object]),
// 提交/预览时再把 JSON 文本解析回 dict,SQL 文本解析失败则原样保留为字符串。
function nativeToText(v) {
  if (v === null || v === undefined) return ''
  return typeof v === 'object' ? JSON.stringify(v, null, 2) : String(v)
}
function nativeFromText(t) {
  const s = (t || '').trim()
  if (s.startsWith('{') || s.startsWith('[')) {
    try { return JSON.parse(s) } catch { /* 非合法 JSON,按原始文本提交 */ }
  }
  return t
}
const previewJson = computed(() => JSON.stringify(previewRows.value, null, 2))

const STREAM_FAMILIES = ['cdc', 'stream']

const model = reactive({
  extract: { datasource_code: '', object: '', tables: [], native: '', max_events: 100 },
  transform: { enabled: false, code: DEFAULT_TRANSFORM },
  load: { datasource_code: '', table: '', mode: 'append', dataset: 'public', format: 'csv' }
})

const srcIsStream = computed(() => {
  const s = sources.value.find((x) => x.code === model.extract.datasource_code)
  return !!s && STREAM_FAMILIES.includes(s.family)
})
// 当前源的 family(用于按源类型给原生查询不同的默认模板)
const srcFamily = computed(() => sources.value.find((x) => x.code === model.extract.datasource_code)?.family || '')
const destIsFile = computed(() => {
  const s = sources.value.find((x) => x.code === model.load.datasource_code)
  return !!s && s.family === 'file'
})
// 目标表兜底:流式=消费对象;批量=只选 1 张时用它,多张/不选需手填
const defaultTable = computed(() =>
  srcIsStream.value ? model.extract.object : (model.extract.tables.length === 1 ? model.extract.tables[0] : ''))
const hasTransformed = computed(() => previewRowsTransformed.value.length > 0)
const previewRows = computed(() =>
  previewTab.value === 'transformed' && hasTransformed.value ? previewRowsTransformed.value : previewRowsRaw.value
)

async function loadSources() {
  const res = await listSource({ pageNum: 1, pageSize: 200 })
  sources.value = res.rows || []
}

async function loadObjects(code) {
  objects.value = []
  const src = sources.value.find((s) => s.code === code)
  if (!src) return
  objLoading.value = true
  try {
    objects.value = (await listTables(src.id)).data || []
  } finally {
    objLoading.value = false
  }
}

// 用户切换源:清空已选 + 重新加载对象列表(初始化还原时不要清空,见 initParams)
function onSrcChange(code) {
  model.extract.object = ''
  model.extract.tables = []
  loadObjects(code)
}

// 批量源多选:只选 1 张时预填默认查询和目标表;多张/不选则不预填(交给 AI 连表/全库)
// 按源类型给不同默认:api(akshare/ccxt)是"函数名+参数",填 JSON 模板;SQL 源填 SELECT。
function onTablesChange(tbls) {
  if ((tbls || []).length !== 1) return
  const t = tbls[0]
  if (!model.extract.native.trim()) {
    model.extract.native = srcFamily.value === 'api'
      ? `{\n  "func": "${t}",\n  "params": {}\n}`
      : `SELECT * FROM ${t} LIMIT 100`
  }
  if (!model.load.table) model.load.table = t
}

function initParams() {
  const p = props.taskParams || {}
  if (p.extract) {
    Object.assign(model.extract, p.extract)
    // DSL 源 native 为 dict,文本框需字符串 → 转 JSON 文本,避免显示 [object Object]
    model.extract.native = nativeToText(p.extract.native)
    // 还原多选(老数据可能只存了单个 object)
    model.extract.tables = Array.isArray(p.extract.tables) ? p.extract.tables
      : (p.extract.object ? [p.extract.object] : [])
  }
  if (p.transform) {
    model.transform.enabled = !!p.transform.enabled
    // 存的 code 为空(转换未启用时)→ 回填默认模板,避免开启后编辑器空白
    model.transform.code = (p.transform.code || '').trim() ? p.transform.code : DEFAULT_TRANSFORM
  }
  if (p.load) Object.assign(model.load, p.load)
  if (model.extract.datasource_code) loadObjects(model.extract.datasource_code)  // 仅加载列表,保留已选
}

// 运行时开启转换且代码空白 → 给默认模板
watch(() => model.transform.enabled, (on) => {
  if (on && !(model.transform.code || '').trim()) model.transform.code = DEFAULT_TRANSFORM
})

onMounted(async () => {
  await loadSources()
  initParams()
})
watch(() => props.taskParams, initParams, { deep: true })

// ---- AI 流式生成(生成→下方流式打印→确认采用)----
const aiq = reactive({ open: false, question: '', output: '', loading: false })
const ait = reactive({ open: false, question: '', output: '', loading: false })
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
  const reader = resp.body.getReader()
  const dec = new TextDecoder()
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    onChunk(dec.decode(value, { stream: true }))
  }
}

async function genQuery() {
  if (!model.extract.datasource_code) { ElMessage.warning('请先选择源数据源'); return }
  if (!aiq.question.trim()) { ElMessage.warning('请描述要抽取的数据'); return }
  aiq.output = ''; aiq.loading = true
  try {
    await streamAi('/data/etl/ai-query/stream',
      { datasourceCode: model.extract.datasource_code, objectNames: model.extract.tables, question: aiq.question },
      (c) => { aiq.output += c })
  } catch (e) {
    ElMessage.error('生成失败: ' + e.message)
  } finally {
    aiq.loading = false
  }
}
function applyQuery() {
  model.extract.native = stripFence(aiq.output).replace(/;\s*$/, '')
  aiq.open = false
  ElMessage.success('已采用到原生查询')
}

async function genTransform() {
  if (!ait.question.trim()) { ElMessage.warning('请描述转换逻辑'); return }
  ait.output = ''; ait.loading = true
  try {
    await streamAi('/data/etl/ai-transform/stream',
      { question: ait.question, columns: previewCols.value },
      (c) => { ait.output += c })
  } catch (e) {
    ElMessage.error('生成失败: ' + e.message)
  } finally {
    ait.loading = false
  }
}
function applyTransform() {
  model.transform.code = stripFence(ait.output) || DEFAULT_TRANSFORM
  ait.open = false
  ElMessage.success('已采用到转换代码')
}

async function doPreview() {
  if (!model.extract.datasource_code) { ElMessage.warning('请选择源数据源'); return }
  if (!srcIsStream.value && !(model.extract.native || '').trim()) {
    ElMessage.warning('请填写原生查询')
    return
  }
  if (srcIsStream.value && !model.extract.object) { ElMessage.warning('请选择要消费的表/主题'); return }
  previewLoading.value = true
  try {
    const res = await previewEtl({
      datasourceCode: model.extract.datasource_code,
      native: srcIsStream.value ? null : nativeFromText(model.extract.native),
      objectName: model.extract.object || null,
      transformCode: model.transform.enabled ? model.transform.code : null,
      limit: previewLimit
    })
    const d = res.data || {}
    previewRowsRaw.value = d.records || []
    previewRowsTransformed.value = d.transformed || []
    previewCols.value = d.columns || []
    previewTab.value = hasTransformed.value ? 'transformed' : 'raw'
    ElMessage.success(`预览 ${previewRowsRaw.value.length} 条`)
  } finally {
    previewLoading.value = false
  }
}

async function doTestLoad() {
  if (!model.load.datasource_code) { ElMessage.warning('请选择目标数据源'); return }
  const table = (model.load.table || '').trim() || defaultTable.value
  if (!table) { ElMessage.warning('请填写目标表'); return }
  // 优先写转换后的样本(若有)
  const records = previewTab.value === 'transformed' && hasTransformed.value
    ? previewRowsTransformed.value : previewRowsRaw.value
  await ElMessageBox.confirm(`将把 ${records.length} 条样本以「${model.load.mode}」写入 ${table},确认?`, '测试写入',
    { type: 'warning' })
  loadLoading.value = true
  try {
    const res = await testLoadEtl({
      datasourceCode: model.load.datasource_code, table, mode: model.load.mode,
      dataset: model.load.dataset, format: model.load.format, records
    })
    ElMessage.success(`已写入 ${res.data.written} 条到 ${res.data.table}`)
  } finally {
    loadLoading.value = false
  }
}

// 由父级提交时调用:校验并返回任务参数
function genTaskParams() {
  if (!model.extract.datasource_code) return { error: '请选择源数据源' }
  if (srcIsStream.value) {
    if (!model.extract.object) return { error: '流式源请选择要消费的表/主题' }
  } else if (!(model.extract.native || '').trim()) {
    return { error: '请填写原生查询' }
  }
  if (!model.load.datasource_code) return { error: '请选择目标数据源' }
  const table = (model.load.table || '').trim() || defaultTable.value
  if (!table) return { error: '请填写目标表' }
  const oneTable = !srcIsStream.value && model.extract.tables.length === 1 ? model.extract.tables[0] : null
  return {
    params: {
      extract: {
        datasource_code: model.extract.datasource_code,
        // 流式:单个消费对象;批量:选 1 张才作目标表兜底,多张/不选为 null
        object: srcIsStream.value ? (model.extract.object || null) : oneTable,
        tables: srcIsStream.value ? undefined : model.extract.tables,
        native: srcIsStream.value ? '' : nativeFromText(model.extract.native),
        max_events: srcIsStream.value ? (model.extract.max_events || 0) : undefined
      },
      transform: { enabled: !!model.transform.enabled, code: model.transform.enabled ? model.transform.code : '' },
      load: {
        datasource_code: model.load.datasource_code,
        table,
        mode: model.load.mode || 'append',
        dataset: model.load.dataset || 'public',
        format: model.load.format || 'csv'
      }
    }
  }
}

defineExpose({ genTaskParams })
</script>

<style scoped>
.etl-form .bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.etl-form .muted { color: #909399; font-size: 12px; }
.etl-form .ai-panel { margin-top: 8px; padding: 10px; border: 1px dashed #c0c4cc; border-radius: 6px; background: #fafafa; }
.etl-form .ai-out {
  margin: 8px 0; padding: 8px 10px; max-height: 220px; overflow: auto;
  background: #1e1e1e; color: #d4d4d4; border-radius: 4px;
  font-family: Consolas, Monaco, monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all;
}
.etl-form .cursor { animation: blink 1s steps(1) infinite; color: #67c23a; }
@keyframes blink { 50% { opacity: 0; } }
</style>
