<template>
  <div class="metric-tab">
    <div class="mt-toolbar">
      <span class="hint"> {{ $t('指标 = 绑定在本模型上的口径化度量(如「行业加权市盈率」)。AI 分析时可直接 query_metric 取权威一致的数, 避免每次重写聚合。改动本模型会把相关指标标记为「待复核」。') }} </span>
      <el-button type="primary" size="small" icon="Plus" @click="openAdd">{{ $t('新建指标') }}</el-button>
    </div>

    <vxe-table :data="list" v-loading="loading" border height="360" size="small">
      <vxe-column field="code" :title="$t('代码')" width="150" />
      <vxe-column field="name" :title="$t('名称')" min-width="130" />
      <vxe-column :title="$t('度量')" width="150">
        <template #default="{ row }">{{ measureText(row) }}</template>
      </vxe-column>
      <vxe-column :title="$t('维度')" min-width="120">
        <template #default="{ row }">{{ dimsText(row) }}</template>
      </vxe-column>
      <vxe-column field="unit" :title="$t('单位')" width="70" />
      <vxe-column :title="$t('状态')" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.reviewState === 'stale'" type="warning" size="small">{{ $t('待复核') }}</el-tag>
          <el-tag v-else-if="row.status === '0'" type="success" size="small">{{ $t('启用') }}</el-tag>
          <el-tag v-else type="info" size="small">{{ $t('停用') }}</el-tag>
        </template>
      </vxe-column>
      <vxe-column :title="$t('操作')" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="preview(row)">{{ $t('试跑') }}</el-button>
          <el-button link type="primary" size="small" @click="openEdit(row)">{{ $t('编辑') }}</el-button>
          <el-button link type="danger" size="small" @click="remove(row)">{{ $t('删除') }}</el-button>
        </template>
      </vxe-column>
      <template #empty><el-empty :description="$t('本模型暂无指标,点「新建指标」创建')" :image-size="70" /></template>
    </vxe-table>

    <!-- 新建 / 编辑 -->
    <el-dialog :title="form.metricId ? $t('编辑指标') : $t('新建指标')" v-model="dlg" width="640px" append-to-body>
      <el-form :model="form" label-width="142px">
        <el-form-item :label="$t('名称')" required>
          <el-input v-model="form.name" :placeholder="$t('如:行业加权市盈率')" />
        </el-form-item>
        <el-form-item :label="$t('代码')" required>
          <el-input v-model="form.code" :disabled="!!form.metricId" :placeholder="$t('英文唯一,如 industry_pe_avg')" />
        </el-form-item>
        <el-form-item :label="$t('度量')" required>
          <el-select v-model="form.agg" style="width: 130px" :placeholder="$t('聚合')">
            <el-option v-for="a in AGGS" :key="a.v" :label="a.t" :value="a.v" />
          </el-select>
          <el-select v-model="form.field" filterable allow-create style="width: 200px; margin-left: 8px"
            :placeholder="$t('度量字段')" :disabled="form.agg === 'count'">
            <el-option v-for="f in fieldOpts" :key="f" :label="f" :value="f" />
          </el-select>
          <span class="tip">{{ $t('count 无需字段') }}</span>
        </el-form-item>
        <el-form-item :label="$t('维度')">
          <el-select v-model="form.dims" multiple filterable allow-create style="width: 100%"
            :placeholder="$t('分组维度字段(可多选,如 industry_name)')">
            <el-option v-for="f in fieldOpts" :key="f" :label="f" :value="f" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('时间字段')">
          <el-select v-model="form.timeField" clearable filterable allow-create style="width: 260px"
            :placeholder="$t('用于时间范围过滤(如 date)')">
            <el-option v-for="f in fieldOpts" :key="f" :label="f" :value="f" />
          </el-select>
          <span class="tip">{{ $t('口径的时间列,可留空') }}</span>
        </el-form-item>
        <el-form-item :label="$t('单位')"><el-input v-model="form.unit" style="width: 200px" :placeholder="$t('如 倍 / 元 / 亿')" /></el-form-item>
        <el-form-item :label="$t('口径说明')">
          <el-input v-model="form.caliber" type="textarea" :rows="2"
            :placeholder="$t('该指标的业务口径/计算说明,AI 与用户共用同一定义')" />
        </el-form-item>
        <el-form-item :label="$t('状态')">
          <el-switch v-model="form.status" active-value="0" inactive-value="1" :active-text="$t('启用')" :inactive-text="$t('停用')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" :loading="saving" @click="save">{{ $t('保存') }}</el-button>
        <el-button @click="dlg = false">{{ $t('取消') }}</el-button>
      </template>
    </el-dialog>

    <!-- 试跑结果 -->
    <el-dialog :title="$t('指标试跑')" v-model="pvDlg" width="640px" append-to-body>
      <div v-if="pvData">
        <div class="pv-meta">
          <b>{{ pvData.code }}</b> · {{ $t('单位') }} {{ pvData.unit || '—' }}
          <div v-if="pvData.caliber" class="pv-caliber">{{ $t('口径说明') }}:{{ pvData.caliber }}</div>
        </div>
        <vxe-table :data="pvData.rows || []" border height="320" size="small">
          <vxe-column type="seq" width="50" />
          <vxe-column v-for="col in pvCols" :key="col" :field="col" :title="col" />
        </vxe-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { t as $t } from '@/lang'
