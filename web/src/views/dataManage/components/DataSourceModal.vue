<template>
  <el-dialog :title="form.id ? '编辑数据源' : '新建数据源'" v-model="visible" width="640px" append-to-body>
    <el-form :model="form" label-width="120px">
      <el-form-item label="源类型" required>
        <el-select v-model="form.sourceType" filterable placeholder="选择数据源类型" :disabled="!!form.id"
          @change="onTypeChange" style="width: 100%">
          <el-option v-for="t in types" :key="t.sourceType" :label="`${t.title}(${t.sourceType})`" :value="t.sourceType" />
        </el-select>
      </el-form-item>
      <el-form-item label="名称" required>
        <el-input v-model="form.name" placeholder="显示名称" />
      </el-form-item>
      <el-form-item label="编码">
        <el-input v-model="form.code" :disabled="!!form.id"
          :placeholder="form.id ? '' : '稳定引用编码,留空自动生成(创建后不可改)'" />
        <span v-if="form.id" class="tip">编码是下游模型/接口的引用锚点,创建后不可修改</span>
      </el-form-item>

      <!-- 连接参数:由 connection_schema 动态渲染 -->
      <template v-for="(prop, key) in schemaProps" :key="key">
        <el-form-item :label="prop.title || key" :required="requiredKeys.includes(key)">
          <el-input v-if="prop.format === 'password'" v-model="values[key]" type="password" show-password
            :placeholder="form.id ? '留空则保持原值不变' : prop.description" />
          <el-input-number v-else-if="prop.type === 'integer'" v-model="values[key]" :controls="false"
            class="num-input" />
          <el-switch v-else-if="prop.type === 'boolean'" v-model="values[key]" />
          <el-input v-else v-model="values[key]" :placeholder="prop.description" />
        </el-form-item>
      </template>
      <el-form-item label="备注 / 业务上下文">
        <div style="width: 100%">
          <el-input v-model="form.remark" type="textarea" :autosize="{ minRows: 6, maxRows: 20 }"
            placeholder="该数据源的业务上下文(表关系 / 指标口径 / 常见问法→字段 / 取数注意)。会作为上下文喂给取数 AI;可点「AI 解析」按结构自动生成初稿再编辑。" />
          <div style="margin-top: 6px; display: flex; align-items: center; gap: 10px">
            <el-button size="small" :loading="analyzing" :disabled="!form.id" @click="onAnalyze">✨ AI 解析</el-button>
            <el-button v-if="analyzeText" size="small" type="primary" link @click="applyAnalyze">↥ 应用到描述</el-button>
            <span v-if="!form.id" class="tip">保存数据源后可用(需读取其结构)</span>
            <span v-else class="tip">AI 读取现有描述 + 表结构后生成</span>
          </div>
          <pre v-if="analyzeText" class="analyze-out">{{ analyzeText }}</pre>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="onTest" :loading="testing">测试连接</el-button>
      <el-button type="primary" @click="onSubmit">确定</el-button>
      <el-button @click="visible = false">取消</el-button>
    </template>
  </el-dialog>
</template>

<script setup name="DataSourceModal">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getSourceTypes, getSourceSchema, addSource, updateSource, testSource, getSource } from '@/api/dataManage/data'
import { getToken } from '@/utils/auth'

const emit = defineEmits(['ok'])
const visible = ref(false)
const testing = ref(false)
const analyzing = ref(false)
const analyzeText = ref('')
const types = ref([])
const schema = ref({})
const values = reactive({})
const form = reactive({ id: undefined, name: '', code: '', sourceType: '', remark: '' })

const schemaProps = computed(() => schema.value.properties || {})
const requiredKeys = computed(() => schema.value.required || [])
const secretKeys = computed(() =>
  Object.entries(schemaProps.value).filter(([, p]) => p.format === 'password').map(([k]) => k)
)

function reset() {
  form.id = undefined; form.name = ''; form.code = ''; form.sourceType = ''; form.remark = ''
  Object.keys(values).forEach((k) => delete values[k])
  schema.value = {}
  analyzeText.value = ''
}

// AI 解析:读该源现有描述+结构,流式生成业务上下文初稿(后端 text/event-stream 直出文本增量)
async function onAnalyze() {
  if (!form.id) return
  analyzing.value = true; analyzeText.value = ''
  try {
    const resp = await fetch(
      `${import.meta.env.VITE_APP_BASE_API}/data/source/${form.id}/analyze-context/stream`,
      { method: 'POST', headers: { Authorization: 'Bearer ' + getToken(), 'Content-Type': 'application/json' } }
    )
    if (!resp.ok || !resp.body) throw new Error('HTTP ' + resp.status)
    const reader = resp.body.getReader(); const dec = new TextDecoder()
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      analyzeText.value += dec.decode(value, { stream: true })
    }
  } catch (e) {
    ElMessage.error('AI 解析失败: ' + (e.message || e))
  } finally {
    analyzing.value = false
  }
}
function applyAnalyze() {
  form.remark = analyzeText.value
  ElMessage.success('已应用到备注,可继续编辑后保存')
}

async function loadSchema(type) {
  const res = await getSourceSchema(type)
  schema.value = res.data || {}
}

// 用 schema 里的 default(来自 connection_args_example)预填空字段
function applyDefaults() {
  for (const [k, p] of Object.entries(schemaProps.value)) {
    if (p.default !== undefined && (values[k] === undefined || values[k] === '')) {
      values[k] = p.default
    }
  }
}

async function onTypeChange(type) {
  Object.keys(values).forEach((k) => delete values[k])
  await loadSchema(type)
  applyDefaults()
}

function splitConfigSecrets() {
  const config = {}, secrets = {}
  for (const [k, v] of Object.entries(values)) {
    if (v === undefined || v === '') continue
    if (secretKeys.value.includes(k)) secrets[k] = v
    else config[k] = v
  }
  return { config, secrets }
}

async function open(row) {
  reset()
  const res = await getSourceTypes()
  types.value = res.data || []
  if (row && row.id) {
    const detail = (await getSource(row.id)).data
    form.id = detail.id; form.name = detail.name; form.code = detail.code
    form.sourceType = detail.sourceType; form.remark = detail.remark
    await loadSchema(detail.sourceType)
    Object.assign(values, detail.config || {})
    applyDefaults()
  }
  visible.value = true
}

async function onTest() {
  const { config, secrets } = splitConfigSecrets()
  testing.value = true
  try {
    const res = await testSource(form.id ? { id: form.id } : { sourceType: form.sourceType, config, secrets })
    res.data.success ? ElMessage.success('连接成功 ' + (res.data.latencyMs ? Math.round(res.data.latencyMs) + 'ms' : ''))
      : ElMessage.error('连接失败: ' + res.data.message)
  } finally {
    testing.value = false
  }
}

async function onSubmit() {
  if (!form.sourceType || !form.name) { ElMessage.warning('请填写源类型和名称'); return }
  const { config, secrets } = splitConfigSecrets()
  const payload = { ...form, config, secrets: Object.keys(secrets).length ? secrets : undefined }
  await (form.id ? updateSource(payload) : addSource(payload))
  ElMessage.success(form.id ? '修改成功' : '新增成功')
  visible.value = false
  emit('ok')
}

defineExpose({ open })
</script>

<style scoped>
/* 数字输入框:固定宽度,值左对齐(默认居中且占满,丑) */
.num-input {
  width: 220px;
}
.num-input :deep(.el-input__inner) {
  text-align: left;
}
.tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}
.analyze-out {
  margin: 8px 0 0;
  padding: 8px 10px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  max-height: 260px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
}
</style>
