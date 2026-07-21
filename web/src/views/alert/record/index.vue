<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item :label="$t('标题')" prop="title">
        <el-input v-model="queryParams.title" :placeholder="$t('请输入告警标题')" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item :label="$t('状态')" prop="status">
        <el-select v-model="queryParams.status" :placeholder="$t('处理状态')" clearable style="width: 140px">
          <el-option :label="$t('未处理')" :value="0" />
          <el-option :label="$t('已处理')" :value="1" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">{{ $t('搜索') }}</el-button>
        <el-button icon="Refresh" @click="resetQuery">{{ $t('重置') }}</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['alert:record:remove']">{{ $t('删除') }}</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="recordList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="ID" align="center" prop="alertId" width="70" />
      <el-table-column :label="$t('标题')" align="center" prop="title" :show-overflow-tooltip="true" />
      <el-table-column :label="$t('等级')" align="center" width="90">
        <template #default="scope">
          <el-tag :type="levelTag(scope.row.level)">{{ levelText(scope.row.level) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('业务')" align="center" prop="biz" width="110" />
      <el-table-column :label="$t('对象')" align="center" prop="source" :show-overflow-tooltip="true" />
      <el-table-column :label="$t('指标')" align="center" prop="metric" width="110" />
      <el-table-column :label="$t('状态')" align="center" width="90">
        <template #default="scope">
          <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">{{ scope.row.status === 1 ? '已处理' : '未处理' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('时间')" align="center" prop="createTime" width="160" />
      <el-table-column :label="$t('操作')" align="center" width="180" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button link type="primary" icon="View" @click="handleView(scope.row)">{{ $t('详情') }}</el-button>
          <el-button v-if="scope.row.status !== 1" link type="success" icon="Check" @click="handleProcess(scope.row)" v-hasPermi="['alert:record:edit']">{{ $t('处理') }}</el-button>
          <el-button link type="danger" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['alert:record:remove']">{{ $t('删除') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />

    <el-dialog :title="$t('告警详情')" v-model="viewOpen" width="640px" append-to-body>
      <el-descriptions :column="1" border>
        <el-descriptions-item :label="$t('标题')">{{ current.title }}</el-descriptions-item>
        <el-descriptions-item :label="$t('等级')">{{ levelText(current.level) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('业务')">{{ current.biz }}</el-descriptions-item>
        <el-descriptions-item :label="$t('对象')">{{ current.source }}</el-descriptions-item>
        <el-descriptions-item :label="$t('指标')">{{ current.metric }}</el-descriptions-item>
        <el-descriptions-item :label="$t('内容')">{{ current.content }}</el-descriptions-item>
        <el-descriptions-item :label="$t('标签')">{{ current.tags }}</el-descriptions-item>
        <el-descriptions-item :label="$t('时间')">{{ current.createTime }}</el-descriptions-item>
        <el-descriptions-item :label="$t('恢复时间')">{{ current.recoverTime || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup name="AlertRecord">
import { listRecord, changeRecordStatus, delRecord } from '@/api/alert/record'

const { proxy } = getCurrentInstance()

const recordList = ref([])
const loading = ref(true)
const showSearch = ref(true)
const ids = ref([])
const multiple = ref(true)
const total = ref(0)
const viewOpen = ref(false)
const current = ref({})

const data = reactive({
  queryParams: { pageNum: 1, pageSize: 10, title: undefined, status: undefined }
})
const { queryParams } = toRefs(data)

function levelText(l) {
  return ['信息', '警告', '错误'][l] || '信息'
}
function levelTag(l) {
  return ['info', 'warning', 'danger'][l] || 'info'
}

function getList() {
  loading.value = true
  listRecord(queryParams.value).then(response => {
    recordList.value = response.rows
    total.value = response.total
    loading.value = false
  })
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
  ids.value = selection.map(item => item.alertId)
  multiple.value = !selection.length
}
function handleView(row) {
  current.value = row
  viewOpen.value = true
}
function handleProcess(row) {
  proxy.$modal.confirm('确认将该告警标记为已处理吗?').then(function () {
    return changeRecordStatus(row.alertId, 1)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('操作成功')
  }).catch(() => {})
}
function handleDelete(row) {
  const alertIds = row.alertId || ids.value.join(',')
  proxy.$modal.confirm('是否确认删除选中的告警记录？').then(function () {
    return delRecord(alertIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

getList()
</script>
