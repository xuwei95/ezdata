<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item :label="$t('策略名称')" prop="strategyName">
        <el-input v-model="queryParams.strategyName" :placeholder="$t('请输入策略名称')" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item :label="$t('状态')" prop="status">
        <el-select v-model="queryParams.status" :placeholder="$t('状态')" clearable style="width: 140px">
          <el-option :label="$t('启用')" :value="1" />
          <el-option :label="$t('停用')" :value="0" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">{{ $t('搜索') }}</el-button>
        <el-button icon="Refresh" @click="resetQuery">{{ $t('重置') }}</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['alert:strategy:add']">{{ $t('新增') }}</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['alert:strategy:remove']">{{ $t('删除') }}</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="strategyList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column :label="$t('策略名称')" align="center" prop="strategyName" :show-overflow-tooltip="true" />
      <el-table-column :label="$t('业务')" align="center" prop="biz" width="110" />
      <el-table-column :label="$t('告警等级')" align="center" width="100">
        <template #default="scope">
          <el-tag :type="levelTag(triggerLevel(scope.row))">{{ levelText(triggerLevel(scope.row)) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('转发渠道')" align="center">
        <template #default="scope">
          <el-tag v-for="(c, i) in forwardTypes(scope.row)" :key="i" size="small" style="margin: 2px">{{ channelLabel(c) }}</el-tag>
          <span v-if="!forwardTypes(scope.row).length">-</span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('状态')" align="center" width="90">
        <template #default="scope">
          <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">{{ scope.row.status === 1 ? '启用' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('操作')" align="center" width="150" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['alert:strategy:edit']">{{ $t('修改') }}</el-button>
          <el-button link type="primary" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['alert:strategy:remove']">{{ $t('删除') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />

    <el-dialog :title="title" v-model="open" width="720px" append-to-body>
      <el-form ref="strategyRef" :model="form" :rules="rules" label-width="150px">
        <el-form-item :label="$t('策略名称')" prop="strategyName">
          <el-input v-model="form.strategyName" :placeholder="$t('请输入策略名称')" />
        </el-form-item>
        <el-form-item :label="$t('告警等级')" prop="level">
          <el-radio-group v-model="form.level">
            <el-radio :value="0">{{ $t('信息') }}</el-radio>
            <el-radio :value="1">{{ $t('警告') }}</el-radio>
            <el-radio :value="2">{{ $t('错误') }}</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-divider content-position="left">{{ $t('转发渠道') }}</el-divider>
        <div v-for="(ch, idx) in channels" :key="idx" class="channel-card">
          <div class="channel-head">
            <el-select v-model="ch.type" size="small" style="width: 160px" :placeholder="$t('渠道类型')">
              <el-option v-for="c in channelTypes" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
            <el-button link type="danger" icon="Delete" @click="channels.splice(idx, 1)">{{ $t('移除') }}</el-button>
          </div>
          <!-- webhook -->
          <template v-if="ch.type === 'webhook'">
            <el-input v-model="ch.webhook_url" :placeholder="$t('Webhook 地址 URL')" size="small" class="mt6" />
            <el-row :gutter="8" class="mt6">
              <el-col :span="8">
                <el-select v-model="ch.webhook_method" size="small" :placeholder="$t('方法')">
                  <el-option label="POST" value="POST" />
                  <el-option label="PUT" value="PUT" />
                  <el-option label="GET" value="GET" />
                </el-select>
              </el-col>
              <el-col :span="16"><el-input v-model="ch.webhook_header" placeholder='可选请求头(JSON)' size="small" /></el-col>
            </el-row>
          </template>
          <!-- 转通知 -->
          <template v-if="ch.type === 'notice'">
            <div class="mt6">
              <notice-user-select v-model="ch.notice_users" />
            </div>
          </template>
          <!-- kafka -->
          <template v-if="ch.type === 'kafka'">
            <el-input v-model="ch.topic" placeholder="Kafka topic" size="small" class="mt6" />
            <el-input v-model="ch.bootstrap_servers" :placeholder="$t('bootstrap_servers(逗号分隔)，如 kafka1:9092,kafka2:9092')" size="small" class="mt6" />
          </template>
          <!-- 邮件 -->
          <template v-if="ch.type === 'email'">
            <el-row :gutter="8" class="mt6">
              <el-col :span="16"><el-input v-model="ch.host" placeholder="SMTP host" size="small" /></el-col>
              <el-col :span="8"><el-input v-model="ch.port" :placeholder="$t('端口(465)')" size="small" /></el-col>
            </el-row>
            <el-row :gutter="8" class="mt6">
              <el-col :span="12"><el-input v-model="ch.user" :placeholder="$t('账号')" size="small" /></el-col>
              <el-col :span="12"><el-input v-model="ch.password" :placeholder="$t('密码/授权码')" size="small" type="password" /></el-col>
            </el-row>
            <el-input v-model="ch.to" :placeholder="$t('收件人(逗号分隔)')" size="small" class="mt6" />
          </template>
        </div>
        <el-button size="small" icon="Plus" @click="channels.push({ type: 'webhook', webhook_method: 'POST' })">{{ $t('添加渠道') }}</el-button>

        <el-divider content-position="left">{{ $t('其他') }}</el-divider>
        <el-form-item :label="$t('状态')">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">{{ $t('启用') }}</el-radio>
            <el-radio :value="0">{{ $t('停用') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="$t('备注')">
          <el-input v-model="form.remark" type="textarea" :placeholder="$t('请输入备注')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="submitForm">{{ $t('确 定') }}</el-button>
        <el-button @click="cancel">{{ $t('取 消') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="AlertStrategy">
import { listStrategy, getStrategy, addStrategy, updateStrategy, delStrategy } from '@/api/alert/strategy'
import NoticeUserSelect from '@/views/alert/strategy/components/NoticeUserSelect.vue'

const { proxy } = getCurrentInstance()

const strategyList = ref([])
const open = ref(false)
const loading = ref(true)
const showSearch = ref(true)
const ids = ref([])
const multiple = ref(true)
const total = ref(0)
const title = ref('')
const channels = ref([])

const channelTypes = [
  { label: '通用Webhook', value: 'webhook' },
  { label: '转通知', value: 'notice' },
  { label: 'Kafka', value: 'kafka' },
  { label: '邮件', value: 'email' }
]

const data = reactive({
  form: {},
  queryParams: { pageNum: 1, pageSize: 10, strategyName: undefined, status: undefined },
  rules: { strategyName: [{ required: true, message: '策略名称不能为空', trigger: 'blur' }] }
})
const { queryParams, form, rules } = toRefs(data)

function safeParse(raw, def) {
  if (!raw) return def
  try {
    return JSON.parse(raw)
  } catch (e) {
    return def
  }
}
function triggerLevel(row) {
  return safeParse(row.triggerConf, {}).level ?? 0
}
function forwardTypes(row) {
  return (safeParse(row.forwardConf, []) || []).map(c => c.type)
}
function channelLabel(v) {
  return (channelTypes.find(c => c.value === v) || {}).label || v
}
function levelText(l) {
  return ['信息', '警告', '错误'][l] || '信息'
}
function levelTag(l) {
  return ['info', 'warning', 'danger'][l] || 'info'
}

function getList() {
  loading.value = true
  listStrategy(queryParams.value).then(response => {
    strategyList.value = response.rows
    total.value = response.total
    loading.value = false
  })
}

function cancel() {
  open.value = false
  reset()
}
function reset() {
  form.value = { strategyId: undefined, strategyName: undefined, biz: 'scheduler', level: 2, status: 1, remark: undefined }
  channels.value = []
  proxy.resetForm('strategyRef')
}
function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}
function resetQuery() {
  proxy.resetForm('queryRef')
  handleQuery()
}
function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.strategyId)
  multiple.value = !selection.length
}
function handleAdd() {
  reset()
  channels.value = [{ type: 'webhook', webhook_method: 'POST' }]
  open.value = true
  title.value = '新增告警策略'
}
function handleUpdate(row) {
  reset()
  getStrategy(row.strategyId).then(response => {
    const d = response.data
    form.value = { strategyId: d.strategyId, strategyName: d.strategyName, biz: d.biz || 'scheduler', level: safeParse(d.triggerConf, {}).level ?? 2, status: d.status, remark: d.remark }
    channels.value = safeParse(d.forwardConf, []) || []
    open.value = true
    title.value = '修改告警策略'
  })
}
function buildPayload() {
  return {
    strategyId: form.value.strategyId,
    strategyName: form.value.strategyName,
    biz: form.value.biz || 'scheduler',
    triggerConf: JSON.stringify({ level: form.value.level }),
    forwardConf: JSON.stringify(channels.value || []),
    status: form.value.status,
    remark: form.value.remark
  }
}
function submitForm() {
  proxy.$refs['strategyRef'].validate(valid => {
    if (!valid) return
    const payload = buildPayload()
    if (form.value.strategyId != undefined) {
      updateStrategy(payload).then(() => {
        proxy.$modal.msgSuccess('修改成功')
        open.value = false
        getList()
      })
    } else {
      addStrategy(payload).then(() => {
        proxy.$modal.msgSuccess('新增成功')
        open.value = false
        getList()
      })
    }
  })
}
function handleDelete(row) {
  const strategyIds = row.strategyId || ids.value.join(',')
  proxy.$modal.confirm('是否确认删除选中的告警策略？').then(function () {
    return delStrategy(strategyIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

getList()
</script>

<style scoped>
.channel-card {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
  background: #fafafa;
}
.channel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.mt6 {
  margin-top: 6px;
}
</style>