import { listMetric, addMetric, updateMetric, delMetric, previewMetric } from '@/api/dataManage/data'

const props = defineProps({ model: { type: Object, required: true } })

const AGGS = computed(() => [
  { v: 'sum', t: $t('求和 sum') }, { v: 'avg', t: $t('平均 avg') }, { v: 'max', t: $t('最大 max') },
  { v: 'min', t: $t('最小 min') }, { v: 'count', t: $t('计数 count') }, { v: 'count_distinct', t: $t('去重计数') },
])

const list = ref([])
const loading = ref(false)
const fieldOpts = computed(() => (props.model?.fields || []).map((f) => f.name).filter(Boolean))

function safeParse(s, d) { try { return typeof s === 'string' ? JSON.parse(s) : s || d } catch { return d } }
function measureText(row) {
  const m = safeParse(row.measure, {})
  return m.agg === 'count' ? 'count' : `${m.agg || ''}(${m.field || ''})`
}
function dimsText(row) {
  const ds = safeParse(row.dimensions, [])
  return (ds || []).map((d) => d.field).filter(Boolean).join(', ') || '—'
}

async function load() {
  if (!props.model?.id) return
  loading.value = true
  try {
    // 后端列表无 modelId 过滤,取回后按本模型过滤
    const res = await listMetric({ pageNum: 1, pageSize: 500 })
    list.value = (res.rows || []).filter((r) => r.modelId === props.model.id)
  } finally {
    loading.value = false
  }
}

// ---- 增改 ----
const dlg = ref(false)
const saving = ref(false)
const form = ref({})
function blank() {
  return { metricId: null, name: '', code: '', agg: 'sum', field: '', dims: [], timeField: '', unit: '', caliber: '', status: '0' }
}
function openAdd() { form.value = blank(); dlg.value = true }
function openEdit(row) {
  const m = safeParse(row.measure, {})
  const ds = safeParse(row.dimensions, [])
  form.value = {
    metricId: row.metricId, name: row.name, code: row.code,
    agg: m.agg || 'sum', field: m.field || '',
    dims: (ds || []).map((d) => d.field).filter(Boolean),
    timeField: row.timeField || '', unit: row.unit || '', caliber: row.caliber || '', status: row.status || '0',
  }
  dlg.value = true
}
async function save() {
  if (!form.value.name || !form.value.code) { ElMessage.warning($t('名称、代码必填')); return }
  if (form.value.agg !== 'count' && !form.value.field) { ElMessage.warning($t('该聚合需选度量字段')); return }
  const payload = {
    name: form.value.name, code: form.value.code, modelId: props.model.id,
    measure: JSON.stringify(form.value.agg === 'count' ? { agg: 'count' } : { agg: form.value.agg, field: form.value.field }),
    dimensions: JSON.stringify((form.value.dims || []).map((f) => ({ field: f, name: f }))),
    timeField: form.value.timeField || null, unit: form.value.unit || '', caliber: form.value.caliber || '',
    status: form.value.status,
  }
  saving.value = true
  try {
    if (form.value.metricId) { payload.metricId = form.value.metricId; await updateMetric(payload); ElMessage.success($t('已保存')) }
    else { await addMetric(payload); ElMessage.success($t('已创建')) }
    dlg.value = false
    load()
  } finally { saving.value = false }
}
async function remove(row) {
  await ElMessageBox.confirm($t('删除指标「{name}」?', { name: row.name }), $t('提示'), { type: 'warning' })
  await delMetric(row.metricId)
  ElMessage.success($t('删除成功'))
  load()
}

// ---- 试跑 ----
const pvDlg = ref(false)
const pvData = ref(null)
const pvCols = computed(() => {
  const rows = pvData.value?.rows || []
  // 过滤 vxe-table 注入的内部行键(_X_ROW_KEY 等下划线开头字段)
  return rows.length ? Object.keys(rows[0]).filter((k) => !k.startsWith('_')) : []
})
async function preview(row) {
  const loadingInst = ElMessage({ message: $t('试跑中…'), type: 'info', duration: 0 })
  try {
    const res = await previewMetric(row.code)
    pvData.value = res.data
    pvDlg.value = true
  } finally { loadingInst.close() }
}

watch(() => props.model?.id, load, { immediate: true })
</script>

<style scoped lang="scss">
.metric-tab { display: flex; flex-direction: column; }
.mt-toolbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.mt-toolbar .hint { font-size: 12px; color: #909399; line-height: 1.5; }
.tip { font-size: 12px; color: #c0c4cc; margin-left: 8px; }
.pv-meta { margin-bottom: 8px; font-size: 13px; }
.pv-caliber { color: #909399; font-size: 12px; margin-top: 4px; }
</style>
